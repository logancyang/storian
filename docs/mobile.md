# Storian on mobile: design doc

Status: proposal · Owner: Logan Yang · Last updated: 2026-10-21

## Summary

Storian runs locally: the footage, the agent and the storyboard all live on the user's computer,
served at `http://localhost:7878`. This doc proposes **Storian Cloud**, a paid service that
puts the same storyboard, shot list and review flow on the user's phone or any browser.

The open-source CLI stays complete and free. People pay for convenience: their project on every
device, synced, shareable and usable on a shoot day. This is the Obsidian model (free app, paid
Sync and Publish). It also keeps the business separate from the code: nothing in the MIT repo is
held back or crippled.

Three decisions shape everything else:

1. **Raw footage never leaves the computer.** Only a small copy of the project is uploaded:
   JSON, resized frames, and low-resolution previews of the ranges in the cut. For the HK test
   project that's about 100 MB against 74.5 GB of footage.
2. **One web app, everywhere.** The localhost page becomes an installable web app (a PWA). The
   same code runs from the laptop for free and from the cloud for paying users. A native
   wrapper comes later, only if it earns its place.
3. **The phone sends requests; only the agent edits the project.** Phones and browsers never write
   `sequence.json` or `coverage.json`. They send small typed requests (a comment, a tick, a
   treatment choice) that the agent picks up. With one writer there are no sync conflicts,
   and the protocol survives moving the agent to the cloud later.

## Goals

- A paying user can open their project on a phone within a minute of deciding to, with one
  QR scan and no typed password.
- The shot list ("What to shoot next") works offline on location and syncs ticks back.
- Comments made on the phone reach the agent, and the agent's changes reach the phone, without the
  user copying anything between devices.
- A user can share a view-only storyboard with a client or collaborator.
- Running costs stay close to storage costs: the user's own agent does the AI work.

## Non-goals (for now)

- Uploading, storing or editing raw footage in the cloud.
- Running the agent on our servers (phase 3, priced separately).
- Editing the cut by drag-and-drop on the phone. The agent edits; the phone asks.
- Native iOS and Android apps at launch.
- Team workspaces and permissions beyond "owner" and "view-only link".

## Who it's for and what they do

The user is a solo or two-person creator who films travel or lifestyle footage and edits on a
laptop. Their phone moments are:

| Moment | Where | What they need |
|---|---|---|
| **Shoot day** | on the street, often offline | the shot list for nearby scenes: what to get, which lens, which angle, how long to roll. A tick-off box per shot. |
| **Review** | the couch, a train | the animatic, full screen, swipeable. A quick way to say "this drags" about a specific shot. |
| **Waiting on the agent** | anywhere | a notification when the re-cut is ready, opening on what changed. |
| **Showing someone** | a message to a client or friend | a link that plays the storyboard, with comments. |

## Experience

### First run

1. On the laptop: `storian login` opens the browser for sign-in (passkey, Apple or Google).
   The CLI uses the OAuth device flow, the same pattern as `gh auth login`.
2. `storian sync` uploads the project and prints a QR code and a short URL.
3. On the phone: scan the code. The project opens, already signed in for this device
   (the QR carries a one-time pairing code). The page offers "Add to Home Screen".

Nobody types a password on a phone. A free user who runs `storian sync` sees one clear screen:
what Pro adds, the price, and a Stripe checkout. Nothing breaks if they decline.

### Shoot mode

- **Layout:** the "What to shoot next" list, re-laid out for a phone. Scenes are grouped by
  place and sorted by priority. Each shot shows what to film, lens, angle, movement, how long
  to roll, and a frame of what already exists.
- **Offline:** the list, its frames and the user's ticks are cached on the device. Ticks made
  offline are queued and sent when the phone is back online.
- **Reference photo:** an optional photo per ticked shot ("I got it here"). It's stored with the tick.
- **Closing the loop:** after the user ingests new footage, the agent matches new clips to ticked
  shots, removes satisfied needs from `coverage.json`, and notes which clip satisfied each one.

### Review mode

- **Player:** a full-screen vertical player of the animatic. Swipe moves between shots; the act
  and shot id show at the top; the VO line shows as a subtitle.
- **Comments:** tap to comment on the current shot, by typing or with a voice note that's
  transcribed on upload. Comments are tied to a shot id and a time inside the shot.
- **Treatments:** pick or blend options from the Treatments tab.
- **Agent progress:** each comment shows its state: sent, picked up by the agent, done. The done
  state carries the agent's one-line reply ("swapped s047 for C5612, act 3 now 2:41").

### Notifications

Web push works for installed web apps on iOS 16.4+ and Android. A notification is sent when the
agent finishes a request or a re-cut, and tapping it opens on the changed shots. Notifications
are off until the user turns them on from a request they care about, never at first launch.

### Share links

The owner creates a view-only link per project, with an optional expiry. Viewers see the
storyboard and animatic, and they can comment if the owner allows it. Viewer comments go into
the same inbox, labelled with the viewer's name.

## Architecture

```
 Laptop (free, MIT)                          Storian Cloud (paid)              Phone / any browser
 ──────────────────                          ────────────────────              ───────────────────
 raw footage          ✗ never uploaded
 agent + storian CLI
 project files ──── storian sync ────▶  storage for files      ──── CDN ───▶  web app (PWA), offline
   (JSON, frames,     upload only          API + database                     cache, push
    previews)         new files            live channel per project ◀──────▶  live updates
 ◀── storian inbox ────────────────────  request log  ◀──────────────────────  comments, ticks, picks
```

### The uploaded copy of a project

`storian sync` builds a copy for the cloud from the project folder:

| Included | Prepared as |
|---|---|
| `project.json`, `story.json`, `sequence.json`, `coverage.json`, labels | as is, with local paths removed |
| `clips.json` | without `path` and any location metadata, only what the page shows |
| frames the page uses (shot strips, scene thumbnails) | WebP, 640 px wide |
| contact sheets | WebP, reduced, loaded only when opened |
| previews of the shots in the cut | H.264 540p, audio kept, web-optimized |

Raw footage, the LUT and full-resolution frames stay local. For HK, the copy is about 2 MB
of JSON, about 20 MB of frames and about 80 MB of previews.

### Sync protocol

**Files are named by their content.** Each file in the copy is identified by its SHA-256 hash.
A **manifest** lists the project's files for one version:

```json
{
  "schema_version": 1,
  "project": "prj_01JB…",
  "version": 42,
  "parent": 41,
  "created": "2026-10-21T09:12:00Z",
  "files": {
    "sequence.json": {"hash": "sha256:9f2c…", "size": 45012, "type": "application/json"},
    "previews/C5711_14.00_16.50.mp4": {"hash": "sha256:1ab0…", "size": 612344, "type": "video/mp4"}
  }
}
```

Each upload goes like this:

1. **Propose:** the CLI posts the manifest.
2. **Missing list:** the server replies with the hashes it doesn't have, each with a short-lived
   upload URL.
3. **Upload:** the CLI uploads only those files, straight to storage.
4. **Commit:** the CLI commits the version. A re-sync after a one-shot swap uploads one preview
   and one JSON file.

Versions are kept, so the web app can show "what changed since you last looked" by comparing
two manifests. Old versions expire after a set time, while the files they share stay.

**Requests: everything a phone does is one.** A request is an immutable record:

```json
{
  "id": "op_01JB…",
  "schema_version": 1,
  "project": "prj_01JB…",
  "at": "2026-10-21T10:03:11Z",
  "author": {"user": "usr_…", "device": "dev_…", "role": "owner"},
  "type": "comment",
  "target": {"shot": "s047", "t": 1.2},
  "payload": {"text": "drags, try something with motion"}
}
```

Request types in v1:

| type | target | payload |
|---|---|---|
| `comment` | shot id, scene id, act index, or none | text, optional audio and its transcript |
| `tick` / `untick` | scene id + need index, or pickup index | optional reference photo |
| `choose_treatment` | none | option index, optional blend note |
| `request` | none | free text to the agent ("make it 10 minutes") |
| `resolve` | the id of the request being answered | the agent's one-line reply, the manifest version it produced |

The agent is the only writer of the project's JSON:
- `storian sync` pulls new requests into `inbox.jsonl` in the project folder.
- `storian inbox` lists the open ones for the agent.
- `storian inbox done <id> --note "…"` sends a `resolve` request.

Ticks are a special case: the page reads tick state straight from the request log, so ticking
feels instant even when the agent isn't running.

Shot ids (`s047`) and scene ids (`sc12`) are already stable by convention (see `AGENTS.md`).
That convention becomes a hard rule, because requests refer to them.

**Live updates.** Each project has a live channel (websocket). Open pages get new versions and
requests pushed to them, replacing today's 2-second polling of `/api/version`. The localhost
server keeps polling, so the same page works in both places.

### Agent loop

- **Phase 1:** the user runs `storian sync` when they sit down at the laptop, and their agent
  reads the inbox.
- **Phase 2:** `storian sync --watch` runs in the background. When a request arrives, it runs the
  user's own agent headless with the inbox as the prompt (for example Claude Code's `claude -p`,
  or any agent through a configurable command), then re-syncs.

The user's agent and API key do the work; we pay only for storage and bandwidth.

### Accounts, devices and billing

- **Sign-in:** passkeys first, then Sign in with Apple or Google, then an email magic link. No
  passwords.
- **CLI:** OAuth 2.0 device authorization grant (RFC 8628). The token is stored in the OS keychain.
- **Phones:** paired by QR, which carries a one-time code. Each device is listed and revocable
  in account settings.
- **Billing:** Stripe Checkout and the Stripe customer portal, sold on the web. The server
  stores plan entitlements (number of projects, storage quota, share links, push) and checks
  them on every write. Tokens carry the plan, but the server's record is what counts.
- **App stores:** if native apps ship, they're reader-style apps that sign in to an existing
  account. US rules now allow linking out to web checkout. Revisit in-app purchase only if the
  data shows people want it.

### Stack

| Part | Choice | Why |
|---|---|---|
| API | Cloudflare Workers | close to users, no servers to run, fits the small JSON API |
| File storage | Cloudflare R2 | no download fees, which matters when the traffic is video previews |
| Database | Cloudflare D1 | users, projects, versions, requests, entitlements |
| Live channel | Durable Objects, one per project | websocket fan-out and ordered request log per project |
| Web app | the existing `storian/web` page plus a manifest file and a service worker | one codebase for localhost and cloud |
| Billing | Stripe | subscriptions, tax, customer portal |
| Push | standard Web Push (VAPID keys) | works in installed web apps on iOS and Android |

### Privacy and security

- **What's uploaded:** footage is never uploaded. The copy strips local paths and camera location
  metadata. `storian sync --dry-run` lists exactly what would leave the machine.
- **Delete:** `storian unpublish` deletes a project's copy, versions and requests. Account
  deletion removes everything within 30 days.
- **Files:** stored privately and served through short-lived signed URLs. Share links are random,
  revocable and optionally expiring.
- **Phase 0 LAN mode:** binds to the local network with a random token in the URL, because the
  current server binds only to 127.0.0.1 and has no auth.
- **End-to-end encryption:** an optional mode later. It isn't the default, because it breaks share
  links and the phase 3 cloud agent.

### Keeping it future-proof

- **Version the files:** every project file and protocol message carries `schema_version`. Readers
  accept older versions and ignore unknown fields, so old CLIs and new apps keep working together.
- **The protocol is public:** the manifest and request formats are documented in this repo.
  Self-hosting is allowed; the hosted service wins on convenience and reliability.
- **Moving the agent changes nothing:** a cloud agent is just another writer that reads requests
  and commits manifests.
- **Proxies fit the same model:** 540p proxies of the whole library (phase 3) are files named by
  content, like everything else in the copy.

## Roadmap

| Phase | Scope | Exit criteria | Plan |
|---|---|---|---|
| **0 · Mobile-ready (1 week)** | Fix the phone layout of every tab; installable web app. `storian serve --lan` with a token and a QR code for same-Wi-Fi use. Ticks stay in local storage. | The shot list and animatic are good to use on a phone on the same Wi-Fi. | Free |
| **1 · Sync MVP (4–6 weeks)** | `login`, `sync` (only new files, `--dry-run`), `inbox`; hosted viewer; QR pairing; offline shot list with synced ticks; comments; Stripe; one share link per project. | People sync and open the project on a phone within a day of signing up; shoot mode is used on a real shoot. | **Pro** |
| **2 · Agent from the phone (4 weeks)** | `sync --watch` running the user's agent; request states and replies; chat panel; voice notes; push notifications; viewer comments on share links; "what changed" view. | A comment made on the phone becomes a re-cut on the phone without the user touching the laptop. | **Pro** |
| **3 · Laptop-off** | Optional proxy upload; a cloud agent that re-cuts and renders previews from proxies; native wrappers if needed; team workspaces. | A re-cut finishes while the laptop is closed. | **Studio** |

Price placeholders, to be tested rather than assumed: Pro at $8–10 a month (sync, mobile,
3 active projects, 10 GB), Studio at $20–30 a month (proxies, cloud agent, more storage, team).

## Metrics

- **Activation:** share of new Pro users who open a synced project on a phone within 24 hours.
- **Shoot mode:** shots ticked per active user per month, and the share of ticked shots later
  matched to new clips.
- **The loop:** median time from a phone comment to its `resolve`, in phase 2.
- **Business:** free-to-Pro conversion among people who run `storian sync`; Pro monthly churn.

## Risks

| Risk | Mitigation |
|---|---|
| People don't want storyboards on their phone. | Phase 0 tests this for free before any cloud work. |
| Preview storage grows with every re-cut. | Files are named by content, so versions share files. 540p previews, expiring old versions, storage quota per plan. |
| The agent isn't running when a phone request arrives. | Clear request states ("waiting for your laptop"), `sync --watch`, and the cloud agent in phase 3. |
| Open source makes the paid tier easy to copy. | The paid value is a reliable hosted service and the phone experience, not hidden code. A self-hosted version doesn't hurt. |
| App store policies change. | The web app needs no store. Native wrappers are optional and sign in to existing accounts. |

## Open questions

1. Is the phone experience strong enough to pay for on its own, or is it the share links? Phase 0
   and early phase 1 interviews decide which one leads the pricing page.
2. Should share-link viewers need an account to comment? Proposal: name only, rate-limited.
3. Which model and cost cap should the phase 3 cloud agent use, and is it metered or included?
4. Should optional end-to-end encryption ship before phase 3 for privacy-sensitive users?
