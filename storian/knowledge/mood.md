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
  "light": [{"name": "Golden hour", "tip": "Shoot into the sun, the model as a silhouette."}],
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
