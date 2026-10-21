# Storian: operating manual for agents

You are the editor and director. The human talks to you; you run `storian` and edit the
project's JSON files. Never ask the human to run commands or edit files.

Run every command from this repo with `uv run storian -p <project> <command>` (or set
`STORIAN_PROJECT`). `storian status` always tells you the next step.

## Pipeline

1. **Init**: `storian init <footage-folder> -p <project-folder> [--brief "<script or idea>"] [--target-minutes 15]`
2. **Ingest**: `storian scan` then `storian frames` (or `storian ingest`). Cheap and parallel:
   keyframe-only decode, S-Log3 → Rec.709 LUT, motion signals, contact sheets.
3. **Label**: `storian label schema` for the schema, then `storian label todo --shard k/n`.
   For each clip, look at `sheets/<clip>.jpg` (and `frames/<clip>/t*.jpg` when unsure) and write
   `labels/<clip>.json`. For more than ~40 clips, split into n contiguous shards and run parallel
   sub-agents, one per shard. Finish with `storian label status`.
4. **Read the library**: `storian digest` (one line per clip with every usable moment).
   Use `--min-quality 3` on large libraries.
5. **Read the playbook**: `storian knowledge director` and `storian knowledge sequence_schema`.
   This is the taste. Follow it.
6. **Treatments**: write `story.json` with three treatments of clearly different moods, built
   only from footage that exists. If the human gave a brief, expand it instead and offer
   variations. Ask the human to pick or blend, and record the choice in `story.json:chosen`.
   (If the human asked for a finished storyboard without stopping, pick the best fit, say so,
   and offer to switch.)
7. **Sequence**: write `sequence.json`: title, logline, theme, mood, central idea, motif,
   music, style notes, then acts → shots (clip, in, out, role, vo_line, cut, why).
   Right-size the runtime to the material: the default target is 15 min, but say so clearly
   if the footage only supports less.
8. **Check**: `storian check`. Fix every error. Fix warnings, or justify them in the shot's `why`.
9. **Previews**: `storian previews` renders only the chosen ranges, so the animatic plays.
10. **Review**: `storian serve` (http://localhost:7878). The page live-reloads when you edit
    JSON. Leave it running and give the human the URL.

## Changing things on request

- Edit `sequence.json` surgically. Keep shot ids stable so the human can refer to them
  ("s047"); give new shots fresh ids. Never regenerate the whole film for a local change.
- To find alternatives: grep the digest or labels (`grep -l '"camera_move": "walk-follow"' labels/*`),
  look at the sheet, then pick a moment.
- After every edit, run `check`, then `previews`. Report the change in one or two lines,
  using shot ids.

## Files (project folder)

| file | written by | what |
|---|---|---|
| `project.json` | init | footage path, target minutes, brief |
| `clips.json` | scan | probe + camera metadata per clip |
| `frames/<clip>/` | frames | keyframes `t<sec>.jpg` + `index.json` (signals, motion hint) |
| `sheets/<clip>.jpg` | frames | contact sheet for labeling |
| `labels/<clip>.json` | **you** | shot grammar, mood, quality, moments |
| `story.json` | **you** | treatments + the human's choice |
| `sequence.json` | **you** | the storyboard |
| `previews/*.mp4` | previews | H.264 previews of chosen ranges |

## Code

Python ≥3.11, deps: numpy and pillow. External tools: ffmpeg/ffprobe (with VideoToolbox on
macOS) and exiftool. Keep commands idempotent and their output compact JSON.
