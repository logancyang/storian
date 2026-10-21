// Private storyboard on Cloudflare: static assets behind a one-time key.
// `storian publish` deploys this with the project snapshot. KEY_HASH and COOKIE_CHECK are
// SHA-256 hashes, so neither the key nor a valid cookie can be read back from the config.

const enc = new TextEncoder();
const PUBLIC = new Set(["/login", "/sw.js", "/manifest.webmanifest", "/icon-180.png", "/icon-512.png"]);
const API = { "/api/project": "/api/project.json", "/api/version": "/api/version.json" };

async function sha(s) {
  const b = await crypto.subtle.digest("SHA-256", enc.encode(s));
  return [...new Uint8Array(b)].map(x => x.toString(16).padStart(2, "0")).join("");
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    if (url.pathname === "/login") return login(req, env);
    if (!PUBLIC.has(url.pathname)) {
      const m = (req.headers.get("Cookie") || "").match(/(?:^|;\s*)storian=([0-9a-f]{64})/);
      if (!m || (await sha(m[1])) !== env.COOKIE_CHECK) {
        const page = req.headers.get("Sec-Fetch-Mode") === "navigate" || (req.headers.get("Accept") || "").includes("text/html");
        return page ? Response.redirect(`${url.origin}/login`, 302) : new Response("sign in first", { status: 401 });
      }
    }
    const target = API[url.pathname];
    const res = await env.ASSETS.fetch(target ? new Request(new URL(target, url), req) : req);
    const media = url.pathname.startsWith("/media/");
    const out = media && res.status === 200 && req.headers.has("Range") ? await ranged(req, res) : new Response(res.body, res);
    out.headers.set("X-Robots-Tag", "noindex");
    out.headers.set("Cache-Control", media ? "private, max-age=604800" : "private, no-cache");
    if (media) out.headers.set("Accept-Ranges", "bytes");
    return out;
  },
};

// Static assets answer Range requests with the whole file, and iPhone Safari won't play
// video without 206 responses. Media files are a few MB, so slicing in memory is fine.
async function ranged(req, res) {
  const m = req.headers.get("Range").match(/^bytes=(\d*)-(\d*)$/);
  if (!m || (!m[1] && !m[2])) return new Response(res.body, res);
  const buf = await res.arrayBuffer(), size = buf.byteLength;
  const start = m[1] ? +m[1] : Math.max(0, size - +m[2]);
  const end = m[1] && m[2] ? Math.min(+m[2], size - 1) : size - 1;
  const headers = new Headers(res.headers);
  if (start >= size || start > end) {
    headers.set("Content-Range", `bytes */${size}`);
    return new Response(null, { status: 416, headers });
  }
  headers.set("Content-Range", `bytes ${start}-${end}/${size}`);
  headers.set("Content-Length", String(end - start + 1));
  return new Response(buf.slice(start, end + 1), { status: 206, headers });
}

async function login(req, env) {
  if (req.method === "POST") {
    const key = String((await req.formData()).get("key") || "").trim();
    if ((await sha(key)) === env.KEY_HASH) {
      const cookie = await sha("cookie:" + key);
      return new Response(null, { status: 303, headers: {
        Location: "/", "Set-Cookie": `storian=${cookie}; Path=/; Max-Age=31536000; HttpOnly; Secure; SameSite=Lax` } });
    }
    return page(env, "That key didn't match. Copy it again from the laptop.", 401);
  }
  return page(env, "");
}

function page(env, error, status = 200) {
  const name = (env.PROJECT || "Storian").replace(/[<>&"]/g, "");
  return new Response(`<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#000000"><title>${name} · Storian</title>
<link rel="manifest" href="/manifest.webmanifest"><link rel="apple-touch-icon" href="/icon-180.png">
<style>
:root { --paper: #000; --ink: #fff; --paper-2: #FFD147; --ink-soft: #5765FF; --grid: rgba(255,255,255,.10); --muted: rgba(255,255,255,.62); }
* { box-sizing: border-box; }
body { margin: 0; min-height: 100vh; display: grid; place-items: center; background: var(--paper); color: var(--ink);
  font: 16px/1.5 system-ui, sans-serif; background-image: linear-gradient(var(--grid) 1px, transparent 1px),
  linear-gradient(90deg, var(--grid) 1px, transparent 1px); background-size: 32px 32px; padding: 16px; }
form { width: min(420px, 100%); border: 1.5px solid var(--ink); background: #000; padding: 28px 24px; }
.micro { font: 600 12px/1 system-ui; letter-spacing: .16em; text-transform: uppercase; color: var(--muted); }
h1 { font: 400 40px/1 Georgia, serif; margin: 14px 0 10px; } h1 b { color: var(--paper-2); font-weight: 400; }
p { color: var(--muted); margin: 0 0 20px; } .err { color: #ff7b7b; }
input { width: 100%; background: #000; color: var(--ink); border: 1.5px solid var(--ink); font: 16px ui-monospace, monospace; padding: 14px 12px; }
button { width: 100%; margin-top: 12px; background: var(--paper-2); color: #000; border: 0; font: 600 14px system-ui; letter-spacing: .14em; text-transform: uppercase; padding: 16px; }
</style></head><body>
<form method="post" action="/login"><div class="micro">Storian · private storyboard</div><h1>${name}<b>.</b></h1>
<p class="${error ? "err" : ""}">${error || "Enter the key that <code>storian publish</code> printed on your laptop. You only do this once per device."}</p>
<input name="key" id="key" autocomplete="current-password" autocapitalize="off" spellcheck="false" placeholder="key" required>
<button>Open</button></form>
<script>
const k = new URLSearchParams(location.hash.slice(1)).get("k");
if (k && !${JSON.stringify(Boolean(error))}) { document.getElementById("key").value = k; history.replaceState(null, "", "/login"); document.forms[0].submit(); }
</script></body></html>`, { status, headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store", "X-Robots-Tag": "noindex" } });
}
