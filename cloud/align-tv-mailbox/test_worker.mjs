import w from "./worker.js";
import { AlignMailbox } from "./worker.js";
const objets = new Map();
const namespace = {
  idFromName: (n) => n,
  get: (id) => {
    if (!objets.has(id)) { const m = new Map(); objets.set(id, new AlignMailbox({ storage: { put: async (k, v) => m.set(k, v), get: async (k) => m.get(k) } })); }
    const o = objets.get(id);
    return { fetch: (u, init) => o.fetch(new Request(u, init)) };
  },
};
const env = { ALIGN_TV_INGEST_TOKEN: "i".repeat(40), ALIGN_TV_MAILBOX_TOKEN: "r".repeat(40), ALIGN_TV_MAILBOX: namespace };
const call = async (m, p, body, h = {}) => { const r = await w.fetch(new Request("https://x" + p, { method: m, body, headers: h }), env); return [r.status, await r.json()]; };
const ok = (c, msg) => { if (!c) { console.log("ÉCHEC", msg); process.exit(1); } console.log("OK  ", msg); };
let [s, b] = await call("GET", "/health"); ok(s === 200 && b.ok, "health");
[s] = await call("POST", "/ingest/" + "x".repeat(40), "{}"); ok(s === 401, "ingest refusé sans bon jeton");
[s, b] = await call("POST", "/ingest/" + env.ALIGN_TV_INGEST_TOKEN, '{"source":"AUTRE"}'); ok(s === 202 && b.ignored, "message non ALIGN ignoré");
[s] = await call("POST", "/ingest/" + env.ALIGN_TV_INGEST_TOKEN, '{"source":"ALIGN_MTF_PRO_V25","symbol":"EURUSD"}'); ok(s === 400, "symbole hors liste refusé");
[s] = await call("POST", "/ingest/" + env.ALIGN_TV_INGEST_TOKEN, '{"source":"ALIGN_MTF_PRO_V25","symbol":"BTCUSD","tickerid":"CRYPTO:BTCUSD","price":64000}'); ok(s === 200, "BTC stocké");
[s] = await call("GET", "/mailbox?symbol=BTCUSD"); ok(s === 401, "lecture refusée sans jeton");
[s, b] = await call("GET", "/mailbox?symbol=BTCUSD", undefined, { authorization: "Bearer " + env.ALIGN_TV_MAILBOX_TOKEN }); ok(s === 200 && b.payload.price === 64000 && b.receivedAt > 0, "lecture BTC avec jeton");
[s, b] = await call("GET", "/mailbox?symbol=NAS100", undefined, { authorization: "Bearer " + env.ALIGN_TV_MAILBOX_TOKEN }); ok(s === 200 && b.ok === false, "NASDAQ vide signalé");
// Webhook TradingView sans jeton : accepté UNIQUEMENT depuis les IP officielles TradingView.
[s] = await call("POST", "/ingest/tradingview", '{"source":"ALIGN_MTF_PRO_V25","symbol":"XAUUSD","tickerid":"FOREXCOM:XAUUSD","price":2400}', { "cf-connecting-ip": "1.2.3.4" });
ok(s === 401, "webhook /ingest/tradingview refusé hors IP TradingView");
[s] = await call("POST", "/ingest/tradingview", '{"source":"ALIGN_MTF_PRO_V25","symbol":"XAUUSD","tickerid":"FOREXCOM:XAUUSD","price":2400}');
ok(s === 401, "webhook /ingest/tradingview refusé sans IP");
[s] = await call("POST", "/ingest/tradingview", '{"source":"ALIGN_MTF_PRO_V25","symbol":"XAUUSD","tickerid":"FOREXCOM:XAUUSD","price":2400}', { "cf-connecting-ip": "52.89.214.238" });
ok(s === 200, "webhook TradingView accepté depuis une IP officielle");
[s, b] = await call("GET", "/mailbox?symbol=XAUUSD", undefined, { authorization: "Bearer " + env.ALIGN_TV_MAILBOX_TOKEN });
ok(s === 200 && b.payload.price === 2400, "GOLD lu après webhook TradingView");
// 18/11 : alerte NAS100 envoyée avec « BTCUSD » → refusée, la boîte BTC reste intacte.
[s, b] = await call("POST", "/ingest/" + env.ALIGN_TV_INGEST_TOKEN, '{"source":"ALIGN_MTF_PRO_V25","symbol":"BTCUSD","tickerid":"FX:NAS100","price":27000}');
ok(s === 400 && b.error === "symbol_tickerid_mismatch", "marché mélangé refusé (NAS100 déclaré BTCUSD)");
[s, b] = await call("GET", "/mailbox?symbol=BTCUSD", undefined, { authorization: "Bearer " + env.ALIGN_TV_MAILBOX_TOKEN });
ok(s === 200 && b.payload.price === 64000, "boîte BTC non polluée");
[s] = await call("POST", "/ingest/" + env.ALIGN_TV_INGEST_TOKEN, '{"source":"ALIGN_MTF_PRO_V25","symbol":"NAS100","price":27000}');
ok(s === 400, "tickerid absent refusé");
