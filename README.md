# storian

**From hundreds of gigabytes of raw footage to a director-quality storyboard. You chat; an agent does the rest.**

Storian is an agent-first tool for cinematic travel and lifestyle films. Point your coding agent
(Claude Code, Codex, …) at a folder of ungraded camera footage (S-Log3 4K H.265 is fine), with an
optional script or a paragraph of ideas. The agent:

1. asks for the film's **mood and theme first**, since they decide the music and every shot, and
   turns them into a mood bible plus a **Plan tab** for shooting somewhere new: pick the kind of
   place (street, market, viewpoint…) and get 8 shots in order, each with a pencil sketch of the
   frame, the camera height and how long to hold
2. ingests everything cheaply: keyframe-only hardware decode, a log → Rec.709 LUT, motion signals, contact sheets
3. labels every clip like an assistant editor: shot size, focal feel, angle, movement, subject, action, mood, and the usable in/out **moments**
4. proposes three treatments inside that mood (theme, central idea, motif) and lets you pick
5. directs a sequence with craft encoded in [`knowledge/director.md`](storian/knowledge/director.md): perspective changes, cuts on action and motion, pacing curves, VO vs B-roll sections, motif and bookends
6. serves a **storyboard on localhost**: theme, mood and idea at the top, then every shot with frames, clip name, labels, in/out timecodes, VO line and a director's note, plus a playable animatic

7. reviews coverage like a director on the dailies: which scenes lack close-ups, a tele
   perspective, an establishing wide, a human reaction, an entry or exit, or an action covered
   from two sizes. It turns those gaps into a **shot list for the videographer** (what, lens,
   angle, move, how long, and why), shown at the top of the storyboard. The list is built for
   reshoots without the original outfit: each shot says whether the model is needed, with a
   no-model fallback, plus the scene's original light and wardrobe
8. scores the film: takes your reference tracks, writes a cue sheet per act, finds three
   different candidates per cue (Epidemic Sound or Artlist through their MCP servers, or free
   Creative Commons music built in), checks licences for monetised YouTube, and plays it all in a
   Music tab and under the animatic

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
| `music` | `add` a reference, `search` free CC music, `fetch` previews, `analyze` tempo and energy |
| `serve` | storyboard + animatic at http://localhost:7878 |
| `publish` | private copy on Cloudflare for your phone: shot list, storyboard, music, offline (`--install` republishes in the background on every change, `--link` reprints the sign-in link, `--new-key`, `--dry-run`) |
| `status` | pipeline state and next step |
| `knowledge` | print the director playbook and schemas |

## On your phone

`storian publish` puts a private copy of the storyboard on your own Cloudflare account (free
plan) so you can use it on a shoot: the shot list with tick boxes, the storyboard, the animatic
and the music. It's a static snapshot behind a key you enter once per device, and it keeps
working offline once opened. The footage stays on the laptop; only the frames, contact sheets and
previews the page shows are uploaded (about 350 MB for the HK test project). It needs Node 22+
and `npx wrangler login` once.

To keep the phone current while an agent works and you're away, run `storian publish --install`
once per project. A macOS background job then republishes about two minutes after each change
settles, survives restarts, and logs to `.publish/watch.log`. It runs outside the agent's
sandbox, so Codex or Claude Code don't need network access. The laptop must stay awake and
online. `storian publish --uninstall` stops it.

## Design

See [`docs/design.html`](docs/design.html) for the market survey (54 products) and the full
design, and [`docs/mobile.md`](docs/mobile.md) for Storian Cloud: the paid mobile and sync plan.
Roadmap: reference-film style learning → OTIO/FCPXML export to DaVinci Resolve → local
VLM first-pass labeling → music beat / VO timing.

## License

MIT
