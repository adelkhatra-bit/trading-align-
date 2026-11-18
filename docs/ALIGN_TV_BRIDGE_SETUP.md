# ALIGN canonical Pine v25 → ROBOT V12 bridge

## Scope

This bridge connects the **canonical production indicator** `align-bot/pine/ALIGN_MTF_PRO_v25.pine` (`ALIGN MTF PRO v25 (Inside)`) to the existing ALIGN MTF BOT preflight contract.

The only Pine changes are two isolated, opt-in bridge blocks:
- a settings group, disabled by default;
- a structured JSON export appended after the existing script.

The canonical indicator's existing source is protected by a regression test: after removing those two bridge blocks, its Git blob SHA must remain exactly `823635f039ff3b59c39867a7b59dfa3ed6fafaf1`. The title, short title, signal calculations, Entry/SL/TP1/TP2 logic, animation setting, chart drawings, table and existing human-readable alerts remain unchanged. No second indicator is introduced.

This service is isolated from the legacy `server.js`/port 4000 and from the `tradingview-analyzer` extension. Do not reuse the old project, its ports, or its Cloudflare tunnel.

## Data flow

1. One TradingView chart and one alert are configured for each market: BTC, GOLD and NASDAQ.
2. In the canonical v25 indicator settings, enable **Envoyer les snapshots au ROBOT V12** and select the exact market: `BTCUSD`, `XAUUSD` or `NAS100`. This option is **disabled by default**.
3. Create one alert per chart with condition **Any alert() function call** and the Cloudflare mailbox webhook URL shown below.
4. While the chart is receiving real-time updates, Pine emits a structured JSON snapshot every 20 seconds. The same alert can also receive the existing human-readable signal messages; the mailbox Worker ignores non-JSON messages.
5. The payload includes `source=ALIGN_MTF_PRO_V25`, the declared market, the actual `syminfo.tickerid`, active timeframe, TradingView price, the fixed M15 Entry/SL/TP1/TP2 plan, confirmation state and independent MTF direction/RSI/bar-time data for M1, M5, M15, M30, H1, H2, H4, D1 and W1.
6. The Cloudflare Worker accepts `POST /ingest/tradingview` only from TradingView's published webhook IPs. It verifies the source, market and real ticker identity, then stores the latest payload in one Durable Object per market. The route has **no token in its URL**.
7. The GitHub Actions worker starts `align_tv_bridge.py` on its own runner at `127.0.0.1:4100` and starts `align_tv_mailbox_feeder.py`. The feeder reads the three Cloudflare mailboxes and forwards their payloads to that temporary local bridge.
8. The Python bridge validates timestamps, each timeframe's own candle timestamp, the active price, the fixed M15 plan, the entry zone and the strategy-specific closed trigger candle. The trigger timeframe is independent of the chart timeframe: SCALPING = M1, DAY = M5, SWING = H1.
9. When `ALIGN_REQUIRE_TV_BRIDGE=1` (production default), the bot does not authorize a local Python-generated substitute for Entry/SL/TP. Missing or invalid Pine snapshots mean **MODE SANS SIGNAL**. The bridge never places broker orders.
10. The mailbox stops serving a market snapshot after 10 minutes. The production preflight is stricter: the active TradingView price must be no more than 30 seconds old, and the required M5/M15/H1/H4/D1/W1 snapshots must be fresh.
11. After a completed worker run, the publisher updates `live-data/live.json`; the live band reads that public file. A recent `live.json` alone does not prove that Pine webhooks were received: the worker's `BRIDGE_CONFIRMED` checks are the proof of bridge ingestion.

## Local service

The current production path is a **Cloudflare mailbox plus a temporary bridge inside GitHub Actions**:

- TradingView sends to the Cloudflare Worker; it does not connect to the GitHub runner or to the user's PC.
- The workflow starts `align_tv_bridge.py` on the runner at `127.0.0.1:4100` and the mailbox feeder forwards the latest payloads to it.
- The local bridge is temporary and in-memory. A new runner starts empty and must wait for fresh TradingView webhooks before the bot can pass its bridge preflight.
- Do not expose port 4100, create a tunnel to the PC, or reuse ports/services from another project for this path.
- The Worker has a non-secret `GET /health` route. Its `GET /mailbox?symbol=...` route requires a bearer token and is used only by the authenticated feeder.
- The Worker also retains `POST /ingest/<ALIGN_TV_INGEST_TOKEN>` for controlled manual/test ingestion. **TradingView uses `/ingest/tradingview`, not the token route.**

The feeder reads the mailbox using the HMAC-derived read credential associated with the GitHub Actions secret `CLOUDFLARE_API_TOKEN`. The workflow and Worker must retain their matching configuration. Do not print, copy into source, or share any secret value.

An externally hosted bridge remains an optional alternate mode: if the repository secret `ALIGN_TV_API_URL` is deliberately configured, the workflow skips the local mailbox relay and reads that external bridge using `ALIGN_TV_READ_TOKEN`. The current workflow run inspected for this audit had no external `ALIGN_TV_API_URL` configured and entered the Cloudflare-mailbox mode. Do not add the two external-bridge secrets unless that alternate hosting mode is intentionally selected.

## TradingView configuration

For each of the three charts, use the canonical **ALIGN MTF PRO v25 (Inside)** indicator:

1. Open the indicator settings and expand **Bridge ALIGN (optionnel)**.
2. Turn on **Envoyer les snapshots au ROBOT V12**. It is off by default.
3. Set **Marché ALIGN** to the chart's actual market:
   - BTC chart: `BTCUSD` (the actual ticker ID must identify BTC or XBT).
   - GOLD chart: `XAUUSD` (the actual ticker ID must identify XAU or GOLD).
   - NASDAQ chart: `NAS100` (the actual ticker ID must identify NAS100, NDX, US100, USTEC or NQ).
4. Use a supported active chart timeframe: M1, M5, M15, M30, H1, H2, H4, D1 or W1. The same payload contains the other MTF readings; separate alerts per timeframe are not required.
5. Create one alert for that chart with condition **Any alert() function call** and set this exact webhook URL:

   `https://align-tv-mailbox.adel-khatra.workers.dev/ingest/tradingview`

6. Save and ensure the alert is enabled. Repeat for BTC, GOLD and NASDAQ, with the matching market selection on each chart.

The Worker accepts this route only from TradingView's published webhook IPs. Do not append an ingress token, use the old dedicated-tunnel URL, or point the alert at `127.0.0.1:4100`. A wrong `Marché ALIGN` / `syminfo.tickerid` pair is rejected to prevent cross-market contamination.

## GitHub Actions secrets

For the current Cloudflare-mailbox mode:

- `CLOUDFLARE_API_TOKEN` must be configured as a GitHub Actions secret with the permissions required by the existing mailbox relay/deployment setup. The feeder derives its read credential from this secret; the value is never logged.
- The Cloudflare Worker must have its matching internal mailbox-read configuration. Do not expose that value in the repository, TradingView alert URL or chat.
- `ALIGN_TV_API_URL` and `ALIGN_TV_READ_TOKEN` are **only** for the optional externally hosted bridge mode. When `ALIGN_TV_API_URL` is set, the workflow skips the local mailbox relay. Do not set these to the Cloudflare mailbox URL: the mailbox is an ingestion/relay service, not the Python bridge API.

No secret was changed as part of this documentation correction.

## Validation and limits

- `test_align_tv_bridge.py` covers authentication, source/symbol/timeframe validation, MTF completeness, candle freshness, plan geometry, TP1/TP2 and HTTP response shape.
- `test_align_pine_bridge_contract.py` verifies the canonical Pine identity and animation default, existing human alerts, opt-in export, all MTF timestamps and byte-identical original Pine outside the bridge blocks.
- Worker tests cover the TradingView IP gate, the three allowed markets, ticker-ID matching, mailbox expiry and authenticated mailbox reads.
- CI does not compile Pine in TradingView and cannot prove live webhook delivery. End-to-end success requires fresh snapshots for BTCUSD, XAUUSD and NAS100, a successful bridge preflight for all three, completed bot analysis, the expected Telegram behavior, and the resulting `live.json` / `state.json` persistence.
- A recent Python-generated `live.json` is not proof of Pine ingestion. Check the worker logs for `BRIDGE_CONFIRMED` per market and verify the timestamps before declaring recovery.
- The bridge and mailbox do not place broker orders. No real order is sent.
