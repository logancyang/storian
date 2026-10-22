"""Localhost storyboard. Serves the single-page UI plus the project's JSON and media.

The page polls /api/version, so edits the agent makes to story.json / sequence.json / labels
show up in the browser within a couple of seconds without a reload.
"""

import json
import mimetypes
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from .check import check_sequence
from .coverage import analyze as analyze_coverage
from . import mood, music
from .project import Project, read_json

WEB = Path(__file__).parent / "web"
MEDIA_DIRS = ("frames", "sheets", "previews", "music")


def project_payload(p: Project) -> dict:
    frames = {}
    for idx in p.frames_dir.glob("*/index.json"):
        d = read_json(idx)
        frames[d["clip"]] = {"t": [f["t"] for f in d["frames"]], "motion": d.get("motion")}
    previews = sorted(f.name for f in p.previews_dir.glob("*.mp4")) if p.previews_dir.exists() else []
    clips = {c["id"]: {k: c.get(k) for k in ("duration", "fps", "lens", "camera", "gamma", "recorded_at", "width", "height", "path")}
             for c in p.clips()}
    return {
        "config": p.config,
        "clips": clips,
        "labels": p.labels(),
        "frames": frames,
        "story": read_json(p.story_path) if p.story_path.exists() else None,
        "sequence": read_json(p.sequence_path) if p.sequence_path.exists() else None,
        "check": check_sequence(p) if p.sequence_path.exists() else None,
        "previews": previews,
        "coverage": analyze_coverage(p) if p.labels_dir.exists() else None,
        "music": music_payload(p),
        "mood": mood_payload(p),
    }


def music_payload(p: Project):
    if not p.music_path.exists():
        return None
    data = music.load(p)
    return {**data, "cue_seconds": music.cue_lengths(p, data), "errors": music.check(p, data)}


def mood_payload(p: Project):
    data = mood.load(p)
    return {**data, "errors": mood.check(data)} if data else None


def version(p: Project) -> float:
    paths = [p.config_path, p.mood_path, p.story_path, p.sequence_path, p.coverage_path, p.music_path, p.clips_path, p.labels_dir, p.previews_dir, p.frames_dir]
    paths += list(p.labels_dir.glob("*.json")) if p.labels_dir.exists() else []
    return max((x.stat().st_mtime for x in paths if x.exists()), default=0)


def make_handler(p: Project):
    class Handler(SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def send_json(self, data):
            body = json.dumps(data, ensure_ascii=False).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def send_file(self, path: Path):
            if not path.is_file():
                return self.send_error(404)
            size = path.stat().st_size
            start, end = 0, size - 1
            rng = self.headers.get("Range")
            if rng and rng.startswith("bytes="):
                a, _, b = rng[6:].partition("-")
                start = int(a) if a else max(0, size - int(b))
                end = int(b) if a and b else end
                self.send_response(206)
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            else:
                self.send_response(200)
            self.send_header("Content-Type", mimetypes.guess_type(path.name)[0] or "application/octet-stream")
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(end - start + 1))
            self.send_header("Cache-Control", "max-age=60")
            self.end_headers()
            with open(path, "rb") as f:
                f.seek(start)
                remaining = end - start + 1
                while remaining > 0:
                    chunk = f.read(min(1 << 20, remaining))
                    if not chunk:
                        break
                    try:
                        self.wfile.write(chunk)
                    except (BrokenPipeError, ConnectionResetError):
                        return
                    remaining -= len(chunk)

        def do_GET(self):
            path = unquote(urlparse(self.path).path)
            if path in ("/", "/index.html"):
                return self.send_file(WEB / "index.html")
            if path == "/api/project":
                return self.send_json(project_payload(p))
            if path == "/api/version":
                return self.send_json({"v": version(p)})
            parts = path.strip("/").split("/")
            if len(parts) >= 2 and parts[0] == "media" and parts[1] in MEDIA_DIRS:
                base = (p.root / parts[1]).resolve()
                target = (base / "/".join(parts[2:])).resolve()
                if base in target.parents:
                    return self.send_file(target)
            if len(parts) == 1 and (WEB / parts[0]).is_file():
                return self.send_file(WEB / parts[0])
            self.send_error(404)

    return Handler


def serve(p: Project, port: int = 7878, open_browser: bool = False):
    srv = ThreadingHTTPServer(("127.0.0.1", port), make_handler(p))
    url = f"http://localhost:{port}"
    print(f"storian storyboard: {url}  (project {p.root})", flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
