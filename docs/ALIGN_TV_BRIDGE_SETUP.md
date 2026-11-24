# ALIGN v25 → ROBOT V12 — canonical bridge routing

## Purpose and protected scope

The production Pine source is `align-bot/pine/ALIGN_MTF_PRO_v25.pine` (`ALIGN MTF PRO v25 (Inside)`). Its bridge export sends one JSON snapshot containing the active chart timeframe, price, current plan and independent MTF readings. It does not place or authorize broker orders.

The Pine title, calculations, Entry/SL/TP1/TP2 plan, animation setting, chart drawings, table and existing human-readable alerts are preserved. The bridge is a data-ingestion path only; it never sends broker orders.

This guide distinguishes the **default Cloudflare mailbox path** from the **optional external bridge path**. They are alternatives. Do not configure both as competing webhook routes for the same market.

## Canonical production path — Cloudflare mailbox → runner bridge

This is the path used by the standard `.github/workflows/align-bot.yml` run when the GitHub Actions secret `ALIGN_TV_API_URL` is not set and `CLOUDFLARE_API_TOKEN` is available.

1. **TradingView alert → Cloudflare Worker.** Create one alert for BTC and one for GOLD. Each alert posts to:

   `https://align-tv-mailbox.adel-khatra.workers.dev/ingest/tradingview`

   The Worker accepts this route from TradingView's allow-listed source IPs. No ingress token is appended to this URL in the standard mailbox mode.

2. **Worker mailbox.** `cloud/align-tv-mailbox/worker.js` checks the ALIGN source marker and the symbol/ticker match, then stores the latest payload in its Durable Object mailbox for that symbol. It is a mailbox, not the authoritative MTF validator.

3. **GitHub Actions runner.** The workflow creates per-run ingress/read tokens, starts exactly one `align_tv_bridge.py` listener on `127.0.0.1:4100`, then starts `align_tv_mailbox_feeder.py`. The feeder reads BTCUSD and XAUUSD from the Worker mailbox every 10 seconds and forwards the payload unchanged to that runner-local bridge.

4. **Single authoritative bridge validation.** `align_tv_bridge.py` validates the payload and maintains the in-memory snapshots for that workflow run. Its read endpoint is `GET /bridge/robot-v12/mtf?symbol=...`, protected by `ALIGN_TV_READ_TOKEN`. The listener is temporary on the GitHub Actions runner; it is not a permanent desktop service and does not need a public tunnel in this mode.

5. **ROBOT V12 and Telegram.** `align_bot.py` reads the runner-local bridge endpoint. Missing, incomplete or stale TradingView data keeps entries fail-closed: the bot must not substitute local/fabricated prices or plans. Telegram connectivity does not override this signal gate.

The feeder does not transform or repair snapshots, and the Worker does not replace the bridge validator. There is one validation point: `align_tv_bridge.py` in the runner.

### Required GitHub Actions configuration for the default path

- `CLOUDFLARE_API_TOKEN`: required by the workflow to derive the mailbox read token and start the feeder.
- `ALIGN_TV_API_URL`: leave unset to select this default Worker → runner path.
- `ALIGN_TV_READ_TOKEN`: not required as a persistent repository secret for the default path; the workflow creates a per-run read token for its runner-local bridge.
- The Worker must have its mailbox Durable Object binding and the expected Worker secrets configured. Never print or copy secrets into Pine, the repository, alert messages or chat.

Do not install another permanent bridge on the desktop for this workflow. Do not point TradingView at `127.0.0.1`, a local port, the legacy port 4000, or an unrelated service.

## Optional alternative — a dedicated external bridge

Use this mode only when an independently operated HTTPS bridge already exists and is intentionally selected for production.

- Set GitHub Actions secrets `ALIGN_TV_API_URL` (the external bridge base URL) and `ALIGN_TV_READ_TOKEN` (the read token accepted by that bridge).
- The workflow then skips starting the default Worker mailbox feeder and runner-local bridge, and reads the external service through `GET /bridge/robot-v12/mtf?symbol=...`.
- TradingView must post to that external bridge's dedicated HTTPS ingress route, for example `https://<dedicated-host>/ingest/<private-ingress-token>`, using a separate ingress token. The external service must implement the same snapshot and read contracts as the canonical ALIGN bridge.
- Keep the ingress token and read token separate. Never expose the read token in the TradingView webhook URL.
- The external host/tunnel must be dedicated to this bridge. Do not reuse or repurpose another server or tunnel.

Choose one mode for the production bot. Setting `ALIGN_TV_API_URL` changes the workflow path; it is not an extra forwarding hop to be added on top of the default mailbox path.

## TradingView configuration — BTC and GOLD only

For each market, use the canonical **ALIGN MTF PRO v25 (Inside)** instance:

1. Use a BTCUSD chart for BTC, or an XAUUSD chart for GOLD. The actual chart ticker and the indicator's **Marché ALIGN** input must represent the same market. Never set `XAUUSD` on a BTCUSD chart or `BTCUSD` on an XAUUSD chart.
2. Enable **Envoyer les snapshots au ROBOT V12**.
3. Set **Marché ALIGN** to `BTCUSD` or `XAUUSD`, matching that chart.
4. Use a ROBOT V12 supported active chart timeframe: `M1`, `M5`, `M15`, `M30`, `H1`, `H2`, `H4`, `D1` or `W1`. The payload still carries independent MTF readings for all 12 timeframes; `M3`, `M10` and `M45` are MTF inputs, not supported active chart contexts for the current bot/preflight.
5. Create one alert per market with condition **Any alert() function call**. In the default mailbox mode, use the Worker URL shown in the canonical production path above. Do not create one webhook alert per timeframe.

The payload contains independent readings and candle timestamps for all 12 timeframes: M1, M3, M5, M10, M15, M30, M45, H1, H2, H4, D1 and W1. Separate alerts for each timeframe are not required.

Attach the bridge alert to the **v25** indicator instance. The legacy `ALIGN MTF PRO (Inside)` / `ALIGN MTF` indicator is not a second bridge and must not be confused with the canonical v25 snapshot exporter.

**TradingView alert snapshots:** TradingView retains the script version, inputs and chart context captured when an alert is created. After changing the Pine script, the bridge checkbox, market input, chart symbol or webhook route, delete and recreate only the corresponding ALIGN BTC or GOLD alert. An existing alert does not automatically inherit later Pine changes.

## Bridge isolation and ports

- The default workflow bridge listens on `127.0.0.1:4100` **inside the GitHub Actions runner**.
- Its snapshots are held in memory for that run. A new run starts with an empty cache and must wait for fresh TradingView payloads.
- Ports `3000`, `4000` and `5001` are forbidden for this bridge. In particular, do not touch, stop, reuse or redirect the legacy server on port `4000`.
- The Cloudflare Worker is only the mailbox layer in the default path. Do not add a second bridge between the mailbox feeder and the runner bridge.
- Do not reuse the `tradingview-analyzer` extension, historical project copies, or unrelated server instances as an ALIGN bridge.

## ROBOT V12 validation and safety

The bridge validates source, supported market, active timeframe, source timestamp, the active price and the independent MTF readings/bar times. It also validates the plan and the strategy-specific closed trigger candle. Production requires fresh M5, M15, H1, H4, D1 and W1 snapshots, a fresh supported active timeframe, a valid price and usable ROBOT V12 readings; the bridge also enforces its complete MTF contract.

When `ALIGN_REQUIRE_TV_BRIDGE=1`, ROBOT V12 does not fall back to locally generated entry levels. It uses the Pine M15 Entry/SL/TP1/TP2 only after the validated trigger. Existing news, Daily/Weekly extreme, risk/reward and risk-memory filters remain mandatory vetoes. No broker order is sent.

## Validation and limits

- `align-bot/test_align_tv_bridge.py` covers authentication, source/symbol/timeframe validation, MTF completeness, candle freshness, plan geometry, TP1/TP2 and HTTP response shape.
- `align-bot/test_align_pine_bridge_contract.py` verifies the canonical Pine identity and animation default, existing human alerts, bridge export and MTF timestamps.
- CI does not compile Pine in TradingView and cannot prove that the two active server-side TradingView alerts are current or delivering.
- End-to-end production validation requires fresh BTCUSD and XAUUSD snapshots from the intended alert route, bridge confirmation for both symbols, a successful ROBOT V12 run and a fresh `live-data/live.json` publication.
- No real broker orders are placed by this bridge.
