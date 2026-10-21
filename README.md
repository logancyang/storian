# storian

**From hundreds of gigabytes of raw footage to a director-quality storyboard. You chat; an agent does the rest.**

Storian is an agent-first tool for cinematic travel and lifestyle films. Point your coding agent
(Claude Code, Codex, …) at a folder of ungraded camera footage (S-Log3 4K H.265 is fine), with an
optional script or a paragraph of ideas. The agent:

1. ingests everything cheaply: keyframe-only hardware decode, a log → Rec.709 LUT, motion signals, contact sheets
2. labels every clip like an assistant editor: shot size, focal feel, angle, movement, subject, action, mood, and the usable in/out **moments**
3. proposes three treatments (theme, mood, central idea, motif) and lets you pick
4. directs a sequence with craft encoded in [`knowledge/director.md`](storian/knowledge/director.md): perspective changes, cuts on action and motion, pacing curves, VO vs B-roll sections, motif and bookends
5. serves a **storyboard on localhost**: theme, mood and idea at the top, then every shot with frames, clip name, labels, in/out timecodes, VO line and a director's note, plus a playable animatic

6. reviews coverage like a director on the dailies: which scenes lack close-ups, a tele
   perspective, an establishing wide, a human reaction, an entry or exit, or an action covered
   from two sizes. It turns those gaps into a **shot list for the videographer** (what, lens,
   angle, move, how long, and why), shown at the top of the storyboard

Then you say things like *"act 3 drags"* or *"swap s047 for something with more motion"*, and
the agent edits the plan. The page updates live.

## Quick start (for your agent)

```bash
git clone https://github.com/logancyang/storian && cd storian
uv sync
uv run storian init "/path/to/footage" -p ~/storian-projects/trip
uv run storian -p ~/storian-projects/trip ingest
uv run storian -p ~/storian-projects/trip status   # tells the agent what to do next
```

Tell your agent: *"Use storian (read AGENTS.md) to make a storyboard from this footage."*
[`AGENTS.md`](AGENTS.md) is the operating manual.

Requirements: Python ≥ 3.11, [uv](https://docs.astral.sh/uv/), `ffmpeg`/`ffprobe`, `exiftool`.
macOS uses VideoToolbox hardware decode and falls back to software elsewhere.

## Commands

| command | what it does |
|---|---|
| `init <footage> -p <proj>` | create a project (`--brief`, `--target-minutes`) |
| `scan` | probe every clip (duration, codec, gamma, lens, record time) |
| `frames` | keyframes + log LUT + motion signals + contact sheets |
| `label todo/status/schema` | labeling worklist for the agent (`--shard k/n` for parallel labelers) |
| `digest` | one line per clip with every labeled moment |
| `check` | validate `sequence.json` and lint it against editing rules |
| `previews` | render H.264 previews of only the chosen ranges |
| `coverage` | scenes, coverage counts and gaps; `--scaffold` starts `coverage.json` |
| `serve` | storyboard + animatic at http://localhost:7878 |
| `status` | pipeline state and next step |
| `knowledge` | print the director playbook and schemas |

## Design

See [`docs/design.html`](docs/design.html) for the market survey (54 products) and the full
design, and [`docs/mobile.md`](docs/mobile.md) for Storian Cloud: the paid mobile and sync plan.
Roadmap: reference-film style learning → OTIO/FCPXML export to DaVinci Resolve → local
VLM first-pass labeling → music beat / VO timing.

## License

MIT
