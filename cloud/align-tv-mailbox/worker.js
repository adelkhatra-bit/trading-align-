// ALIGN — boîte aux lettres TradingView (Cloudflare Worker + Durable Object).
// Rôle UNIQUE : recevoir les alertes JSON du Pine v25 et garder la dernière par marché.
// Aucune validation métier ici : la seule source de validation reste
// align-bot/align_tv_bridge.py (BridgeStore), exécuté dans GitHub Actions.
//
// Stockage : un Durable Object par marché (lecture toujours à jour, contrairement
// à KV dont le cache peut dépasser la fenêtre de fraîcheur de 30 s du bridge).
//
// Routes :
//   POST /ingest/tradingview                  ← webhook TradingView, SANS jeton dans l'URL :
//                                               accepté seulement depuis les 4 IP officielles de TradingView
//   POST /ingest/<ALIGN_TV_INGEST_TOKEN>      ← envoi manuel / tests (jeton)
//   GET  /mailbox?symbol=BTCUSD               ← lecture (Authorization: Bearer <ALIGN_TV_MAILBOX_TOKEN>)
//   GET  /health                              ← santé, sans secret
// Liaison : ALIGN_TV_MAILBOX (Durable Object). Secrets : ALIGN_TV_INGEST_TOKEN, ALIGN_TV_MAILBOX_TOKEN.

const SOURCE = "ALIGN_MTF_PRO_V25";
const SYMBOLS = new Set(["BTCUSD", "XAUUSD"]);
const MAX_BODY = 32768;
const MAX_AGE_MS = 10 * 60 * 1000; // au-delà de 10 min, le message n'est plus servi
// Canal séparé pour la scène Thomas/Leïla. Il utilise un ID DO distinct de BTCUSD/XAUUSD.
const SHOW_ORIGIN = "https://adelkhatra-bit.github.io";
const SHOW_MAX_AGE_MS = 60 * 1000;
const SHOW_MIN_INTERVAL_MS = 12 * 1000;
const SHOW_MAX_MESSAGE = 2048;
// IP d'envoi publiées par TradingView (support.tradingview.com, « About webhooks »).
const TRADINGVIEW_IPS = new Set(["52.89.214.238", "34.212.75.30", "54.218.53.128", "52.32.178.7"]);

// Le marché déclaré doit correspondre au graphique réel (syminfo.tickerid) : jamais de mélange
// (18/11 : alertes NAS100/XAUUSD envoyées avec « BTCUSD »). Même règle que align_tv_bridge.py.
const TICKER_MARKERS = {
  BTCUSD: ["BTC", "XBT"],
  XAUUSD: ["XAU", "GOLD"],
};

export function tickerMatchesSymbol(symbol, tickerid) {
  const ticker = String(tickerid || "").trim().slice(0, 64).toUpperCase().split(":").pop();
  if (!ticker) return false;
  const hits = Object.keys(TICKER_MARKERS).filter((m) => TICKER_MARKERS[m].some((k) => ticker.includes(k)));
  return hits.length === 1 && hits[0] === symbol;
}

function depuisTradingView(request) {
  return TRADINGVIEW_IPS.has(String(request.headers.get("cf-connecting-ip") || "").trim());
}

function json(status, body, extraHeaders = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json", "cache-control": "no-store", ...extraHeaders },
  });
}

function showCors(request) {
  const origin = String(request.headers.get("origin") || "");
  return origin === SHOW_ORIGIN
    ? { "access-control-allow-origin": origin, "access-control-allow-methods": "GET, OPTIONS",
        "access-control-allow-headers": "content-type", "access-control-max-age": "600", "vary": "Origin" }
    : {};
}

function showBox(env) {
  // ID dédié : ne partage jamais les clés latest des boîtes BTCUSD et XAUUSD.
  return env.ALIGN_TV_MAILBOX.get(env.ALIGN_TV_MAILBOX.idFromName("LIVE_SHOW"));
}

async function lireShow(env) {
  const response = await showBox(env).fetch("https://box/");
  if (response.status !== 200) return { show: null, voice: null, voiceEnabled: false, voiceUpdatedAt: 0 };
  try { return JSON.parse(await response.text()); }
  catch { return { show: null, voice: null, voiceEnabled: false, voiceUpdatedAt: 0 }; }
}

async function ecrireShow(env, state) {
  await showBox(env).fetch("https://box/", { method: "PUT", body: JSON.stringify(state) });
}

function parseShowMessage(raw, type) {
  if (typeof raw !== "string" || !raw || raw.length > SHOW_MAX_MESSAGE) return null;
  try {
    const payload = JSON.parse(raw);
    return payload && payload.type === type ? payload : null;
  } catch { return null; }
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

    if (url.pathname.startsWith("/show/")) {
      const cors = showCors(request);
      if (request.method === "OPTIONS") return json(200, { ok: true }, cors);

      if (request.method === "GET" && url.pathname === "/show/state") {
        const state = await lireShow(env);
        const now = Date.now();
        const show = state.show && now - Number(state.show.ts || 0) <= SHOW_MAX_AGE_MS ? state.show : null;
        const voice = state.voice && now - Number(state.voice.ts || 0) <= 30000 ? state.voice : null;
        return json(200, { ok: true, show, voice, voiceEnabled: state.voiceEnabled === true,
          voiceUpdatedAt: Number(state.voiceUpdatedAt || 0) }, cors);
      }

      if (request.method === "GET" && url.pathname === "/show/publish") {
        if (request.headers.get("origin") !== SHOW_ORIGIN) return json(403, { ok: false, error: "origin_forbidden" }, cors);
        const payload = parseShowMessage(url.searchParams.get("message"), "ALIGN_SHOW");
        const now = Date.now();
        if (!payload || payload.action !== "PAIR" ||
            !["t", "l"].includes(payload.speaker1) || !["t", "l"].includes(payload.speaker2) ||
            payload.speaker1 === payload.speaker2 ||
            !["BTC", "GOLD"].includes(payload.market) ||
            typeof payload.text1 !== "string" || payload.text1.trim().length < 12 || payload.text1.length > 280 ||
            typeof payload.text2 !== "string" || payload.text2.trim().length < 12 || payload.text2.length > 280 ||
            !["t", "l"].includes(payload.speaker1EN) || !["t", "l"].includes(payload.speaker2EN) ||
            typeof payload.text1EN !== "string" || payload.text1EN.trim().length < 12 || payload.text1EN.length > 280 ||
            typeof payload.text2EN !== "string" || payload.text2EN.trim().length < 12 || payload.text2EN.length > 280 ||
            !Number.isFinite(Number(payload.ts)) || now - Number(payload.ts) > 10000 || Number(payload.ts) > now + 5000 ||
            !Number.isFinite(Number(payload.startAt)) || Number(payload.startAt) < now + 1000 || Number(payload.startAt) > now + 12000 ||
            !Number.isFinite(Number(payload.duration1)) || Number(payload.duration1) < 2500 || Number(payload.duration1) > 12000 ||
            !Number.isFinite(Number(payload.duration2)) || Number(payload.duration2) < 2500 || Number(payload.duration2) > 12000 ||
            !Number.isFinite(Number(payload.duration1EN)) || Number(payload.duration1EN) < 2500 || Number(payload.duration1EN) > 12000 ||
            !Number.isFinite(Number(payload.duration2EN)) || Number(payload.duration2EN) < 2500 || Number(payload.duration2EN) > 12000) {
          return json(400, { ok: false, error: "invalid_show_payload" }, cors);
        }
        const state = await lireShow(env);
        if (state.show && Number(payload.ts) <= Number(state.show.ts || 0)) return json(409, { ok: false, error: "stale_show" }, cors);
        if (state.show && now - Number(state.show.ts || 0) < SHOW_MIN_INTERVAL_MS) return json(429, { ok: false, error: "show_rate_limited" }, cors);
        state.show = payload;
        state.updatedAt = now;
        await ecrireShow(env, state);
        return json(200, { ok: true, id: payload.id || payload.ts }, cors);
      }

      if (request.method === "GET" && url.pathname === "/show/voice") {
        const payload = parseShowMessage(url.searchParams.get("message"), "ALIGN_VOICE");
        const now = Date.now();
        if (!payload || !["START", "STOP"].includes(payload.action) ||
            !["t", "l"].includes(payload.speaker) || !["fr", "en"].includes(payload.lang) ||
            !Number.isFinite(Number(payload.ts)) || now - Number(payload.ts) > 10000 || Number(payload.ts) > now + 5000 ||
            typeof payload.text !== "string" || payload.text.length > 280 ||
            !Number.isFinite(Number(payload.durationMs)) || Number(payload.durationMs) < 0 || Number(payload.durationMs) > 20000) {
          return json(400, { ok: false, error: "invalid_voice_payload" }, cors);
        }
        const state = await lireShow(env);
        if (state.voice && Number(payload.ts) <= Number(state.voice.ts || 0)) return json(409, { ok: false, error: "stale_voice" }, cors);
        state.voice = payload;
        state.updatedAt = now;
        await ecrireShow(env, state);
        return json(200, { ok: true, ts: payload.ts }, cors);
      }

      if (request.method === "GET" && url.pathname === "/show/coach") {
        const enabled = url.searchParams.get("enabled");
        if (enabled !== "1" && enabled !== "0") return json(400, { ok: false, error: "invalid_coach_state" }, cors);
        const state = await lireShow(env);
        state.voiceEnabled = enabled === "1";
        state.voiceUpdatedAt = Date.now();
        if (!state.voiceEnabled) state.voice = null;
        state.updatedAt = Date.now();
        await ecrireShow(env, state);
        return json(200, { ok: true, voiceEnabled: state.voiceEnabled }, cors);
      }
    }

    if (request.method === "GET" && url.pathname === "/health") {
      return json(200, { ok: true, service: "align-tv-mailbox", source: SOURCE });
    }

    if (request.method === "POST" && url.pathname.startsWith("/ingest/")) {
      const viaTradingView = url.pathname === "/ingest/tradingview" && depuisTradingView(request);
      if (!viaTradingView && !sameSecret(url.pathname.slice("/ingest/".length), env.ALIGN_TV_INGEST_TOKEN)) {
        return json(401, { ok: false, error: "unauthorized" });
      }
      const raw = await request.text();
      if (raw.length > MAX_BODY) return json(413, { ok: false, error: "payload_too_large" });
      let payload;
      try { payload = JSON.parse(raw); } catch { return json(202, { ok: true, ignored: true, reason: "not_json" }); }
      if (!payload || payload.source !== SOURCE) return json(202, { ok: true, ignored: true, reason: "not_an_align_snapshot" });
      const symbol = String(payload.symbol || "").toUpperCase();
      if (!SYMBOLS.has(symbol)) return json(400, { ok: false, error: "unsupported_symbol" });
      if (!tickerMatchesSymbol(symbol, payload.tickerid)) {
        return json(400, { ok: false, error: "symbol_tickerid_mismatch", symbol });
      }
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
