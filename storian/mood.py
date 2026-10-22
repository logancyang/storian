"""The mood: what the film should feel like, settled with the human before anything is designed.

mood.json (see knowledge/mood.md) holds the mood and theme, how they translate into music and
shots, and shot recipes for kinds of places. The Plan tab turns a recipe into a list to shoot
on arrival somewhere new.
"""

from .project import Project, read_json

HEIGHTS = {"low", "eye", "high", "overhead"}
SUBJECTS = {"none", "unrecognizable", "talent"}


def load(p: Project) -> dict | None:
    return read_json(p.mood_path) if p.mood_path.exists() else None


def check(data: dict) -> list[str]:
    errors = [f"mood.{k} is required" for k in ("mood", "theme") if not data.get(k)]
    for pl in data.get("places", []):
        for i, s in enumerate(pl.get("shots", []), 1):
            at = f"mood place {pl.get('id')} shot {i}"
            if not s.get("name"):
                errors.append(f"{at}: name is required")
            if s.get("height") not in HEIGHTS | {None}:
                errors.append(f"{at}: height must be one of {sorted(HEIGHTS)}")
            if s.get("subject") not in SUBJECTS | {None}:
                errors.append(f"{at}: subject must be one of {sorted(SUBJECTS)}")
    return errors
