"""storian CLI. Built to be driven by an agent: every command is idempotent, prints compact
machine-readable output, and leaves its results as plain JSON files in the project folder."""

import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from . import media
from .check import check_sequence
from .project import Project, read_json, write_json

KNOWLEDGE = Path(__file__).parent / "knowledge"


def resolve_project(args) -> Project:
    root = args.project or os.environ.get("STORIAN_PROJECT") or "."
    p = Project(Path(root))
    if not p.exists():
        sys.exit(f"no storian project at {p.root} (run `storian init <footage> --project <dir>`)")
    return p


def progress(i, n, label):
    if not sys.stderr.isatty():
        return
    print(f"\r[{i}/{n}] {label}".ljust(60), end="", file=sys.stderr, flush=True)


# ---------------------------------------------------------------- commands

def cmd_init(args):
    footage = Path(args.footage).expanduser().resolve()
    if not footage.is_dir():
        sys.exit(f"footage folder not found: {footage}")
    root = Path(args.project or f"./{footage.name}.storian").expanduser()
    p = Project(root)
    cfg = p.config if p.exists() else {}
    cfg.update({
        "name": cfg.get("name") or footage.name,
        "footage_dir": str(footage),
        "target_minutes": args.target_minutes or cfg.get("target_minutes", 15),
        "created": cfg.get("created") or datetime.now().isoformat(timespec="seconds"),
    })
    if args.brief:
        cfg["brief"] = Path(args.brief).read_text() if Path(args.brief).is_file() else args.brief
    write_json(p.config_path, cfg)
    media.write_slog3_lut(p.lut_path)
    print(json.dumps({"project": str(p.root), **cfg}, indent=2))


def cmd_scan(args):
    p = resolve_project(args)
    known = p.clip_map()
    files = p.list_footage()
    todo = [f for f in files if f.stem not in known or known[f.stem]["path"] != str(f)]
    done = 0
    with ThreadPoolExecutor(args.jobs) as ex:
        futs = {ex.submit(media.probe, f): f for f in todo}
        for fut in as_completed(futs):
            c = fut.result()
            known[c["id"]] = c
            done += 1
            progress(done, len(todo), c["id"])
    clips = sorted((c for c in known.values() if Path(c["path"]).exists()),
                   key=lambda c: (c.get("recorded_at") or "", c["id"]))
    write_json(p.clips_path, clips)
    total = sum(c["duration"] for c in clips)
    print(file=sys.stderr)
    print(json.dumps({"clips": len(clips), "new": len(todo), "hours": round(total / 3600, 2),
                      "gb": round(sum(c["size_bytes"] for c in clips) / 1e9, 1),
                      "log_clips": sum(media.is_log(c) for c in clips)}))


def _frames_one(p: Project, clip: dict, force: bool):
    d = p.frames_dir / clip["id"]
    idx = d / "index.json"
    if idx.exists() and not force:
        return read_json(idx)
    for old in d.glob("*.jpg"):
        old.unlink()
    frames = media.extract_keyframes(clip, d, p.lut_path)
    sig = media.frame_signals([d / f["file"] for f in frames])
    for f, s in zip(frames, sig):
        f.update(s)
    data = {"clip": clip["id"], "frames": frames, "motion": media.summarize_motion(sig)}
    media.contact_sheet(clip, frames, d, p.sheets_dir / f"{clip['id']}.jpg")
    write_json(idx, data)
    return data


def cmd_frames(args):
    p = resolve_project(args)
    if not p.lut_path.exists():
        media.write_slog3_lut(p.lut_path)
    clips = p.clips()
    if args.clips:
        clips = [c for c in clips if c["id"] in set(args.clips)]
    done = 0
    with ThreadPoolExecutor(args.jobs) as ex:
        futs = {ex.submit(_frames_one, p, c, args.force): c for c in clips}
        for fut in as_completed(futs):
            c = futs[fut]
            try:
                fut.result()
            except Exception as e:  # keep going; report at the end
                print(f"\n{c['id']}: {e}", file=sys.stderr)
            done += 1
            progress(done, len(clips), c["id"])
    print(file=sys.stderr)
    print(json.dumps({"clips": len(clips), "sheets": len(list(p.sheets_dir.glob('*.jpg')))}))


def cmd_ingest(args):
    cmd_scan(args)
    cmd_frames(args)


def cmd_label(args):
    p = resolve_project(args)
    labels = p.labels()
    clips = p.clips()
    if args.action == "status":
        print(json.dumps({"labeled": len(labels), "total": len(clips),
                          "missing": len([c for c in clips if c["id"] not in labels])}))
        return
    if args.action == "schema":
        print((KNOWLEDGE / "label_schema.md").read_text())
        return
    # todo: next clips that need labels, with everything the labeler needs
    if args.shard:  # shard over the full clip list so shards stay stable while labels land
        k, n = (int(x) for x in args.shard.split("/"))
        size = -(-len(clips) // n)  # contiguous blocks keep neighbouring takes (same scene) together
        clips = clips[(k - 1) * size: k * size]
    todo = [c for c in clips if c["id"] not in labels]
    for c in todo[: args.limit]:
        idx = p.frames_dir / c["id"] / "index.json"
        motion = read_json(idx)["motion"] if idx.exists() else {}
        print(json.dumps({"clip": c["id"], "duration": c["duration"], "lens": c.get("lens"),
                          "recorded_at": c.get("recorded_at"), "motion": motion,
                          "sheet": str(p.sheets_dir / f"{c['id']}.jpg"),
                          "write_to": str(p.labels_dir / f"{c['id']}.json")}))


def cmd_digest(args):
    """One line per usable moment. This is what the sequencing agent reads instead of 300 JSON files."""
    p = resolve_project(args)
    labels = p.labels()
    clips = p.clip_map()
    print("# clip | dur | time | size/focal/angle/move | quality | summary || moments [in-out score: desc (match)]")
    for cid, c in clips.items():
        lb = labels.get(cid)
        if not lb:
            continue
        if args.min_quality and lb.get("quality", 3) < args.min_quality:
            continue
        rec = (c.get("recorded_at") or "")[5:16]
        shot = "/".join(str(lb.get(k, "?")) for k in ("shot_size", "focal_feel", "angle", "camera_move"))
        moments = "; ".join(
            f"[{m['in']:.1f}-{m['out']:.1f} {m.get('score', '?')}: {m.get('desc', '')}"
            + (f" (match: {m['match_action']})" if m.get("match_action") else "") + "]"
            for m in lb.get("moments", []))
        tags = ",".join(lb.get("mood", []) + lb.get("story_role", []))
        print(f"{cid} | {c['duration']:.0f}s | {rec} | {shot} | q{lb.get('quality', '?')} | "
              f"{lb.get('location', '')}: {lb.get('summary', '')} [{tags}] || {moments}")


def cmd_check(args):
    p = resolve_project(args)
    report = check_sequence(p)
    print(json.dumps(report, indent=2))
    if report["errors"]:
        sys.exit(1)


def cmd_previews(args):
    p = resolve_project(args)
    seq = read_json(p.sequence_path)
    clips = p.clip_map()
    jobs = []
    for act in seq["acts"]:
        for s in act["shots"]:
            t_in, t_out = media.parse_tc(s["in"]), media.parse_tc(s["out"])
            out = p.previews_dir / f"{s['clip']}_{t_in:.2f}_{t_out:.2f}.mp4"
            if args.force or not out.exists():
                jobs.append((clips[s["clip"]], t_in, t_out, out))
    done = 0
    with ThreadPoolExecutor(args.jobs) as ex:
        futs = [ex.submit(media.render_preview, c, a, b, o, p.lut_path) for c, a, b, o in jobs]
        for fut in as_completed(futs):
            fut.result()
            done += 1
            progress(done, len(jobs), "previews")
    print(file=sys.stderr)
    print(json.dumps({"rendered": len(jobs)}))


def cmd_status(args):
    """Where the pipeline is and what the agent should do next."""
    p = resolve_project(args)
    clips = p.clips()
    labels = p.labels()
    framed = len(list(p.frames_dir.glob("*/index.json"))) if p.frames_dir.exists() else 0
    story = read_json(p.story_path) if p.story_path.exists() else None
    steps = [
        ("scan", bool(clips), "storian scan"),
        ("frames", clips and framed >= len(clips), "storian frames"),
        ("label", clips and len(labels) >= len(clips), "storian label todo  (view each sheet, write labels/<clip>.json)"),
        ("story", story is not None, "write story.json with 3 treatment options; ask the human to pick"),
        ("chosen", bool(story and story.get("chosen") is not None), "record the human's pick in story.json:chosen"),
        ("sequence", p.sequence_path.exists(), "write sequence.json (read knowledge/director.md first)"),
        ("check", p.sequence_path.exists() and not check_sequence(p)["errors"], "storian check"),
        ("previews", p.previews_dir.exists() and any(p.previews_dir.iterdir()), "storian previews"),
    ]
    nxt = next((cmd for name, ok, cmd in steps if not ok), "storian serve  (and iterate with the human)")
    print(json.dumps({"project": str(p.root), "clips": len(clips), "framed": framed, "labeled": len(labels),
                      "steps": {name: bool(ok) for name, ok, _ in steps}, "next": nxt}, indent=2))


def cmd_serve(args):
    from .server import serve
    serve(resolve_project(args), args.port, args.open)


def cmd_knowledge(args):
    names = [args.name] if args.name else ["director", "label_schema", "sequence_schema"]
    for n in names:
        print((KNOWLEDGE / f"{n}.md").read_text())


def main(argv=None):
    ap = argparse.ArgumentParser(prog="storian", description=__doc__)
    ap.add_argument("--project", "-p", help="project folder (default: $STORIAN_PROJECT or cwd)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    # also accept --project after the subcommand
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--project", "-p", default=argparse.SUPPRESS)
    _add = sub.add_parser
    sub.add_parser = lambda *a, **k: _add(*a, parents=[common], **k)

    s = sub.add_parser("init", help="create a project for a footage folder")
    s.add_argument("footage")
    s.add_argument("--target-minutes", type=float)
    s.add_argument("--brief", help="script / idea text, or a path to a text file")
    s.set_defaults(fn=cmd_init)

    for name, fn, help_ in (("scan", cmd_scan, "probe every clip (ffprobe + camera metadata)"),
                            ("frames", cmd_frames, "keyframes, motion signals, contact sheets"),
                            ("ingest", cmd_ingest, "scan + frames")):
        s = sub.add_parser(name, help=help_)
        s.add_argument("-j", "--jobs", type=int, default=6)
        s.add_argument("--force", action="store_true")
        s.add_argument("--clips", nargs="*")
        s.set_defaults(fn=fn)

    s = sub.add_parser("label", help="labeling worklist for the agent")
    s.add_argument("action", choices=["todo", "status", "schema"])
    s.add_argument("--limit", type=int, default=20)
    s.add_argument("--shard", help="k/n: the k-th of n contiguous blocks of clips (parallel labelers)")
    s.set_defaults(fn=cmd_label)

    s = sub.add_parser("digest", help="compact index of all labels for sequencing")
    s.add_argument("--min-quality", type=int, default=0)
    s.set_defaults(fn=cmd_digest)

    sub.add_parser("check", help="validate + lint sequence.json").set_defaults(fn=cmd_check)

    s = sub.add_parser("previews", help="render H.264 previews for every shot in the sequence")
    s.add_argument("-j", "--jobs", type=int, default=4)
    s.add_argument("--force", action="store_true")
    s.set_defaults(fn=cmd_previews)

    sub.add_parser("status", help="pipeline state and next step").set_defaults(fn=cmd_status)

    s = sub.add_parser("serve", help="storyboard on localhost")
    s.add_argument("--port", type=int, default=7878)
    s.add_argument("--open", action="store_true")
    s.set_defaults(fn=cmd_serve)

    s = sub.add_parser("knowledge", help="print the director playbook and schemas")
    s.add_argument("name", nargs="?", choices=["director", "label_schema", "sequence_schema"])
    s.set_defaults(fn=cmd_knowledge)

    args = ap.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
