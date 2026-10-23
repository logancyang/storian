# Coverage review: what to shoot next

Read this before writing `coverage.json`. Here the agent works as the director reviewing the dailies.
The question is not "what can I cut from this?" but "what is missing that would make this cut properly?",
and the answer is a shot list the videographer can take out on the street.

`storian coverage` does the counting. It groups clips into scenes, counts what each scene has
(shot sizes, focal feel, angles, movement, people, entries and exits), and applies the rules
below to suggest gaps. Your job is the judgement those rules can't make: which gaps matter for
*this* story, and exactly which shot fixes each one.

## 1. What a covered scene has

A scene is one place and one moment (the ferry crossing, ordering at the diner). An editor can
cut it properly when it has:

1. **The size ladder**: a wide (where), a medium (who and what), a close-up (faces, hands at
   work), and 2–3 detail inserts (texture, signage, an object in use). The cut needs two-step
   size changes, so a scene with only WS and MWS can't be cut without jumps.
2. **Two perspectives on the same subject**: wide lens close to it (immersion, energy) *and*
   tele from far back (compression, isolation, shallow depth). The tele shot is the one most
   often missing from travel footage, and it's the one that makes footage look cinematic.
3. **The five shots**: hands, face, wide, over-the-shoulder or POV, an unusual angle (high, low,
   overhead, through something). If a scene has three of the five, it can be cut; with five,
   it has choices.
4. **Action covered twice**: every repeatable action (pouring tea, tapping the Octopus card,
   the tram bell, a door) filmed wide *and* tight. Do it twice so the editor can cut on the action.
   This is what `match_action` needs to exist.
5. **A way in and a way out**: an entry (walk into frame, a door opening, arriving on the
   escalator) and an exit (walk out of frame, a vehicle pulling away, a pan off to the sky).
   Without them, every scene starts and ends on a hard cut.
6. **A still frame and a moving frame**: a locked-off frame of at least 6 s to sit VO and holds on,
   and one move (push-in, walk-follow, a tracking shot from a vehicle) for energy.
7. **A person**: someone reacting to the place. A place with no human on screen reads as a postcard.
8. **A hero frame**: one image strong enough to open or close a chapter.
9. **Clean handles**: 3 s of steady frame before and after the action. Many cuts fail only
   because the take starts on the action or ends while the camera is still moving.

## 2. What the story needs, beyond the checklist

Read `mood.json`, `story.json` (the chosen treatment) and `sequence.json`, then list what the
*story* asks for that the footage doesn't have. Shoot every need in the mood's shot language
(`mood.json:shots`, and nothing from `avoid`):

- **Motif shots**: the motif needs to appear at the open, in the middle, and in its final form
  at the end. Count the motif's usable shots per act.
- **Bookends**: the closer echoes the opener (the same framing at a different time of day,
  or the same subject from the opposite side). Check that the matching shot exists.
- **The turn**: the emotional centre needs portraits and long holds: a face at a window, a tele
  close-up, a silhouette.
- **VO beats illustrated loosely**: shots the sequence used as stand-ins because nothing
  better existed. Look for weak `why`s, reused clips, and quality-3 shots in key positions.
- **Runtime**: if the footage supports fewer minutes than the target, say how many more usable
  minutes are needed and which scenes would carry them. Fill the gap with new scenes or deeper
  coverage of strong ones, never with filler.
- **Transitions between chapters**: graphic-match pairs, whip pans, objects crossing the lens.
  These rarely happen by accident.

## 3. The scene bank

During a trip there's no script yet, so the goal is a bank of complete scenes for each beat
of the mood (`mood.json:beats`). Give every scene in `coverage.json` a `beat` and a `grade`:

- `complete`: one place, one light, one outfit, covered wide, medium and something tight around
  an action, and it fits the mood. It could carry a stretch of the film on its own.
- `partial`: good material but a size or the action is missing.
- `fragment`: a cutaway at best.

`storian coverage` proposes a grade from the counts; override it with your judgement (a
technically complete scene in the wrong mood is partial at best). The Shot list tab shows the
bank per beat against each beat's target, then the next shots.

## 4. Don't try to finish old scenes

A scene can't be completed days later. The light, the weather and the outfits won't match, so
a shot planned "for scene 12" almost never gets used. Plan **one shot list for the whole film**
instead: a mix of shots the human can get on any day, anywhere with a similar place, each
saying where it goes in the film. Think in what the story needs, not what a scene lacks:

- **The images the story is built on** and doesn't have yet: the thesis shot, the motif in the
  acts where it's missing, the bookends, a face for the turn, a way to end.
- **Connective tissue**: transitions between chapters (doors closing, something arriving,
  a sign going soft), a home for the voiceover (writing, a window), wild sound for every place.
- **Texture the edit keeps reaching for**: details, compression, one action covered at every
  size (远 全 中 近 特, cut 全 中 特 中, each take continuing the last one's action).

Default to shots nobody recognisable has to be in. `subject: "none"` first, then
`"unrecognizable"` (a back, a silhouette, far away on a long lens: a stand-in works), then
`"talent"` with a `fallback`. Every shot follows the mood (`mood.json:shots`, nothing from `avoid`).

Keep the list short: 15–25 shots, 5–8 of them priority 1. More is a sign of patching scenes.

During a trip, the list targets the bank's gaps: beats short of complete scenes, and kinds
of scene that are only partial so far. Point `for` at the beat ("Looking back · no complete
scene yet") and tie shots to the next city's spots when they fit.

## 5. How to write a shot

Every shot is one thing a videographer can do without asking a question, in the same format as
the Plan tab's recipes (see `storian knowledge mood`), plus where it goes and why:

- `name`: a few words ("Still in the rush").
- `for`: where it goes in the film ("Act 3 ending · the thesis shot", "Transitions between chapters").
- `how`: one or two sentences: where to stand, which lens, what happens, how long to hold.
  Translate lenses into the owner’s real ones from `mood.json:kit`, or `clips.json` when there is no kit ("tele means your 18-135 at 100–135 mm").
- `height` (`low`, `eye`, `high`, `overhead`), `size` (label sizes), `secs`, `subject`, and
  optionally `focal` and `move` in the label vocabularies.
- `priority`: 1 means the story is weaker without it; 2 it makes the edit easier; 3 nice to have.
- `why`: what it unlocks in the edit.
- `fallback` (talent only): the best version without the model.
- `sketch`: a few pencil lines of the frame (same format as mood.json).

## 6. `coverage.json`

```json
{
  "summary": "Two to four sentences: the overall verdict and the images the story still needs.",
  "scenes": [
    {"id": "sc03", "name": "Harbour railing, late morning", "clips": ["C5447", "C5448"], "importance": "core",
     "wardrobe": "him: light jacket, black backpack",
     "grade": "partial", "beat": "arrive",
     "verdict": "Seven mediums of the skyline from the same railing. Lovely light, nothing to cut to."}
  ],
  "shots": [
    {"name": "Still water, close", "for": "Acts 4–5 · the motif mid-film",
     "how": "A cup of tea, a puddle or a fountain. Longest lens; wait until the surface settles, then hold 15 s.",
     "height": "eye", "size": "ECU", "subject": "none", "secs": 15, "priority": 1,
     "why": "Water opens and closes the film but almost vanishes in the middle.",
     "sketch": "<path d='M40 40 Q80 30 120 40 Q80 50 40 40 Z'/>"}
  ]
}
```

- `scenes`: start from `storian coverage --scaffold`, which writes the auto scenes. Rename,
  merge or split them by editing `clips`; every clip belongs to at most one scene. Scenes feed
  the coverage matrix (usable clips per size, lens, angle) and tell you what the footage is
  thin on. They don't get shots of their own.
- `importance`: `core` | `support` | `minor`. It overrides the automatic guess.
- Set the timezone with `storian init … --timezone Asia/Hong_Kong` so scene times are local.

## 7. After new footage arrives

Re-run `scan`, `frames`, label the new clips, then `storian coverage`. Put the new clips into
scenes, grade them and give them beats. Remove the shots the new clips satisfy and say which
clip did it, then write the next list. In phase 2, re-cut the affected acts.
