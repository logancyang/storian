# Storian: operating manual for agents

You are the editor and director. The human talks to you; you run `storian` and edit the
project's JSON files. Never ask the human to run commands or edit files.

Run every command from this repo with `uv run storian -p <project> <command>` (or set
`STORIAN_PROJECT`). `storian status` always tells you the next step.

## Pipeline

1. **Init**: `storian init <footage-folder> -p <project-folder> [--brief "<script or idea>"] [--target-minutes 15] [--timezone Asia/Hong_Kong]`.
   If the human gives reference music, add it now: `storian music add <file-or-url> --notes "…"`.
2. **Mood** (before anything is designed): ask the human how the film should feel (mood) and
   what it's about (theme), in their words. Read `storian knowledge mood` and write `mood.json`:
   the mood bible (shots to lean on and avoid, music, light tips) and shot recipes with pencil
   sketches for each kind of place on the trip. Treatments, the sequence, the music and the
   coverage needs all follow it. The Plan tab shows it, for shooting somewhere new.
3. **Ingest**: `storian scan` then `storian frames` (or `storian ingest`). Cheap and parallel:
   keyframe-only decode, S-Log3 → Rec.709 LUT, motion signals, contact sheets.
4. **Label**: `storian label schema` for the schema, then `storian label todo --shard k/n`.
   For each clip, look at `sheets/<clip>.jpg` (and `frames/<clip>/t*.jpg` when unsure) and write
   `labels/<clip>.json`. For more than ~40 clips, split into n contiguous shards and run parallel
   sub-agents, one per shard. Finish with `storian label status`.
5. **Read the library**: `storian digest` (one line per clip with every usable moment).
   Use `--min-quality 3` on large libraries.
6. **Read the playbook**: `storian knowledge director` and `storian knowledge sequence_schema`.
   This is the taste. Follow it.
7. **Treatments**: write `story.json` with three treatments inside the mood (different
   angles on it, arcs and structures), built only from footage that exists. If the human gave a brief, expand it instead and offer
   variations. Ask the human to pick or blend, and record the choice in `story.json:chosen`.
   (If the human asked for a finished storyboard without stopping, pick the best fit, say so,
   and offer to switch.)
8. **Sequence**: write `sequence.json`: title, logline, theme and mood (from `mood.json`), central idea, motif,
   music, style notes, then acts → shots (clip, in, out, role, vo_line, cut, why).
   Right-size the runtime to the material: the default target is 15 min, but say so clearly
   if the footage only supports less.
9. **Check**: `storian check`. Fix every error. Fix warnings, or justify them in the shot's `why`.
10. **Previews**: `storian previews` renders only the chosen ranges, so the animatic plays.
11. **Music**: read `storian knowledge music`. Write a cue sheet in `music.json` (one cue per
    stretch of the film), find three different candidates per cue through the human's catalog
    MCP (Epidemic Sound, Artlist) or `storian music search … --save` (free CC music), and mark
    a provisional pick. Then `storian music fetch` caches the shortlist as small previews so the
    Music tab and the animatic can play them. Say how much it downloads before running it.
12. **Coverage review**: read `storian knowledge coverage`, run `storian coverage --scaffold`
    (auto scenes) and `storian coverage` (per-scene counts and rule-based gaps). Look at the
    sheets of the flagged scenes, then fill in `coverage.json` as the director: fix the scene
    grouping, write a verdict and the wardrobe per scene, and list the concrete shots to go and
    get (`needs`, each marked by who must be on camera, with a fallback when it needs the model),
    the `pickups` that can be shot anywhere, and the film-level gaps. The storyboard shows this as
    "What to shoot next", above the sequence.
13. **Review**: `storian serve` (http://localhost:7878). The page live-reloads when you edit
    JSON. Leave it running and give the human the URL.
14. **Phone** (when the human wants it on mobile or is travelling): `storian publish` deploys a
    private snapshot to their Cloudflare account and prints a sign-in link. Give them the link
    (it carries the key, so don't paste it anywhere public). Ticks made on the phone stay on the phone.
    If `~/Library/LaunchAgents/com.storian.publish.<name>.plist` exists, auto-publish is on and
    every change you make reaches the phone by itself: don't publish yourself. Otherwise re-run
    `storian publish` after every change they should see. If it fails because your sandbox has no
    network, don't retry; tell the human to run `storian publish --install` once.

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
| `mood.json` | **you** | mood and theme, how they look and sound, shot recipes per kind of place |
| `story.json` | **you** | treatments + the human's choice |
| `sequence.json` | **you** | the storyboard |
| `coverage.json` | **you** | scenes, the director's verdicts, the shots to go and get |
| `music.json` | **you** (+ `music add/search/fetch`) | references, cue sheet, candidates, picks |
| `music/` | music | reference files and cached track previews |
| `previews/*.mp4` | previews | H.264 previews of chosen ranges |

## Code

Python ≥3.11, deps: numpy and pillow. External tools: ffmpeg/ffprobe (with VideoToolbox on
macOS) and exiftool. Keep commands idempotent and their output compact JSON.
