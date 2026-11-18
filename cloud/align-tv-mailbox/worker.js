// ALIGN — boîte aux lettres TradingView (Cloudflare Worker + Durable Object).
// Rôle UNIQUE : recevoir les alertes JSON du Pine v25 et garder la dernière par marché.
// Aucune validation métier ici : la seule source de validation reste
// align-bot/align_tv_bridge.py (BridgeStore), exécuté dans GitHub Actions.
//
// Stockage : un Durable Object par marché (lecture toujours à jour, contrairement
// à KV dont le cache peut dépasser la fenêtre de fraîcheur de 30 s du bridge).
//
// Routes :
//   POST /ingest/<ALIGN_TV_INGEST_TOKEN>      ← webhook d'alerte TradingView
//   GET  /mailbox?symbol=BTCUSD               ← lecture (Authorization: Bearer <ALIGN_TV_MAILBOX_TOKEN>)
//   GET  /health                              ← santé, sans secret
// Liaison : ALIGN_TV_MAILBOX (Durable Object). Secrets : ALIGN_TV_INGEST_TOKEN, ALIGN_TV_MAILBOX_TOKEN.

const SOURCE = "ALIGN_MTF_PRO_V25";
const SYMBOLS = new Set(["BTCUSD", "XAUUSD", "NAS100"]);
const MAX_BODY = 32768;
const MAX_AGE_MS = 10 * 60 * 1000; // au-delà de 10 min, le message n'est plus servi

function json(status, body) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json", "cache-control": "no-store" },
  });
}

function sameSecret(a, b) {
  if (typeof a !== "string" || typeof b !== "string" || a.length !== b.length || a.length < 32) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

// Un objet par marché : écriture et lecture passent par le même objet, donc toujours cohérentes.
export class AlignMailbox {
  constructor(state) { this.state = state; }
  async fetch(request) {
    if (request.method === "PUT") {
      await this.state.storage.put("latest", await request.text());
      return new Response("ok");
    }
    const stored = await this.state.storage.get("latest");
    return stored ? new Response(stored, { status: 200 }) : new Response(null, { status: 204 });
  }
}

function box(env, symbol) {
  return env.ALIGN_TV_MAILBOX.get(env.ALIGN_TV_MAILBOX.idFromName(symbol));
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === "GET" && url.pathname === "/health") {
      return json(200, { ok: true, service: "align-tv-mailbox", source: SOURCE });
    }

    if (request.method === "POST" && url.pathname.startsWith("/ingest/")) {
      if (!sameSecret(url.pathname.slice("/ingest/".length), env.ALIGN_TV_INGEST_TOKEN)) {
        return json(401, { ok: false, error: "unauthorized" });
      }
      const raw = await request.text();
      if (raw.length > MAX_BODY) return json(413, { ok: false, error: "payload_too_large" });
      let payload;
      try { payload = JSON.parse(raw); } catch { return json(202, { ok: true, ignored: true, reason: "not_json" }); }
      if (!payload || payload.source !== SOURCE) return json(202, { ok: true, ignored: true, reason: "not_an_align_snapshot" });
      const symbol = String(payload.symbol || "").toUpperCase();
      if (!SYMBOLS.has(symbol)) return json(400, { ok: false, error: "unsupported_symbol" });
      await box(env, symbol).fetch("https://box/", { method: "PUT", body: JSON.stringify({ receivedAt: Date.now(), payload }) });
      return json(200, { ok: true, symbol });
    }

    if (request.method === "GET" && url.pathname === "/mailbox") {
      const auth = request.headers.get("authorization") || "";
      if (!sameSecret(auth.replace(/^Bearer\s+/i, ""), env.ALIGN_TV_MAILBOX_TOKEN)) {
        return json(401, { ok: false, error: "unauthorized" });
      }
      const symbol = String(url.searchParams.get("symbol") || "").toUpperCase();
      if (!SYMBOLS.has(symbol)) return json(400, { ok: false, error: "unsupported_symbol" });
      const res = await box(env, symbol).fetch("https://box/");
      const stored = res.status === 200 ? JSON.parse(await res.text()) : null;
      if (!stored || Date.now() - stored.receivedAt > MAX_AGE_MS) return json(200, { ok: false, symbol, error: "empty" });
      return json(200, { ok: true, symbol, ...stored });
    }

    return json(404, { ok: false, error: "not_found" });
  },
};
