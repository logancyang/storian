"""Coverage review: group clips into scenes, measure what each scene was shot with, and flag the
shots a director would send the camera operator back for (see knowledge/coverage.md).

The numbers and rule-based gaps here are facts the agent starts from. The agent's judgement
(scene names, verdicts, the concrete shot list) lives in coverage.json and wins where present.
"""

import re
from collections import Counter
from datetime import datetime
from zoneinfo import ZoneInfo

from .media import parse_tc
from .project import Project, read_json

SIZE_BUCKETS = {"EWS": "wide", "WS": "wide", "MWS": "medium", "MS": "medium",
                "MCU": "close", "CU": "close", "ECU": "detail", "insert": "detail"}
FOCAL_BUCKETS = {"ultra-wide": "wide_lens", "wide": "wide_lens", "normal": "normal", "tele": "tele"}
STILL_MOVES = {"static", "handheld-still", "timelapse"}
TRAVEL_MOVES = {"walk-follow", "walk-lead", "vehicle", "tracking"}
PEOPLE = re.compile(r"\b(woman|man|men|women|girl|boy|person|people|she|he|her|friend|couple|"
                    r"child|kid|diners|shoppers|crowd|pedestrians|skaters|commuters|vendor|staff|hands?)\b")
# matrix columns, in display order
COLUMNS = ["wide", "medium", "close", "detail", "wide_lens", "normal", "tele", "angle", "moving", "people", "in_out"]
USABLE = 3          # quality at which a clip counts as coverage
SCENE_GAP_S = 20 * 60
REJOIN_S = 2 * 3600
STOP = {"hong", "kong", "area", "street", "the", "of", "and", "near", "interior", "view", "likely", "island", ""}

# code -> (severity 3/2/1, the shot to get, why a director wants it)
RULES = {
    "thin": (3, "a full 5-shot sequence: wide, medium, close on hands, close on a face, an unusual angle",
             "fewer than three usable clips: this is a fragment, not a scene, so it can only be a cutaway"),
    "no-establishing": (3, "an establishing wide (EWS/WS), locked off, 6–8 s",
                        "the audience never learns where we are or how the space is laid out"),
    "no-close": (3, "close-ups (MCU/CU) of the subject: faces, hands at work",
                 "the scene stays at arm's length, and there is nothing tight to cut to on an action"),
    "no-detail": (2, "2–3 inserts: hands, textures, signage, an object in use (ECU/insert), 2–3 s each",
                  "inserts are the editor's glue: they compress time, hide jump cuts and carry VO"),
    "no-medium": (2, "a medium (MWS/MS) that shows who is doing what",
                  "cutting straight from wide to close is a big leap; mediums carry the action"),
    "no-wide": (2, "a wide that places the subject in the space",
                "everything is tight, so the viewer has no geography and the scene can't open or close"),
    "unusable": (3, "a reshoot of the scene: the takes exist but are shaky, soft or blocked",
                 "there is footage of this place but almost none of it is usable"),
    "no-tele": (2, "a tele shot (85mm+ feel): compress the background, isolate a face or detail",
                "no tele in the scene, so nothing is compressed or isolated and it all reads as snapshots"),
    "one-focal-wide": (2, "a tele shot (85mm+ feel) of the same subject from far back",
                       "every shot is wide-angle: tele compression and shallow depth are what make it feel cinematic"),
    "one-focal-tele": (2, "a wide-lens shot close to the subject for context and energy",
                       "every shot is tele: the scene has intimacy but no space or immersion"),
    "flat-angle": (1, "one high, low, overhead or POV angle",
                   "every shot is at eye level, so the sequence has no visual surprise"),
    "no-movement": (1, "one moving shot: a push-in, walk-follow or tracking move",
                    "everything is locked off; one move gives energy and a way into the scene"),
    "no-static": (1, "a locked-off static frame, 6 s or more",
                  "everything moves; VO and holds need a still frame to rest on"),
    "no-people": (2, "a human moment: someone reacting, a face, hands",
                  "no person on screen, so the scene is a postcard instead of an experience"),
    "no-in-out": (1, "an entry or exit: walk into or out of frame, a door, a vehicle pulling away",
                  "the edit needs a way in and out of the scene that isn't a hard cut"),
    "no-action-pair": (2, "the same action from a second size (wide, then tight on the hands) so you can cut on it",
                       "no action is covered from two sizes, so there is nowhere to match-cut on action"),
    "no-hero": (1, "one hero frame: best light, strongest composition, clean motion",
                "nothing here rates a 5: the scene has coverage but no image to open or close it on"),
}

# who has to be in front of the camera for each rule's fix: "none" (place, objects, light),
# "unrecognizable" (a figure nobody can identify: silhouette, far away, from behind), "talent"
SUBJECT = {"thin": "talent", "unusable": "talent", "no-close": "talent", "no-medium": "talent",
           "no-people": "talent", "no-action-pair": "talent", "no-in-out": "unrecognizable"}


def local_time(c, tz: str | None):
    """Record time as a timezone-aware datetime in the shoot's local zone (camera clocks often
    keep the home timezone; the offset they store makes the conversion exact)."""
    try:
        t = datetime.strptime((c.get("recorded_at") or "")[:25].replace("Z", "+00:00"), "%Y:%m:%d %H:%M:%S%z")
    except ValueError:
        return None
    return t.astimezone(ZoneInfo(tz)) if tz else t


def scene_when(clips: list, lbs: list, tz: str | None) -> dict:
    """When the scene was shot and what the light was, so a reshoot can match it."""
    times = sorted(t for t in (local_time(c, tz) for c in clips) if t)
    if not times:
        return {}
    light = Counter(lb.get("light") for lb in lbs if lb.get("light")).most_common(1)
    return {"date": times[0].strftime("%a %d %b %Y"), "start": times[0].strftime("%H:%M"),
            "end": times[-1].strftime("%H:%M"), "tz": times[0].tzname() or "",
            "time_of_day": sorted({lb.get("time_of_day") for lb in lbs if lb.get("time_of_day")}),
            "light": light[0][0] if light else ""}


def _time(c):
    try:
        return datetime.strptime((c.get("recorded_at") or "")[:19], "%Y:%m:%d %H:%M:%S").timestamp()
    except ValueError:
        return None


def _tokens(loc):
    return {w for w in re.split(r"[^a-z0-9]+", (loc or "").lower()) if w not in STOP and len(w) > 2}


def _place(loc):
    return (loc or "").split(",")[0].split("(")[0].strip().lower()


def auto_scenes(clips: list, labels: dict) -> list:
    """Split the shooting day by record time, then by location within a session.
    A scene breaks on a 20 min pause, or on a 3 min pause where the labelled location shares
    no words with the previous clip's. Coming back to the same place within 2 h rejoins it."""
    scenes, prev_end, prev_tokens = [], None, None
    for c in sorted(clips, key=lambda c: (c.get("recorded_at") or "", c["id"])):
        t = _time(c)
        loc = labels.get(c["id"], {}).get("location")
        tok = _tokens(loc)
        gap = (t - prev_end) if (t is not None and prev_end is not None) else 0
        new_place = gap > 180 and tok and prev_tokens and not tok & prev_tokens
        rejoin = gap < REJOIN_S and scenes and _place(loc) == scenes[-1]["places"].most_common(1)[0][0]
        if not scenes or new_place or (gap > SCENE_GAP_S and not rejoin):
            scenes.append({"ids": [], "places": Counter()})
        scenes[-1]["ids"].append(c["id"])
        scenes[-1]["places"][_place(loc)] += 1
        prev_end = (t + c.get("duration", 0)) if t is not None else prev_end
        prev_tokens = tok or prev_tokens
    out = []
    for i, sc in enumerate(scenes, 1):
        locs = Counter(labels.get(x, {}).get("location", "").split(",")[0].strip() for x in sc["ids"])
        name = next((l for l, _ in locs.most_common() if l), f"Scene {i}")
        out.append({"id": f"sc{i:02d}", "name": name, "clips": sc["ids"]})
    return out


def clip_buckets(lb: dict) -> set:
    """Which coverage columns one clip fills."""
    b = set()
    roles = set(lb.get("story_role", []))
    size = SIZE_BUCKETS.get(lb.get("shot_size"))
    if size:
        b.add(size)
    if lb.get("shot_size") == "CU" and "detail" in roles:
        b.add("detail")
    if lb.get("focal_feel") in FOCAL_BUCKETS:
        b.add(FOCAL_BUCKETS[lb["focal_feel"]])
    if lb.get("angle") not in (None, "eye"):
        b.add("angle")
    move = lb.get("camera_move")
    if move and move not in STILL_MOVES:
        b.add("moving")
    elif move:
        b.add("static")
    text = " ".join(lb.get("subjects", [])) + " " + lb.get("action", "")
    if roles & {"portrait", "reaction"} or PEOPLE.search(text.lower()):
        b.add("people")
    if "transition" in roles or move in TRAVEL_MOVES or "travel" in roles:
        b.add("in_out")
    if "establishing" in roles:
        b.add("establishing")
    if lb.get("quality", 0) >= 5:
        b.add("hero")
    return b


def scene_gaps(lbs: list) -> list:
    """Rule-based gaps for one scene from its usable clips' labels."""
    good = [lb for lb in lbs if lb.get("quality", 3) >= USABLE]
    n = Counter(b for lb in good for b in clip_buckets(lb))
    if len(good) < 3:
        return ["unusable" if len(lbs) >= 3 else "thin"]
    gaps = []
    if not n["wide"] and not n["establishing"]:
        gaps.append("no-establishing")
    elif not n["wide"]:
        gaps.append("no-wide")
    if not n["close"] and not n["detail"]:
        gaps.append("no-close")
    if not n["detail"]:
        gaps.append("no-detail")
    if not n["medium"] and n["wide"] and (n["close"] or n["detail"]):
        gaps.append("no-medium")
    if n["wide_lens"] and not n["tele"] and not n["normal"]:
        gaps.append("one-focal-wide")
    elif n["tele"] and not n["wide_lens"] and not n["normal"]:
        gaps.append("one-focal-tele")
    elif not n["tele"] and len(good) >= 4:
        gaps.append("no-tele")
    if not n["angle"] and len(good) >= 4:
        gaps.append("flat-angle")
    if not n["moving"] and len(good) >= 3:
        gaps.append("no-movement")
    if not n["static"] and len(good) >= 3:
        gaps.append("no-static")
    if not n["people"]:
        gaps.append("no-people")
    if not n["in_out"] and len(good) >= 4:
        gaps.append("no-in-out")
    if not _has_action_pair(good):
        gaps.append("no-action-pair")
    if not n["hero"] and len(good) >= 4:
        gaps.append("no-hero")
    return gaps


def _has_action_pair(lbs: list) -> bool:
    """True when some action is covered at two different size buckets (a cut-on-action pair)."""
    sizes = {SIZE_BUCKETS.get(lb.get("shot_size")) for lb in lbs
             if "action" in lb.get("story_role", []) or any(m.get("match_action") for m in lb.get("moments", []))}
    sizes.discard(None)
    return len(sizes) >= 2


def _sequence_usage(p: Project) -> dict:
    if not p.sequence_path.exists():
        return {}
    used = {}
    for a in read_json(p.sequence_path).get("acts", []):
        for s in a.get("shots", []):
            used.setdefault(s.get("clip"), []).append(s.get("id"))
    return used


def importance(n_clips: int, n_used: int) -> str:
    if n_used >= 4 or n_clips >= 10:
        return "core"
    if n_used >= 1 or n_clips >= 4:
        return "support"
    return "minor"


def analyze(p: Project) -> dict:
    """Coverage facts per scene plus film-level gaps; merges the agent's coverage.json."""
    clips = p.clips()
    labels = p.labels()
    review = read_json(p.coverage_path) if p.coverage_path.exists() else {}
    defined = [s for s in review.get("scenes", []) if s.get("clips")]
    scenes = defined or auto_scenes([c for c in clips if c["id"] in labels], labels)
    used = _sequence_usage(p)
    known = {c["id"] for c in clips}
    errors, assigned = [], Counter(x for s in scenes for x in s["clips"])
    for s in scenes:
        errors += [f"{s['id']}: unknown clip {x}" for x in s["clips"] if x not in known]
    errors += [f"clip {x} is in {k} scenes" for x, k in assigned.items() if k > 1]
    unassigned = [c for c in labels if c not in assigned] if defined else []
    weight = {"core": 1.0, "support": 0.6, "minor": 0.25}
    rev = {r.get("id"): r for r in review.get("scenes", [])}
    clip_map = {c["id"]: c for c in clips}
    tz = p.config.get("timezone")

    out = []
    for s in scenes:
        lbs = [labels[x] for x in s["clips"] if x in labels]
        good = [lb for lb in lbs if lb.get("quality", 3) >= USABLE]
        counts = Counter(b for lb in good for b in clip_buckets(lb))
        shots_used = [sid for x in s["clips"] for sid in used.get(x, [])]
        r = rev.get(s["id"], {})
        imp = r.get("importance") or importance(len(lbs), len(shots_used))
        gaps = scene_gaps(lbs)
        if imp == "minor":
            gaps = [g for g in gaps if g in ("thin", "unusable")]
        secs = sum(max(0, parse_tc(m["out"]) - parse_tc(m["in"])) for lb in good for m in lb.get("moments", [])
                   if m.get("score", 3) >= 3)
        # representative frames: best clip per size bucket, then by quality
        reps = sorted(good or lbs, key=lambda lb: -lb.get("quality", 0))
        seen, thumbs = set(), []
        for lb in reps:
            k = SIZE_BUCKETS.get(lb.get("shot_size"))
            if k not in seen:
                seen.add(k)
                thumbs.append(_thumb(lb))
        thumbs += [_thumb(lb) for lb in reps if _thumb(lb) not in thumbs][: max(0, 6 - len(thumbs))]
        score = round(sum(RULES[g][0] for g in gaps) * weight[imp], 1)
        out.append({
            "id": s["id"], "name": r.get("name") or s.get("name") or s["id"], "clips": s["clips"], "importance": imp,
            "n": len(lbs), "usable": len(good), "usable_s": round(secs), "used": shots_used,
            "time_of_day": sorted({lb.get("time_of_day") for lb in lbs if lb.get("time_of_day")}),
            "counts": {k: counts[k] for k in COLUMNS},
            "gaps": [{"code": g, "severity": RULES[g][0], "need": RULES[g][1], "why": RULES[g][2],
                      "subject": SUBJECT.get(g, "none")} for g in gaps],
            "when": scene_when([clip_map[x] for x in s["clips"] if x in clip_map], lbs, tz),
            "wardrobe": r.get("wardrobe", ""),
            "score": score, "thumbs": thumbs[:6],
            "reviewed": bool(r),
            "verdict": r.get("verdict", ""),
            "needs": r.get("needs", []),
        })
    return {
        "summary": review.get("summary", ""),
        "scenes": out,
        "film": film_gaps(labels, p) + [{"code": "agent", "severity": 2, "need": f, "why": ""}
                                        for f in review.get("film", [])],
        "pickups": review.get("pickups", []),
        "errors": errors,
        "unassigned": unassigned,
        "reviewed": bool(review),
    }


def _thumb(lb):
    m = max(lb.get("moments") or [{"in": 1, "out": 2}], key=lambda m: m.get("score", 0))
    return {"clip": lb.get("clip"), "t": round((parse_tc(m["in"]) + parse_tc(m["out"])) / 2, 1),
            "size": lb.get("shot_size"), "q": lb.get("quality")}


def film_gaps(labels: dict, p: Project) -> list:
    """Gaps across the whole library and in each act of the current sequence."""
    good = [lb for lb in labels.values() if lb.get("quality", 3) >= USABLE]
    roles = Counter(r for lb in good for r in lb.get("story_role", []))
    tod = Counter(lb.get("time_of_day") for lb in good)
    focal = Counter(FOCAL_BUCKETS.get(lb.get("focal_feel")) for lb in good)
    gaps = []

    def add(sev, need, why):
        gaps.append({"code": "film", "severity": sev, "need": need, "why": why})

    if roles["closer"] < 3:
        add(3, "ending images: a walk-away, a rising or pull-out wide, the motif in its final form",
            f"only {roles['closer']} usable clips read as an ending, so the film can't land")
    if roles["hook"] + roles["opener"] < 4:
        add(2, "opening images: a sensory burst or a mysterious detail that reveals the place",
            "few clips are strong enough to open the film")
    if roles["reaction"] < 3:
        add(2, "reaction shots: a face watching, laughing, tasting, looking out of a window",
            f"only {roles['reaction']} reaction shots: the viewer sees places but rarely sees someone feel them")
    if tod["golden-hour"] + tod["dusk"] < 3:
        add(1, "golden hour or dusk: warm low light, long shadows, silhouettes",
            "almost no warm light, so the film's palette has no warm end")
    if good and focal["tele"] / len(good) < 0.15:
        add(2, "more tele: compressed street depth, isolated faces in crowds, stacked skylines",
            f"only {focal['tele']} of {len(good)} usable clips feel tele")
    if p.sequence_path.exists():
        seq = read_json(p.sequence_path)
        runtime = sum(parse_tc(x["out"]) - parse_tc(x["in"]) for a in seq.get("acts", []) for x in a.get("shots", []))
        target = float(p.config.get("target_minutes", 15)) * 60
        if runtime < 0.85 * target:
            add(3, f"about {(target - runtime) / 60:.0f} more minutes of cuttable scenes to reach the "
                   f"{target / 60:.0f} min target: new places, or deeper coverage of the core scenes",
                f"the footage supports a {runtime / 60:.1f} min cut at full quality")
        for i, a in enumerate(seq.get("acts", []), 1):
            lbs = [labels.get(s.get("clip"), {}) for s in a.get("shots", [])]
            sizes = {SIZE_BUCKETS.get(lb.get("shot_size")) for lb in lbs} - {None}
            missing = [b for b in ("wide", "medium", "close", "detail") if b not in sizes]
            if len(lbs) >= 6 and len(missing) >= 2:
                add(2, f"act {i} “{a.get('title')}”: {' and '.join(missing)} shots for this chapter",
                    f"the cut of this act has no {' or '.join(missing)} shots because the footage has none")
    return gaps
