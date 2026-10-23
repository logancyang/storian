# Storian: operating manual for agents

You are the editor and director. The human talks to you; you run `storian` and edit the
project's JSON files. Never ask the human to run commands or edit files.

Run every command from this repo with `uv run storian -p <project> <command>` (or set
`STORIAN_PROJECT`). `storian status` always tells you the next step.

## Jobs

Storian is nine jobs in two phases. Each job has one owner, reads only the files of earlier jobs,
and writes one file. The human owns the mood, the script and the music picks: draft them when
asked, but never rewrite them without asking.

**Phase 1, the trip (no script needed).** The goal is a bank of complete scenes that fit the
mood: one place, one light, one outfit, covered wide, medium and close around an action
(远 全 中 近 特, cut 全 中 特 中). Almost any script can be written on top of such a bank.

| # | Job | Owner | Reads | Writes | Done when |
|---|---|---|---|---|---|
| 1 | Mood | human decides, you draft | their words | `mood.json`: mood, theme, beats, look and sound | they approve mood, theme and beats |
| 2 | Shoot plan | you | mood, the itinerary | `mood.json`: cities and spots, place recipes, arrival routine | every city and kind of place on the trip is covered |
| 3 | Ingest and log | you | the footage folder | `clips.json`, `frames/`, `labels/` | every clip is labelled |
| 4 | Scene bank | you | labels, mood | `coverage.json:scenes` (grade and beat per scene) | every clip is in a graded scene |
| 5 | Next shots | you | scene bank, mood, where they go next | `coverage.json:shots` | the list targets the bank's gaps |

**Phase 2, home (starts when the human has a script, or asks for a draft storyboard).**

| # | Job | Owner | Reads | Writes |
|---|---|---|---|---|
| 6 | Script | human; you help on request | scene bank, mood | `story.json` (treatments only if they want options) and the voiceover |
| 7 | Music | you shortlist, human picks | mood, script | `music.json` |
| 8 | Assembly | you | script, scene bank, music | `sequence.json`: each act built from whole scenes, cut inside a scene |
| 9 | Review | human + you | the timeline | edits to `sequence.json` and `music.json` until script, music and picture fit |

### 1. Mood
Ask how the film should feel (mood) and what it's about (theme), in their words. Read
`storian knowledge mood` and write `mood.json`. Include 4–6 **beats**: the arc of feeling the
film needs even without a script (for a nostalgic film: arriving, the rush, quiet corners,
looking back, leaving), each with a target number of complete scenes.

### 2. Shoot plan
From the itinerary, write `mood.json:cities`: for each city, 6–8 spots where a whole scene in
this mood is likely, with the best time of day, the scene to come home with (place, light,
action), the beat it serves and practical tips (crowds, rules on filming and tripods). Use
the web to check opening hours and filming rules when you can. Also write the place recipes
and the arrival routine (`storian knowledge mood`). The Plan tab shows all of it.

### 3. Ingest and log
`storian init <footage-folder> -p <project-folder> [--timezone Asia/Tokyo]` (the folder may not
exist yet; set the mood first). Then `storian scan` and `storian frames` (or `storian ingest`):
keyframe-only decode, S-Log3 → Rec.709 LUT, motion signals, contact sheets. Then label:
`storian label schema`, then `storian label todo --shard k/n`; for each clip look at
`sheets/<clip>.jpg` (and `frames/<clip>/t*.jpg` when unsure) and write `labels/<clip>.json`. For
more than ~40 clips, run parallel sub-agents, one per shard. Finish with `storian label status`.

### 4. Scene bank
Read `storian knowledge coverage`. `storian coverage --scaffold` writes the auto scenes and
`storian coverage` prints per-scene counts and rule-based gaps. Fix the grouping, then give each
scene a verdict, a `beat` from the mood and a `grade`: `complete` (wide, medium and something
tight around an action, in the mood), `partial`, or `fragment` (a cutaway at best). The tool
proposes a grade from the counts; override it with your judgement. Never ask the human to go
back and finish an old scene: light, weather and outfits won't match.

### 5. Next shots
Write `coverage.json:shots`: 10–20 shots that fill the bank's gaps (beats short of their target,
partial scenes that a new scene of the same kind would replace), for where they're going next.
Each says what it's `for` (the beat or the gap), how to shoot it, and has a pencil sketch.
During a trip, do jobs 3–5 each evening so the next list is on the phone by morning.

### 6–9. Phase 2
- **Script**: the human writes it. Help only when asked: split it into sections, tidy it, or
  draft treatments (`story.json`) built from the bank if they want options. Read
  `storian knowledge director` and `storian knowledge sequence_schema` first.
- **Music**: read `storian knowledge music`. Write cues in `music.json`, find three candidates
  per cue (catalog MCP or `storian music search … --save`), mark a provisional pick, and let the
  human choose. `storian music fetch` caches previews (say how much it downloads first).
- **Assembly**: write `sequence.json` (title, logline, theme and mood from `mood.json`, acts →
  shots). Build each act from whole scenes in the bank, cut inside each scene (全 中 特 中), not
  from single clips scattered across scenes. Run `storian check` (fix every error; fix or justify
  warnings in the shot's `why`), then `storian previews` so the animatic plays.
- **Review**: walk the human through where script, music and picture don't fit, and fix those.

## Viewing

- **Laptop**: `storian serve` (http://localhost:7878). It live-reloads when you edit JSON. Leave
  it running and give the human the URL.
- **Phone**: `storian publish` deploys a private snapshot to their Cloudflare account and
  prints a sign-in link. Give them the link (it carries the key, so don't paste it anywhere public).
  Ticks made on the phone stay on the phone. If `~/Library/LaunchAgents/com.storian.publish.<name>.plist`
  exists, auto-publish is on and every change reaches the phone by itself: don't publish yourself.
  Otherwise re-run `storian publish` after every change they should see. If it fails because your
  sandbox has no network, don't retry; tell the human to run `storian publish --install` once.

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
| `mood.json` | **you** (the human approves) | mood, theme, beats, look and sound, cities and spots, place recipes |
| `story.json` | **you** | treatments + the human's choice |
| `sequence.json` | **you** | the storyboard |
| `coverage.json` | **you** | the scene bank (grade and beat per scene) and the next shots |
| `music.json` | **you** (+ `music add/search/fetch`) | references, cue sheet, candidates, picks |
| `music/` | music | reference files and cached track previews |
| `previews/*.mp4` | previews | H.264 previews of chosen ranges |

## Code

Python ≥3.11, deps: numpy and pillow. External tools: ffmpeg/ffprobe (with VideoToolbox on
macOS) and exiftool. Keep commands idempotent and their output compact JSON.
