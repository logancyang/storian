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

Read `story.json` (the chosen treatment) and `sequence.json`, then list what the *story* asks
for that the footage doesn't have:

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

## 3. How to write a need

Every need is one shot a videographer could execute without asking a question:

- `shot`: subject + action + framing, concretely. Write "Tele CU of the deckhand throwing the
  rope as the ferry docks", not "more close-ups".
- `size`, `focal`, `angle`, `move`: use the label vocabularies. Translate `focal` into the
  owner's actual lenses, which are listed in `clips.json`. Example: "tele means your 18-135 at
  100–135 mm; the 17-40 can't compress."
- `secs`: how long to roll. Default ≥10 s with 3 s handles. For actions, two takes.
- `where`: `on-location` (must go back) or `anywhere` (a pickup shot at home or any city:
  hands, coffee, a notebook, packing, a phone map, window light, room tone).
  Mark pickups honestly. They are the cheapest gaps to close, and they belong in `pickups`.
- `priority`: 1 means the film is weaker without it (a core scene or a story beat). 2 means the
  scene can't be cut properly without it. 3 is nice to have.
- `why`: the edit it unlocks ("lets act 3 cut on action instead of jump-cutting two mediums").

Don't list a gap the story doesn't need. A two-clip transit scene that only serves as a cutaway
needs nothing. A minor scene the film doesn't use is either dropped or flagged "worth a full
sequence if you go back", not given ten needs.

## 4. `coverage.json`

```json
{
  "summary": "Two to four sentences: the overall verdict, the biggest film-level gap, and the one shoot day that would fix most of it.",
  "scenes": [
    {
      "id": "sc03",
      "name": "Harbour railing, late morning",
      "clips": ["C5447", "C5448"],
      "importance": "core",
      "verdict": "Seven mediums of the skyline from the same railing. Lovely light, but nothing to cut to: no wide, no person, no detail.",
      "needs": [
        {"shot": "Tele CU of her hands on the railing, skyline soft behind", "size": "CU", "focal": "tele",
         "angle": "eye", "move": "static", "secs": 10, "where": "on-location", "priority": 1,
         "why": "gives the arrival a human beat and a close to cut against the wide skyline"}
      ]
    }
  ],
  "pickups": [
    {"shot": "ECU of a hand turning a page in a notebook, window light", "size": "ECU", "focal": "normal",
     "angle": "high", "move": "static", "secs": 12, "where": "anywhere", "priority": 2,
     "why": "a recurring 'writing it down' insert gives the VO a home and bridges chapters"}
  ],
  "film": ["Film-level gaps in one sentence each, e.g. 'No golden-hour light in the whole library: the warm end of the palette is missing.'"]
}
```

- `scenes`: start from `storian coverage --scaffold`, which writes the auto scenes. You may
  rename, merge or split them by editing `clips`. Every clip belongs to at most one scene.
  Keep ids stable once the human has seen them.
- Scenes you list with `needs: []` are reviewed as covered. Write them a verdict anyway.
- `importance`: `core` | `support` | `minor`. It overrides the automatic guess.
- The storyboard shows this file at the top, as "What to shoot next", above the sequence.

## 5. After new footage arrives

Re-run `scan`, `frames`, label the new clips, then `storian coverage`. Remove the needs the
new clips satisfy, and mention which clip satisfied each one in the scene's verdict. Then re-cut the
affected acts.
