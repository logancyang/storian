# Music: the playbook and `music.json`

Music is the film's second narrator. In this genre it sets the mood before a single word of VO, and
it decides the pacing as much as the cut does. Pick music from the story (theme, mood, the tempo
curve in `director.md` §3), not from what's popular, and give the human a few strong choices.

## 1. Start from the human's taste

The human may give reference tracks up front: files, YouTube or Spotify links, or just names.
Add each with `storian music add <file-or-url> --notes "what they like about it"`.
Local files are measured (tempo, loudness, brightness, an energy curve, a waveform).

Then describe each reference in catalog words, since that's how you'll search:

- **Genre or tradition**: ambient, neo-classical, lo-fi, post-rock, cinematic, city pop.
- **Instruments**: felt piano, pads, strings, nylon guitar, soft synth arps, field recordings.
- **Tempo and feel**: BPM, straight or swung, pulse or free.
- **Energy shape**: flat bed, slow build, build-and-release, a drop.
- **Density and vocals**: sparse or busy, instrumental or wordless vocals or lyrics.

With no references, derive the same description from `sequence.json` (music, mood, the acts)
and say that you did.

## 2. Write a cue sheet

A cue is one piece of music covering one or more acts. A 7–15 minute film usually has 3–6 cues.
For each cue, decide:

- **Mood and job**: what it must make the viewer feel, and how it hands over to the next cue.
- **Tempo**: a BPM range. The beat sets the cutting grid: at 80 BPM a beat is 0.75 s, so cuts on
  2 and 4 beats land at 1.5 s and 3 s. Montages sit around 100–125 BPM, reflective chapters
  60–80 BPM or free time. Match the act's average shot length to the grid.
- **Energy**: flat, building, or build-and-release, and where the peak should land.
- **Under VO**: sparse, no lead melody or lyrics in the voice's register, so the words stay clear.
- **Length**: `storian music` prints the seconds of picture each cue covers. A track can be
  looped, cut at a phrase, or faded, but it should be at least 70% of the cue's length.
- **Hit points**: shots that should land on a beat or a change (a chapter title, the turn, the
  last shot). Name them by shot id.
- **Transitions**: a hard cut on a hit, a crossfade under nat sound, or silence before the turn.

## 3. Find candidates

Give each cue **three candidates with clearly different takes**: the safe one, the bold one, and
one that reframes the scene. A list of near-identical tracks doesn't help anyone choose.

Where to search, in order of preference:

1. **The human's paid catalog through its MCP server**, if connected:
   - **Epidemic Sound** (official, beta): searches by mood, BPM, genre or a reference track, and
     can cut a track to length. Search is free; using the music needs a subscription.
   - **Artlist**: check which tools its MCP exposes before relying on catalog search.
   Store each result's preview URL and landing page. If a preview needs a login to play, say so
   in `why` and link the landing page.
2. **Free Creative Commons music, built in**: `storian music search "piano ambient" --save`
   searches ccMixter by tag (instrumental, CC BY only by default). `--provider openverse` searches
   Jamendo through Openverse, which works but is heavily rate-limited. Tags work best one word
   each: genre, mood, instrument.

After writing the cue sheet, run `storian music fetch`. It caches each shortlisted candidate as a
small local preview (AAC 96 kb/s, about 2–3 MB a track) in `music/previews/`, measures it, and
the storyboard plays it from there. Tell the human how many tracks and megabytes it downloads
before running it. ccMixter only serves files to its own pages, so its tracks play only once
fetched. `storian music analyze` measures anything else: references, or tracks a catalog lets
you stream. Both record tempo, an energy curve and a waveform, so you can check that a "slow
build" track actually builds and that the BPM fits the cue. You can't listen; the numbers and the tags are your ears.
Prefer tracks whose energy curve matches the cue's shape.

## 4. Licences: what's safe for a monetised YouTube film

| Source / licence | OK? | What it takes |
|---|---|---|
| Epidemic Sound, Artlist (subscription) | yes | an active plan, and the channel registered with the service so Content ID claims are cleared |
| CC BY, CC0, public domain | yes | for CC BY, credit in the description (the track's `attribution` field) |
| CC BY-SA | no by default | syncing music to picture makes an adapted work, so the whole film would have to be BY-SA |
| CC BY-ND | no | CC 4.0 counts music synced to moving images as adapted material, which ND forbids |
| CC BY-NC | no | the channel is monetised |
| Commercial songs (Spotify, YouTube) | no | references only, never in the film |

Set `youtube_ok` on every track. Never make a `youtube_ok: false` track a cue's `chosen`.

## 5. `music.json`

```json
{
  "direction": "One paragraph: the overall sound of the film and how it moves across the acts.",
  "references": [
    {"id": "ref1", "title": "Nuvole Bianche", "source": "user", "url": "https://…", "file": "refs/nuvole.mp3",
     "notes": "the human loves how sparse it is", "describe": "neo-classical solo piano, ~70 bpm, slow build",
     "analysis": {"bpm": 70.2, "loudness_db": -21.3, "brightness_hz": 1450, "dynamic_range_db": 18.0, "energy": [], "peaks": []}}
  ],
  "cues": [
    {"id": "m1", "acts": [0], "title": "Cold open", "mood": "suspended, then a jolt", "tempo": "free → 120 bpm",
     "energy": "near silence, one hit on s002", "instruments": "felt piano, sub hit", "vo": true,
     "hit_points": [{"shot": "s002", "what": "smash cut lands on the downbeat"}],
     "candidates": [{"track": "ccmixter:2905", "why": "sparse piano that leaves room for the first VO line"}],
     "chosen": "ccmixter:2905", "start": 12.0}
  ],
  "tracks": [
    {"id": "ccmixter:2905", "title": "…", "artist": "…", "source": "ccmixter", "url": "landing page",
     "preview": "https://…mp3", "duration": 203, "bpm": 72, "license": "CC Attribution", "youtube_ok": true,
     "attribution": "credit line", "tags": ["piano", "ambient"]}
  ]
}
```

- `acts` are 0-based indexes into `sequence.json` acts. Every act should be scored by exactly
  one cue, or be marked silent in `direction`.
- `start` is optional: the point in the track (in seconds) where the cue begins.
- The storyboard's Music tab plays everything here. The animatic plays each act's chosen
  track under the picture, so the human can judge the music against the cut.
- Leave `chosen` empty until you have a recommendation. Record the human's pick when they make
  one, and say which you recommend and why in the candidate's `why`.
