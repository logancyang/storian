"""`storian publish`: a private, phone-friendly copy of the storyboard on Cloudflare.

Builds a static snapshot (the page, the project data as JSON, and only the media the page
shows), then deploys it as a Cloudflare Worker that asks for a key once per device.
The laptop stays the only place where the agent works. Publish after each session, or let
`storian publish --install` do it in the background whenever the project changes.
"""

import fcntl
import hashlib
import json
import os
import plistlib
import re
import secrets
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from .media import parse_tc
from .project import Project, read_json
from .server import WEB, project_payload, version

HOSTED = Path(__file__).parent / "hosted"
CONFIG = Path.home() / ".config" / "storian" / "hosted.json"
AGENTS = Path.home() / "Library" / "LaunchAgents"
WRANGLER = ["npx", "--yes", "wrangler@4"]
MAX_FILES = 20000  # Workers static assets, per deploy


def worker_name(p: Project) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", p.config["name"].lower()).strip("-")
    return f"storian-{slug}"[:63].rstrip("-")


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def load_config() -> dict:
    return read_json(CONFIG) if CONFIG.exists() else {}


def save_config(cfg: dict):
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps(cfg, indent=2))
    os.chmod(CONFIG, 0o600)


def frame_name(ts: list, t: float) -> str:
    """The keyframe the page shows for time t: the same choice as frameUrl() in index.html."""
    best = ts[0]
    for x in ts:
        if x <= t + 0.5:
            best = x
        else:
            break
    return f"t{best:09.3f}.jpg"


def media_files(p: Project, payload: dict) -> list[str]:
    """Paths under the project root that the page can request, and nothing else."""
    out = set()
    frames = payload["frames"]

    def frame(clip, t):
        f = frames.get(clip)
        if f and f["t"]:
            out.add(f"frames/{clip}/{frame_name(f['t'], t)}")

    for act in (payload["sequence"] or {}).get("acts", []):
        for s in act["shots"]:
            t0, t1 = parse_tc(s["in"]), parse_tc(s["out"])
            for t in (t0 + 0.3, t0, (t0 + t1) / 2, t1 - 0.2):
                frame(s["clip"], t)
    for c, info in payload["clips"].items():  # the Library shows each clip's middle frame
        frame(c, (info.get("duration") or 0) / 2)
    for sc in (payload["coverage"] or {}).get("scenes", []):
        for th in sc.get("thumbs", []):
            frame(th["clip"], th["t"])
    out.update(f"sheets/{c}.jpg" for c in payload["clips"])
    out.update(f"previews/{n}" for n in payload["previews"])
    m = payload["music"] or {}
    out.update(f"music/{t['file']}" for t in m.get("tracks", []) + m.get("references", []) if t.get("file"))
    return sorted(x for x in out if (p.root / x).is_file())


def _place(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(src, dst)  # no copy: the snapshot shares the project's files
    except OSError:
        shutil.copy2(src, dst)


def build(p: Project, site: Path) -> dict:
    stamp = datetime.now().astimezone().isoformat(timespec="seconds")
    payload = project_payload(p)
    payload["hosted"] = {"published": stamp}
    pub = site / "public"
    if pub.exists():
        shutil.rmtree(pub)
    (pub / "api").mkdir(parents=True)
    (pub / "api" / "project.json").write_text(json.dumps(payload, ensure_ascii=False))
    (pub / "api" / "version.json").write_text(json.dumps({"v": stamp}))
    for f in ("index.html", "icon-180.png", "icon-512.png"):
        shutil.copy2(WEB / f, pub / f)
    (pub / "sw.js").write_text((WEB / "sw.js").read_text().replace('const BUILD = "dev"', f'const BUILD = "{stamp}"'))
    manifest = read_json(WEB / "manifest.webmanifest")
    manifest["name"] = f"{p.config['name']} · Storian"
    (pub / "manifest.webmanifest").write_text(json.dumps(manifest, indent=2))
    media = media_files(p, payload)
    for rel in media:
        _place(p.root / rel, pub / "media" / rel)
    n = sum(1 for x in pub.rglob("*") if x.is_file())
    size = sum(x.stat().st_size for x in pub.rglob("*") if x.is_file())
    return {"published": stamp, "files": n, "mb": round(size / 1e6, 1), "media": len(media)}


def write_config(p: Project, site: Path, key: str):
    cfg = {
        "name": worker_name(p),
        "main": str(HOSTED / "worker.js"),
        "compatibility_date": "2025-09-01",
        "workers_dev": True,
        "preview_urls": False,
        "assets": {"directory": "public", "binding": "ASSETS", "run_worker_first": True},
        "vars": {"KEY_HASH": _sha(key), "COOKIE_CHECK": _sha(_sha("cookie:" + key)), "PROJECT": p.config["name"]},
    }
    (site / "wrangler.json").write_text(json.dumps(cfg, indent=2))


def _node_major(node) -> int:
    try:
        return int(subprocess.run([str(node), "--version"], capture_output=True, text=True).stdout.lstrip("v").split(".")[0])
    except (OSError, ValueError):
        return 0


def node_env() -> dict:
    """Wrangler 4 needs Node 22+. Fall back to the newest nvm-installed Node when the default is older."""
    env = dict(os.environ)
    if _node_major(shutil.which("node") or "node") >= 22:
        return env
    best = max(Path.home().glob(".nvm/versions/node/v*/bin/node"), key=_node_major, default=None)
    if not best or _node_major(best) < 22:
        raise SystemExit("storian publish needs Node.js 22 or newer (Cloudflare's wrangler requires it)")
    env["PATH"] = f"{best.parent}{os.pathsep}{env['PATH']}"
    return env


def deploy(site: Path) -> str | None:
    """Run wrangler, echo its output, and return the workers.dev URL it prints."""
    proc = subprocess.Popen(WRANGLER + ["deploy", "--config", "wrangler.json"], cwd=site, env=node_env(),
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    url = None
    for line in proc.stdout:
        print(line, end="", flush=True)
        url = url or (re.search(r"https://[\w.-]+\.workers\.dev", line) or [None])[0]
    if proc.wait():
        raise SystemExit("wrangler deploy failed (run `npx wrangler login` if you're not signed in to Cloudflare)")
    return url


def publish(p: Project, new_key: bool = False, dry_run: bool = False) -> dict:
    cfg = load_config()
    name = worker_name(p)
    w = cfg.setdefault("workers", {}).setdefault(name, {})
    if new_key or not w.get("key"):
        w["key"] = secrets.token_urlsafe(12)
        save_config(cfg)
    site = p.root / ".publish"
    site.mkdir(exist_ok=True)
    with open(site / "lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)  # the background watcher and a manual publish share .publish/
        v = version(p)  # read before building, so changes made during the deploy go out next time
        info = build(p, site)
        if info["files"] > MAX_FILES:
            raise SystemExit(f"{info['files']} files is over Cloudflare's {MAX_FILES} per deploy")
        write_config(p, site, w["key"])
        info.update(worker=name, site=str(site))
        if dry_run:
            return info
        url = deploy(site) or w.get("url")
    cfg = load_config()  # reread: another project's publish may have saved meanwhile
    cfg.setdefault("workers", {})[name] = {**w, "url": url, "version": v}
    save_config(cfg)
    return {**info, "url": url, "key": w["key"], "login": f"{url}/login#k={w['key']}" if url else None}


def due(p: Project, settle: float) -> bool:
    """The project changed since the last publish and has been quiet for `settle` seconds."""
    v = version(p)
    return v > load_config().get("workers", {}).get(worker_name(p), {}).get("version", 0) and time.time() - v >= settle


def watch(p: Project, every: float = 30, settle: float = 90):
    """Publish whenever the project changes. Waits for the agent to pause so a half-written
    edit doesn't go out, and keeps retrying through network drops."""
    print(f"{datetime.now():%F %T} watching {p.root}", flush=True)
    while True:
        if due(p, settle):
            try:
                r = publish(p)
                print(f"{datetime.now():%F %T} published {r['files']} files ({r['mb']} MB)", flush=True)
            except (Exception, SystemExit) as e:
                print(f"{datetime.now():%F %T} publish failed ({e}), retrying in 5 minutes", flush=True)
                time.sleep(300)
        time.sleep(every)


def agent_plist(p: Project) -> Path:
    return AGENTS / f"com.storian.publish.{worker_name(p).removeprefix('storian-')}.plist"


def install(p: Project) -> dict:
    """Run `publish --watch` as a launchd agent: starts at login, restarts if it dies, and
    runs outside any agent sandbox, so Codex or Claude never need network access to publish."""
    plist, log = agent_plist(p), p.root / ".publish" / "watch.log"
    log.parent.mkdir(exist_ok=True)
    AGENTS.mkdir(parents=True, exist_ok=True)
    plist.write_bytes(plistlib.dumps({
        "Label": plist.stem,
        "ProgramArguments": [str(Path(sys.executable).parent / "storian"), "-p", str(p.root.resolve()), "publish", "--watch"],
        "EnvironmentVariables": {"PATH": node_env()["PATH"]},  # launchd's PATH has no node or npx
        "RunAtLoad": True,
        "KeepAlive": True,
        "ProcessType": "Standard",  # unset means launchd throttles CPU and disk, which slowed a deploy from 1 to 4 minutes
        "StandardOutPath": str(log),
        "StandardErrorPath": str(log),
    }))
    uninstall(p, keep_file=True)
    subprocess.run(["launchctl", "bootstrap", f"gui/{os.getuid()}", str(plist)], check=True)
    return {"agent": plist.stem, "log": str(log)}


def uninstall(p: Project, keep_file: bool = False) -> bool:
    plist = agent_plist(p)
    target = f"gui/{os.getuid()}/{plist.stem}"
    subprocess.run(["launchctl", "bootout", target], capture_output=True)
    for _ in range(100):  # bootout returns before the job is gone, and bootstrap fails until it is
        if subprocess.run(["launchctl", "print", target], capture_output=True).returncode:
            break
        time.sleep(0.1)
    if plist.exists() and not keep_file:
        plist.unlink()
        return True
    return False
