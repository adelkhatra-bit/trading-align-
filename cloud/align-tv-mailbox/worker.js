// ALIGN — boîte aux lettres TradingView (Cloudflare Worker).
// Rôle UNIQUE : recevoir les alertes JSON du Pine v25 et garder la dernière par marché.
// Aucune validation métier ici : la seule source de validation reste
// align-bot/align_tv_bridge.py (BridgeStore), exécuté dans GitHub Actions.
//
// Routes :
//   POST /ingest/<ALIGN_TV_INGEST_TOKEN>      ← webhook d'alerte TradingView
//   GET  /mailbox?symbol=BTCUSD               ← lecture (Authorization: Bearer <ALIGN_TV_MAILBOX_TOKEN>)
//   GET  /health                              ← santé, sans secret
// Liaison KV requise : ALIGN_TV_KV. Secrets : ALIGN_TV_INGEST_TOKEN, ALIGN_TV_MAILBOX_TOKEN.

const SOURCE = "ALIGN_MTF_PRO_V25";
const SYMBOLS = new Set(["BTCUSD", "XAUUSD", "NAS100"]);
const MAX_BODY = 32768;
const TTL_SECONDS = 600; // une donnée de plus de 10 min disparaît d'elle-même

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
      await env.ALIGN_TV_KV.put("latest:" + symbol, JSON.stringify({ receivedAt: Date.now(), payload }), { expirationTtl: TTL_SECONDS });
      return json(200, { ok: true, symbol });
    }

    if (request.method === "GET" && url.pathname === "/mailbox") {
      const auth = request.headers.get("authorization") || "";
      if (!sameSecret(auth.replace(/^Bearer\s+/i, ""), env.ALIGN_TV_MAILBOX_TOKEN)) {
        return json(401, { ok: false, error: "unauthorized" });
      }
      const symbol = String(url.searchParams.get("symbol") || "").toUpperCase();
      if (!SYMBOLS.has(symbol)) return json(400, { ok: false, error: "unsupported_symbol" });
      const stored = await env.ALIGN_TV_KV.get("latest:" + symbol);
      return json(200, stored ? { ok: true, symbol, ...JSON.parse(stored) } : { ok: false, symbol, error: "empty" });
    }

    return json(404, { ok: false, error: "not_found" });
  },
};
