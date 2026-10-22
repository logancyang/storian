"""Project workspace layout. Every artifact is a plain file so any agent can read and edit it."""

import json
from pathlib import Path

VIDEO_EXTS = {".mp4", ".mov", ".mxf", ".mts", ".m4v", ".avi", ".mkv"}


class Project:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()

    # files
    @property
    def config_path(self): return self.root / "project.json"
    @property
    def clips_path(self): return self.root / "clips.json"
    @property
    def story_path(self): return self.root / "story.json"
    @property
    def sequence_path(self): return self.root / "sequence.json"
    @property
    def coverage_path(self): return self.root / "coverage.json"
    @property
    def music_path(self): return self.root / "music.json"
    @property
    def mood_path(self): return self.root / "mood.json"
    @property
    def lut_path(self): return self.root / "slog3_to_709.cube"

    # dirs
    @property
    def frames_dir(self): return self.root / "frames"
    @property
    def sheets_dir(self): return self.root / "sheets"
    @property
    def labels_dir(self): return self.root / "labels"
    @property
    def previews_dir(self): return self.root / "previews"
    @property
    def music_dir(self): return self.root / "music"
    @property
    def refs_dir(self): return self.root / "refs"

    def exists(self):
        return self.config_path.exists()

    @property
    def config(self):
        return read_json(self.config_path)

    @property
    def footage_dir(self):
        return Path(self.config["footage_dir"])

    def clips(self):
        return read_json(self.clips_path) if self.clips_path.exists() else []

    def clip_map(self):
        return {c["id"]: c for c in self.clips()}

    def label(self, clip_id):
        p = self.labels_dir / f"{clip_id}.json"
        return read_json(p) if p.exists() else None

    def labels(self):
        if not self.labels_dir.exists():
            return {}
        return {p.stem: read_json(p) for p in sorted(self.labels_dir.glob("*.json"))}

    def list_footage(self):
        return sorted(
            p for p in self.footage_dir.rglob("*")
            if p.suffix.lower() in VIDEO_EXTS and not p.name.startswith("._")
        )


def read_json(path):
    with open(path) as f:
        return json.load(f)


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(path)
