# The storian director's playbook

Read this before writing `story.json` or `sequence.json`. It is the taste storian encodes:
how a cinematic travel / lifestyle film on YouTube is structured, paced and cut.
Rules are defaults, not law; break one only on purpose and say why in the shot's `why`.

---

## 1. Story first, footage second

1. **Find the controlling idea.** One sentence that says what the film is *about*, not what
   it *shows*. "Hong Kong trip" is a topic. "A city that never stops moving teaches me to stand
   still" is an idea. Every act and almost every shot should serve it.
2. **Pick a motif.** A recurring visual (water, windows, trams, hands, light through glass,
   reflections, stairs) that appears at the open, returns in the middle, and pays off at the
   end. The motif is how a film without plot still feels designed.
3. **Theme + mood are different.** Theme = the idea (belonging, solitude, time, home).
   Mood = the felt texture (melancholic, warm, restless, dreamy, euphoric). State both.
4. **An arc even without plot.** Use *change*: from outsider to insider, day to night, noise to
   quiet, alone to together, curiosity to understanding. Order footage by the arc, not by the
   camera clock. Chronology is a fallback, never a default.
5. **When there's no script**, propose 3 treatments with clearly different moods built only from
   footage that exists (check the digest: a "foodie euphoria" treatment needs food shots). Each
   gets: title, logline, theme, mood, central idea, motif, arc (acts), music direction, and
   2–3 sample VO lines. Let the human pick. Then write the VO outline for the chosen one.
6. **When there is a script or idea paragraph**, expand it into act-level VO beats, then cast
   footage to the beats. If the footage can't support a beat, say so and suggest a replacement.

## 2. Structure of a ~15 min cinematic YouTube film

Defaults for a 15 min film; scale proportionally for other targets.

| Act | Share | Purpose | Picture | Sound |
|---|---|---|---|---|
| Cold open / hook | 0:00–0:45 | Make a promise. The single most striking images + one line that raises a question. | 6–12 fast hero shots, often out of chronology (flash-forward) | music hit or nat-sound burst, 1 VO line |
| Title / arrival | ~1 min | Orient: where are we, who am I, why here. | establishing EWS → WS → detail; travel shots (plane window, train, walking out of a station) | VO introduces the question |
| Acts of exploration (2–4 chapters) | 2–3.5 min each | Each chapter = one place/idea, ends on a small turn. | scene sequences (see §4), alternating VO and breathing room | VO ~50–60% of runtime, rest music/nat sound |
| Turn / reflection | 1.5–2 min | The emotional centre; slower, the motif returns. | longer holds, portraits, tele compression, silhouettes | VO sparse, music carries |
| Resolution / closer | 1–1.5 min | Answer the hook's question; echo the opening image (bookend). | callback to first shots, wide pull-outs, golden/blue hour | final VO line, music resolves, end on picture |

- Chapter breaks need a **reset**: title card or a strong wide + 2–4 s of silence or a music change.
- Put the best shot of each chapter in its first 20 s or its last 10 s.
- Give the audience a "breath" every 45–90 s: 4–8 s with no VO, often a wide or a sound moment.

## 3. Pacing and shot length

- **Average shot length (ASL) 2.5–3.5 s overall.** Hook 1–2 s, B-roll montage 1.2–2.5 s,
  VO-backed scenes 2.5–4 s, reflective holds 4–7 s. >8 s only for a deliberate hold (mark
  `role: "hold"`).
- **Cut on the beat for montages**, but not every cut on every beat. Vary: 2-2-1-1-4 feels alive,
  2-2-2-2-2 feels like a slideshow.
- **Static shots read shorter, moving shots need room**: a pan or walk needs to resolve
  (start and end on something) or be cut mid-motion on purpose to another moving shot.
- **Information density sets duration**: a crowded street needs 3 s to read, a texture insert
  needs 1 s. Exit a shot the moment it has given its information.
- **Tempo curve**: fast hook → medium arrival → alternate medium/slow chapters, each ending a
  little faster → slowest at the turn → medium-slow resolution. Never three equally paced
  minutes in a row.
- Retention: cut anything that repeats information. If two shots say the same thing, keep the
  better one. Viewers forgive short; they leave long.

## 4. Building a scene sequence

The atomic unit is a 4–8 shot **sequence** about one moment (arriving at the Peak, ordering
dim sum). Inside it:

1. **Vary shot size by at least two steps per cut** (WS → CU, not WS → MWS). Same-size cuts
   look like mistakes.
2. **Vary focal length / perspective.** Wide (context, energy, immersion) ↔ tele (compression,
   intimacy, isolation). A wide-then-tele pair of the same subject is the most cinematic
   cheap trick there is.
3. **Classic five-shot pattern**: wide (where) → medium (who) → close-up (what they do: hands)
   → close-up (face/reaction or the object) → over-shoulder / POV / unusual angle → back out.
4. **Establish, then go in, then release**: start wide or with a strong detail (mystery
   opener), go tight for the emotional beat, end on a wide or a movement that leads out.
5. **Detail inserts** (hands, textures, steam, signage, feet on stairs) are the glue of travel
   films. Cut them between wider shots to compress time and hide continuity breaks.
6. **Don't cross the line** within a scene: keep screen direction (a subject walking left→right
   keeps doing so) unless a neutral shot (head-on, overhead, insert) resets it.
7. **One idea per shot.** If the label summary needs "and", the shot may be two shots — use
   the moment that carries the idea.

## 5. The cut itself

Mark every cut with `cut` (how this shot enters). Prefer motivated cuts:

- **match-on-action**: cut during a movement, continuing it in the next shot (hand reaches →
  CU hand grabs). Cut ~2–4 frames into the motion. Best with `match_action` labels.
- **cut-on-motion**: cut during camera or subject motion, next shot moves in the same direction
  (pan right → walk right). Hides the cut, builds flow.
- **graphic-match**: shape/colour/position matches across shots (round lantern → round moon;
  vertical tower → vertical tram pole). Great for transitions between places or chapters.
- **whip / masked**: a fast pan or an object crossing lens ends one shot and starts the next.
- **J-cut / L-cut**: sound of the next scene starts before the picture (J) or the last scene's
  sound carries over (L). Default for chapter transitions and VO starts.
- **smash-cut**: abrupt contrast (quiet room → loud market) for energy or humour.
- **hard cut**: fine for content cuts inside a sequence when size/focal change is large.
- **dissolve**: time passing only; use rarely (≤3 per film).

Avoid: jump cuts on the same framing (unless stylistic and repeated ≥3 times), cutting a
pan mid-way to a static shot, cutting from a moving shot that hasn't "landed" to a static
shot of the same subject, two consecutive shots from the same clip without a size change.

## 6. VO and B-roll

- **VO sections**: the picture illustrates *around* the words, not literally. If VO says "I felt
  small", don't show "a small thing" — show a vast EWS with a tiny figure. Avoid word-picture
  redundancy ("we ate dumplings" over dumplings) except for a deliberate punch.
- **Pause the VO** for: hero shots, sound moments (tram bell, sizzling wok, rain), chapter
  starts, and the turn. Mark these shots `role: "broll"` or `"natsound"`.
- **Shots under VO** should be calmer (static, slow moves, longer) so the viewer can listen.
  Busy, fast montages go in the VO gaps.
- A VO line usually spans 2–4 shots. Start a VO line on a cut, end it a beat before a cut.
- Ratio for this genre: ~55% VO / 45% music + nat sound.

## 7. Choosing between takes

Score candidates in this order: (1) does it serve the idea of the current beat, (2) emotion /
human presence, (3) composition and light, (4) clean motion (no jerky pan, no focus hunt),
(5) technical sharpness. A slightly soft shot with a real human moment beats a sharp empty one.
Use each footage range once. Prefer the hero shots (`quality` 5) at the hook, chapter openers,
the turn and the closer — don't spend them all in the first minute.

## 8. Opening and ending patterns that work

- **Opening**: (a) in medias res sensory burst; (b) a single long-held mysterious detail that
  pulls out to reveal the place; (c) travel-in (window, train, walking out of a tunnel into light)
  with the first VO line over black or over the first frame.
- **Ending**: (a) bookend: echo the first image at a different time of day; (b) pull-out / rising
  wide that releases the viewer; (c) the motif in its final form; (d) walk-away from camera.
  Last shot ≥4 s, let the music resolve.

## 9. Writing the sequence

- Write `sequence.json` per `knowledge/sequence_schema.md`. Every shot gets a `why` that a
  human editor would accept: what it does for the story *and* why it follows the previous shot.
- After writing, run `storian check` and fix every error; address warnings or justify them.
- Then `storian previews` so the storyboard can play the animatic.
- When the human asks for changes, edit the JSON surgically (swap a shot, retime, move a
  chapter) and re-run `check` + `previews`. Never regenerate the whole film for a local change.

## 10. Reviewing coverage

The same rules work in reverse: a scene that can't be cut by §4 and §5 is missing shots.
After the sequence exists, review the footage as a director reviews dailies and tell the
videographer what to go and get. See `knowledge/coverage.md`.
