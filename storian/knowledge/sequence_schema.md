# story.json and sequence.json

## story.json — treatments (written before the sequence)

```json
{
  "footage_summary": "2-4 sentences: what the footage actually contains (places, times of day, people, standout shots).",
  "options": [
    {
      "title": "Example Film",
      "logline": "One sentence pitch.",
      "theme": "Stillness inside motion",
      "mood": "contemplative, melancholic, warm at the end",
      "central_idea": "Short paragraph: what the film is about and why it matters to the viewer.",
      "motif": "Water and glass: harbour, reflections, rain on windows",
      "arc": ["Hook: ...", "Arrival: ...", "Chapter 1: ...", "Turn: ...", "Resolution: ..."],
      "music": "Sparse piano + ambient pads, builds to strings in the turn",
      "sample_vo": ["Line one.", "Line two."],
      "footage_fit": "Why the footage supports this treatment; what's thin."
    }
  ],
  "chosen": 0,
  "human_notes": "Anything the human said when choosing."
}
```

## sequence.json — the storyboard

```json
{
  "title": "Example Film",
  "logline": "...",
  "theme": "...",
  "mood": "...",
  "central_idea": "Short paragraph shown at the top of the storyboard.",
  "motif": "...",
  "target_minutes": 15,
  "music": "overall music direction",
  "style_notes": "pacing / grading / look notes for the editor",
  "acts": [
    {
      "id": "a1",
      "title": "Cold open",
      "purpose": "What this act does in the story",
      "vo": "Full VO draft for this act (optional, may be empty for music-only acts)",
      "music": "music cue for this act",
      "shots": [
        {
          "id": "s001",
          "clip": "C5600",
          "in": 12.0,
          "out": 14.5,
          "role": "broll",
          "vo_line": null,
          "cut": "hard",
          "why": "Director note: what the shot does and why it follows the previous one."
        }
      ]
    }
  ]
}
```

- `in`/`out`: seconds from clip start (floats). Stay inside a labeled moment when possible.
- `role`: `vo` (under voiceover), `broll` (music / no VO), `natsound` (let the clip's own sound
  play), `hook`, `hold` (deliberately long), `title` (title card goes over this shot).
- `vo_line`: the VO words that start on this shot (null if none). Lines may span several shots.
- `cut`: how this shot enters — `match-on-action` `cut-on-motion` `graphic-match` `whip` `J-cut`
  `L-cut` `smash-cut` `hard` `dissolve` `fade-in`.
- Shot ids are unique and stable; keep them when reordering so the human can refer to them.
