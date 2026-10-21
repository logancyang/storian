# Clip label schema (`labels/<clip>.json`)

One file per clip, written by the labeling agent after viewing the clip's contact sheet
(`sheets/<clip>.jpg`, frames with timestamps) and, when needed, individual keyframes in
`frames/<clip>/t<seconds>.jpg` (about 1 per second). The thumbnails are a quick
S-Log3 → Rec.709 conversion, not a grade: judge exposure loosely and never mark a clip low
quality only because it looks flat or blue.

Use the `motion` hint from `storian label todo` (`camera_hint`, `activity`), but trust your
eyes over it.

```json
{
  "clip": "C5430",
  "summary": "Blue-hour view over Victoria Harbour from a hotel balcony, Kowloon side, glass facade framing the right edge.",
  "location": "Victoria Harbour, Tsim Sha Tsui waterfront",
  "time_of_day": "blue-hour",
  "subjects": ["harbour", "Hong Kong Island skyline", "ferry"],
  "action": "a ferry drifts left to right across the harbour; water ripples",
  "shot_size": "EWS",
  "focal_feel": "wide",
  "angle": "high",
  "camera_move": "static",
  "composition": "frame-within-frame, building edge on the right third, horizon on the upper third",
  "light": "soft cool ambient, city lights just coming on",
  "mood": ["calm", "anticipation"],
  "story_role": ["establishing", "opener"],
  "audio": "ambient",
  "quality": 4,
  "issues": [],
  "moments": [
    {"in": 2.0, "out": 7.0, "score": 4, "desc": "ferry enters right third", "match_action": "left-to-right drift"}
  ],
  "tags": ["skyline", "water", "hotel-view"]
}
```

## Field vocabulary

- `time_of_day`: `dawn` `day` `golden-hour` `blue-hour` `night` `interior`
- `shot_size`: `EWS` (vast, tiny people) `WS` (full scene, whole body) `MWS` (knees up / small group)
  `MS` (waist up / one subject dominates) `MCU` (chest up) `CU` (face / single object fills)
  `ECU` (detail: eyes, hands, texture), `insert` for a cutaway object detail
- `focal_feel`: what the image looks like, not the lens dial: `ultra-wide` (<20mm-look, stretched edges)
  `wide` (24-35) `normal` (40-60) `tele` (85+, compressed background, shallow depth)
- `angle`: `eye` `high` `low` `overhead` `dutch` `pov` `over-shoulder`
- `camera_move`: `static` `handheld-still` `pan-left` `pan-right` `tilt-up` `tilt-down` `push-in`
  `pull-out` `tracking` `walk-follow` `walk-lead` `orbit` `crane` `vehicle` `timelapse` `hyperlapse`
- `story_role` (any): `hook` `opener` `establishing` `transition` `detail` `action` `reaction`
  `portrait` `atmosphere` `food` `travel` `climax` `closer` `b-roll-filler`
- `audio`: `ambient` `dialogue` `talking-to-camera` `music` `loud` `silent`
- `quality` 1-5: 5 = hero shot (striking composition, clean motion, sharp), 3 = solid coverage,
  1 = unusable (lens cap, accidental record, severe blur). Flat log look is not a defect.
- `issues`: `shaky` `soft-focus` `focus-hunt` `overexposed` `underexposed` `accidental` `obstructed`
  `tilted-horizon` `jerky-pan`

## Moments (the most important field)

`moments` are the usable sub-ranges an editor would actually cut in, in seconds from clip start.
For every clip list 1–4 moments, each 1.5–8 s long, best first. Skip the first ~0.5 s after
record start and any camera settling. For each moment:

- `in`/`out`: start and end in seconds (keyframes are ~1 s apart; pick from the sheet timestamps)
- `score` 1-5: how much an editor would want this exact range
- `desc`: what happens in it, concretely
- `match_action` (optional but valuable): the motion or graphic shape a cut could match:
  direction of movement ("walks left→right"), an action ("hand reaches for cup", "door closes"),
  or a shape ("round lantern centre frame", "strong vertical lines"). The sequencer uses this to
  build match cuts and cuts on motion.

Write valid JSON only. One file per clip. Do not invent things you cannot see.
