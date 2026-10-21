"""Validate sequence.json and lint it against the editing rules in knowledge/director.md."""

from .media import parse_tc
from .project import Project, read_json

# cuts motivated by motion or shape can join two shots of the same size and focal length
MOTIVATED_CUTS = ("match", "graphic", "cut-on-motion", "whip", "smash")


def check_sequence(p: Project) -> dict:
    errors, warnings = [], []
    if not p.sequence_path.exists():
        return {"errors": ["sequence.json missing"], "warnings": [], "stats": {}}
    seq = read_json(p.sequence_path)
    clips = p.clip_map()
    labels = p.labels()
    target = float(seq.get("target_minutes") or p.config.get("target_minutes", 15)) * 60

    for key in ("title", "theme", "mood", "central_idea", "acts"):
        if not seq.get(key):
            errors.append(f"sequence.{key} is required")

    shots, seen_ids = [], set()
    for a in seq.get("acts", []):
        for s in a.get("shots", []):
            sid = s.get("id")
            if sid in seen_ids:
                errors.append(f"duplicate shot id {sid}")
            seen_ids.add(sid)
            c = clips.get(s.get("clip"))
            if not c:
                errors.append(f"{sid}: unknown clip {s.get('clip')}")
                continue
            t_in, t_out = parse_tc(s["in"]), parse_tc(s["out"])
            if not (0 <= t_in < t_out <= c["duration"] + 0.05):
                errors.append(f"{sid}: in/out {t_in}-{t_out} outside clip {c['id']} (0-{c['duration']})")
            shots.append({**s, "_in": t_in, "_out": t_out, "_dur": t_out - t_in, "_act": a.get("title"),
                          "_label": labels.get(c["id"], {})})

    if not shots:
        return {"errors": errors or ["no shots"], "warnings": warnings, "stats": {}}

    total = sum(s["_dur"] for s in shots)
    durs = sorted(s["_dur"] for s in shots)
    for prev, cur in zip(shots, shots[1:]):
        if prev["clip"] == cur["clip"] and abs(prev["_out"] - cur["_in"]) < 1.0:
            warnings.append(f"{cur['id']}: continues {prev['id']} from the same clip (jump cut?)")
        a, b = prev["_label"].get("shot_size"), cur["_label"].get("shot_size")
        if a and a == b and prev["_act"] == cur["_act"] and prev["_label"].get("focal_feel") == cur["_label"].get("focal_feel") \
                and not cur.get("cut", "").startswith(MOTIVATED_CUTS):
            warnings.append(f"{cur['id']}: same size+focal as previous ({a}); change perspective or justify the cut")
    for s in shots:
        if s["_dur"] > 8 and s.get("role") != "hold":
            warnings.append(f"{s['id']}: {s['_dur']:.1f}s is long for this pacing; mark role 'hold' if intended")
        if s["_dur"] < 0.6:
            warnings.append(f"{s['id']}: {s['_dur']:.2f}s may read as a flash frame")
        if s["_label"] and s["_label"].get("quality", 3) <= 2:
            warnings.append(f"{s['id']}: uses low-quality clip {s['clip']}")
    used = {}
    for s in shots:
        for (a, b, sid) in used.get(s["clip"], []):
            if s["_in"] < b and a < s["_out"]:
                warnings.append(f"{s['id']}: overlaps footage already used in {sid}")
        used.setdefault(s["clip"], []).append((s["_in"], s["_out"], s["id"]))
    if abs(total - target) > 0.15 * target:
        warnings.append(f"runtime {total/60:.1f} min vs target {target/60:.1f} min")

    vo = sum(s["_dur"] for s in shots if s.get("vo_line") or s.get("role") == "vo")
    stats = {
        "shots": len(shots),
        "runtime_min": round(total / 60, 2),
        "target_min": round(target / 60, 2),
        "avg_shot_s": round(total / len(shots), 2),
        "median_shot_s": round(durs[len(durs) // 2], 2),
        "vo_share": round(vo / total, 2) if total else 0,
        "clips_used": len(used),
        "acts": len(seq.get("acts", [])),
    }
    return {"errors": errors, "warnings": warnings, "stats": stats}
