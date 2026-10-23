# Mood first

Settle the mood and theme with the human before anything else is designed. They decide the
music (tempo, key, instruments, how much space) and the shots (lens, distance, how long a
shot holds, where the person stands, the light). Two films made from the same footage feel
different mostly because of these choices.

- **Mood** is the felt texture: nostalgic, melancholy, restless, warm, euphoric, dreamy.
- **Theme** is the idea under it: time passing, belonging, solitude, home.

Ask the human for both in their own words. If they give one sentence ("nostalgia and
reflection on life, a little melancholy"), keep their words as the mood and offer a theme.
Everything after this step (treatments, sequence, music cues, coverage shot list) works inside
the mood. Treatments become different angles on it, not different moods.

## mood.json

```json
{
  "mood": "Nostalgic and reflective, a little melancholy",
  "theme": "Every moment is already becoming a memory",
  "feel": "Two or three sentences a beginner can picture: what the viewer should feel, and how.",
  "shots": ["long static holds: let people walk out of frame", "a small figure in a big wide frame", "..."],
  "avoid": ["whip pans and speed ramps", "..."],
  "music": "Slow felt piano or strings, 60–80 bpm, minor key, lots of space between notes.",
  "beats": [
    {"id": "arrive", "name": "Arriving", "what": "first light on a new place, the outsider's eye", "target": 3}
  ],
  "cities": [
    {"name": "Kyoto", "note": "One line: what this city gives the film.",
     "spots": [
       {"name": "Fushimi Inari, upper gates", "area": "Fushimi", "when": "Dawn, before 7:00",
        "scene": "The model climbs alone through the gates; wide from below, medium through the gates, hands on a gate, the empty path after.",
        "why": "Repetition and an empty path read as memory.", "tip": "Crowds by 8:30. Small tripods only.",
        "beat": "arrive", "place": "temple", "map": "Fushimi Inari Taisha"}
     ]}
  ],
  "light": [{"name": "Golden hour", "tip": "Shoot into the sun, the model as a silhouette."}],
  "kit": [{"name": "Sigma 56mm f/1.4", "use": "Your longest: closes, details, faces."}],
  "arrive": ["Walk the place once with the camera in the bag: light, background, where people move.", "..."],
  "places": [
    {"id": "street", "name": "Street", "intro": "One line on how this mood plays in this kind of place.",
     "shots": [
       {"name": "The street from above", "how": "Find stairs or a footbridge. Widest lens, hold 10 s while people pass.",
        "height": "high", "size": "EWS", "subject": "none", "secs": 10,
        "sketch": "<path d='M0 70 L160 60'/><use href='#p' transform='translate(80 68) scale(.4)'/>"}
     ]}
  ]
}
```

- `shots` / `avoid`: 5–7 short lines each, concrete enough to act on at a location.
- `arrive`: the first 10 minutes at any new place, 5–6 steps: look before shooting, choose the
  light, one wide that says where/who/when, cover one action at every size (远 全 中 近 特, cut
  全 中 特 中, each take continuing the last one's action), change the angle rather than the
  subject, and one move plus 30 s of sound before leaving.
- `beats`: 4–6 stretches of feeling the film needs even without a script (for nostalgia:
  arriving, the rush, quiet corners, looking back, leaving). `target` is how many complete
  scenes the bank should hold for that beat (default 3). Scenes and spots point at a beat by id.
- `cities`: for a trip, 6–8 `spots` per city where a whole scene in this mood is likely. `when`
  is the best time of day (be specific: "blue hour, about 17:20 in November"). `scene` is the
  scene to come home with: place, light and an action, covered at several sizes. `tip` covers
  crowds and rules (filming bans, tripods, private lanes). `place` links to the matching recipe,
  `map` is the search text for the map link. Check opening hours and rules on the web when you can.
- `light`: one tip per light the human may meet (golden hour, blue hour, midday, night, overcast).
- `places`: 6–8 kinds of place the trip will have (street, waterfront, market, temple, café,
  viewpoint, transit). Each gets 7–9 shots **in shooting order**: one wide establishing shot,
  a medium, details, the person moving through (back to camera, over the shoulder, in and out
  of frame), one moving shot, and one hero shot that carries the mood. The second shot is
  always "One action, four sizes": one action typical of the place, repeated at wide, medium,
  close and detail, so the edit can cut on the action. Every shot follows the
  mood: a melancholy street recipe and a euphoric one share almost nothing.
- Shot fields: `how` is one sentence on where to stand, which lens, how long to hold.
  `height` is `low`, `eye`, `high` or `overhead`. `size` uses the label sizes (EWS, WS, MWS,
  MS, MCU, CU, ECU, insert). `subject` is `none`, `unrecognizable` (a stand-in or a back is
  fine) or `talent` (needs the model).
- `kit`: the human's camera and lenses, one line each on what to use it for and the one setting
  that matters for this trip (an ND filter for log in daylight, stabilisation for walking shots).
  When there's a kit, every shot names its lens in `lens` (a `kit` name), and `how` says "the
  56mm" rather than "the longest lens". Use the same names in coverage.json shots.

## Sketches

Each shot has a `sketch`: a few pencil lines showing the frame. It's SVG markup inside a
160×90 frame (y grows down), drawn as thin pale lines. Keep it to 3–8 elements: the horizon
or the main lines of the place, and where the person stands and how big they are.

- Lines: `<path d='…'/>`, `<line …/>`, `<rect …/>`, `<circle …/>`. No fill, no text.
- A person: `<use href='#p' transform='translate(x y) scale(s)'/>`, standing with feet at (x, y).
  At scale 1 the figure is 40 units tall (close to half the frame height); scale .3 is
  a small figure in a wide shot, scale 2 is a medium shot cut at the waist.
- `class='a'` draws that element in the accent colour: use it for the person or the one
  thing the shot is about. `class='f'` draws faint lines for background or out-of-focus areas.
- Use single quotes for attributes so the JSON stays readable.
