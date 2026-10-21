"""Music: reference tracks the human likes, candidate tracks found for each act, and the picks.

Everything lives in music.json (see knowledge/music.md). This module does the parts an agent
can't do by reading: measuring a reference track (tempo, loudness, energy over time, a
waveform) and a built-in search of free Creative Commons music (ccMixter by default, or
Jamendo through Openverse). Paid catalogs (Epidemic Sound, Artlist) are searched by the agent through
their MCP servers and written into the same file.
"""

import json
import shutil
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np

from .project import Project, read_json, write_json

SR = 11025
OPENVERSE = "https://api.openverse.org/v1/audio/"
CCMIXTER = "https://ccmixter.org/api/query"
UA = {"User-Agent": "storian (https://github.com/logancyang/storian)"}
# licences that allow syncing into a monetised video. CC 4.0 treats music synced to moving
# images as adapted material, so ND is out, and SA would put the whole film under BY-SA.
COMMERCIAL_OK = {"by", "cc0", "pdm"}


def load(p: Project) -> dict:
    data = read_json(p.music_path) if p.music_path.exists() else {}
    for k in ("references", "cues", "tracks"):
        data.setdefault(k, [])
    data.setdefault("direction", "")
    return data


def decode(path: Path, seconds: float = 240) -> np.ndarray:
    """Mono float samples at SR Hz, at most `seconds` long."""
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-t", str(seconds), "-ac", "1",
                          "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32)


def estimate_bpm(y: np.ndarray) -> float | None:
    """Tempo from the autocorrelation of an onset-strength envelope (good to ±2 BPM on clear beats)."""
    hop, win = 256, 1024
    if len(y) < SR * 8:
        return None
    frames = np.lib.stride_tricks.sliding_window_view(y, win)[::hop]
    spec = np.abs(np.fft.rfft(frames * np.hanning(win), axis=1))
    flux = np.maximum(0, np.diff(np.log1p(spec), axis=0)).sum(axis=1)
    flux -= flux.mean()
    ac = np.correlate(flux, flux, "full")[len(flux) - 1:]
    fps = SR / hop
    lags = np.arange(len(ac)) / fps
    ok = (lags >= 60 / 180) & (lags <= 60 / 60)
    if not ok.any() or ac[ok].max() <= 0:
        return None
    # weight towards 120 BPM, as people tap, to settle octave errors
    idx = np.flatnonzero(ok)
    score = ac[idx] * np.exp(-0.5 * (np.log2(60 / lags[idx] / 110) / 0.9) ** 2)
    i = idx[np.argmax(score)]
    a, b, c = ac[i - 1], ac[i], ac[i + 1]  # parabolic peak: sub-frame lag precision
    shift = 0.5 * (a - c) / (a - 2 * b + c) if (a - 2 * b + c) else 0
    return round(float(60 * fps / (i + shift)), 1)


def analyze(path) -> dict:
    """Tempo, loudness, brightness and a per-second energy curve for one audio file."""
    y = decode(path)
    if not len(y):
        return {}
    sec = y[: len(y) // SR * SR].reshape(-1, SR)
    rms = np.sqrt((sec ** 2).mean(axis=1) + 1e-12)
    db = 20 * np.log10(rms)
    spec = np.abs(np.fft.rfft(sec * np.hanning(SR), axis=1))
    freqs = np.fft.rfftfreq(SR, 1 / SR)
    centroid = float((spec * freqs).sum() / (spec.sum() + 1e-9))
    energy = np.clip((db - db.max() + 30) / 30, 0, 1)
    peaks = np.abs(y[: len(y) // 400 * 400]).reshape(400, -1).max(axis=1) if len(y) >= 400 else np.abs(y)
    return {
        "bpm": estimate_bpm(y),
        "loudness_db": round(float(20 * np.log10(np.sqrt((y ** 2).mean()) + 1e-12)), 1),
        "brightness_hz": round(centroid),
        "dynamic_range_db": round(float(np.percentile(db, 95) - np.percentile(db, 10)), 1),
        "energy": [round(float(e), 2) for e in energy],
        "peaks": [round(float(v), 3) for v in peaks / (peaks.max() + 1e-9)],
    }


def add_reference(p: Project, src: str, title: str = "", notes: str = "") -> dict:
    data = load(p)
    ref = {"id": f"ref{len(data['references']) + 1}", "title": title, "notes": notes, "source": "user"}
    if src.startswith(("http://", "https://")):
        ref.update(url=src, title=title or src)
    else:
        f = Path(src).expanduser()
        if not f.is_file():
            raise FileNotFoundError(src)
        dest = p.music_dir / "refs" / f.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        if f.resolve() != dest.resolve():
            shutil.copy2(f, dest)
        ref.update(file=f"refs/{f.name}", title=title or f.stem, duration=_duration(dest), analysis=analyze(dest))
    data["references"].append(ref)
    write_json(p.music_path, data)
    return ref


def _duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True).stdout.strip()
    return round(float(out), 1) if out else 0.0


def _get_json(url: str, timeout: float):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return json.load(r)


def _seconds(ps: str) -> int:
    parts = [int(x) for x in (ps or "0").split(":") if x.isdigit()]
    return sum(v * 60 ** i for i, v in enumerate(reversed(parts)))


def search_ccmixter(query: str, limit: int = 10, commercial: bool = True, vocals: bool = False,
                    timeout: float = 20) -> list[dict]:
    """Creative Commons music from ccMixter, matched on tags (all must match; relaxed from the end
    until something matches). No key needed. Licence BY by default, which allows monetised use with credit."""
    tags = [t for t in query.lower().replace(",", " ").split() if t]
    if not vocals:
        tags = ["instrumental"] + [t for t in tags if t != "instrumental"]
    results = []
    while tags and not results:
        params = {"f": "json", "tags": ",".join(tags), "sort": "rank", "limit": limit}
        if commercial:
            params["lic"] = "by"
        results = _get_json(f"{CCMIXTER}?{urllib.parse.urlencode(params)}", timeout)
        tags = tags[:-1] if not results else tags
    out = []
    for x in results:
        f = (x.get("files") or [{}])[0]
        extra = x.get("upload_extra") or {}
        if not vocals and "vocals" in extra.get("usertags", ""):  # "instrumental" tags aren't always honest
            continue
        lic = x.get("license_name", "")
        out.append({
            "id": f"ccmixter:{x['upload_id']}",
            "title": x.get("upload_name"), "artist": x.get("user_real_name") or x.get("user_name"),
            "source": "ccmixter", "url": x.get("file_page_url"), "preview": f.get("download_url"),
            "hotlink_blocked": True,  # ccmixter only serves files to its own pages: `music fetch` to play
            "duration": _seconds((f.get("file_format_info") or {}).get("ps")), "bpm": extra.get("bpm") or None,
            "license": f"CC {lic}", "license_url": x.get("license_url"),
            "youtube_ok": not any(w in lic.lower() for w in ("noncommercial", "noderiv", "no deriv", "sharealike", "share alike")),
            "attribution": f"\"{x.get('upload_name')}\" by {x.get('user_name')} (ccmixter.org), {lic}, {x.get('license_url')}",
            "tags": [t for t in extra.get("usertags", "").split(",") if t][:10],
            "found_by": query,
        })
    return out


def search(query: str, provider: str = "ccmixter", **kw) -> list[dict]:
    if provider == "openverse":
        kw.pop("vocals", None)
        return search_openverse(query, **kw)
    return search_ccmixter(query, **kw)


def search_openverse(query: str, limit: int = 10, commercial: bool = True, timeout: float = 20) -> list[dict]:
    """Creative Commons music from Jamendo via Openverse. No key needed, but heavily rate-limited."""
    params = {"q": query, "source": "jamendo", "page_size": min(limit, 20)}
    if commercial:
        params["license_type"] = "commercial"
    results = _get_json(f"{OPENVERSE}?{urllib.parse.urlencode(params)}", timeout).get("results", [])
    return [{
        "id": f"jamendo:{x['id'][:8]}",
        "title": x.get("title"), "artist": x.get("creator"), "source": "jamendo",
        "url": x.get("foreign_landing_url"), "preview": x.get("url"),
        "duration": round((x.get("duration") or 0) / 1000), "bpm": None,
        "license": f"CC {x.get('license', '').upper()} {x.get('license_version') or ''}".strip(),
        "youtube_ok": x.get("license") in COMMERCIAL_OK,
        "attribution": x.get("attribution"),
        "tags": [t["name"] for t in x.get("tags") or []][:8] + (x.get("genres") or []),
        "found_by": query,
    } for x in results]


def save_tracks(p: Project, tracks: list[dict]) -> int:
    data = load(p)
    known = {t["id"] for t in data["tracks"]}
    new = [t for t in tracks if t["id"] not in known]
    data["tracks"] += new
    write_json(p.music_path, data)
    return len(new)


def cue_lengths(p: Project, data: dict) -> dict:
    """Seconds of picture each cue has to cover, from the acts it scores."""
    if not p.sequence_path.exists():
        return {}
    from .media import parse_tc
    acts = read_json(p.sequence_path).get("acts", [])
    dur = [sum(parse_tc(s["out"]) - parse_tc(s["in"]) for s in a.get("shots", [])) for a in acts]
    return {c["id"]: round(sum(dur[i] for i in c.get("acts", []) if i < len(dur)), 1) for c in data["cues"]}


def shortlisted(data: dict) -> set:
    return {x.get("track") for c in data["cues"] for x in c.get("candidates", [])} | \
           {c["chosen"] for c in data["cues"] if c.get("chosen")}


def fetch_tracks(p: Project, data: dict, everything: bool = False) -> list[str]:
    """Cache tracks as small local previews (AAC 96 kb/s) so the storyboard plays them offline and
    no page hotlinks a catalog. Only the shortlisted candidates unless `everything`. The request
    carries the track's own page as Referer, as a download from that page would."""
    want = None if everything else shortlisted(data)
    done = []
    for t in data["tracks"]:
        if (want is not None and t["id"] not in want) or t.get("file") or not t.get("preview"):
            continue
        out = p.music_dir / "previews" / (t["id"].replace(":", "_") + ".m4a")
        out.parent.mkdir(parents=True, exist_ok=True)
        headers = f"Referer: {t['url']}\r\n" if t.get("url") else ""
        cmd = ["ffmpeg", "-v", "error", "-y", "-user_agent", UA["User-Agent"]] + (["-headers", headers] if headers else []) + \
              ["-i", t["preview"], "-vn", "-ac", "2", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(out)]
        if subprocess.run(cmd, capture_output=True).returncode == 0:
            t["file"] = f"previews/{out.name}"
            t["analysis"] = analyze(out)
            t["bpm"] = t.get("bpm") or t["analysis"].get("bpm")
            done.append(t["id"])
        else:
            out.unlink(missing_ok=True)
    return done


def analyze_tracks(p: Project, data: dict, force: bool = False) -> int:
    """Measure tracks: from the local cached file, else streamed from the preview URL."""
    n = 0
    for t in data["tracks"]:
        src = str(p.music_dir / t["file"]) if t.get("file") else t.get("preview")
        if not src or (t.get("analysis") and not force):
            continue
        try:
            t["analysis"] = analyze(src)
        except subprocess.CalledProcessError:
            continue
        t["bpm"] = t.get("bpm") or t["analysis"].get("bpm")
        n += 1
    return n


def check(p: Project, data: dict) -> list[str]:
    errors = []
    tracks = {t["id"] for t in data["tracks"]}
    n_acts = len(read_json(p.sequence_path).get("acts", [])) if p.sequence_path.exists() else None
    for c in data["cues"]:
        for t in [x.get("track") for x in c.get("candidates", [])] + ([c["chosen"]] if c.get("chosen") else []):
            if t not in tracks:
                errors.append(f"cue {c['id']}: unknown track {t}")
        if n_acts is not None and any(not 0 <= i < n_acts for i in c.get("acts", [])):
            errors.append(f"cue {c['id']}: act index out of range (0-{n_acts - 1})")
    for r in data["references"]:
        if r.get("file") and not (p.music_dir / r["file"]).exists():
            errors.append(f"{r['id']}: missing file music/{r['file']}")
    return errors
