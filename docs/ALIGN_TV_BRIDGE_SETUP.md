# ALIGN canonical Pine v25 → ROBOT V12 bridge

## Scope

This bridge connects the **canonical production indicator** `align-bot/pine/ALIGN_MTF_PRO_v25.pine` (`ALIGN MTF PRO v25 (Inside)`) to the existing ALIGN MTF BOT preflight contract.

The only Pine changes are two isolated, opt-in bridge blocks:
- a settings group, disabled by default;
- a structured JSON export appended after the existing script.

The canonical indicator's existing source is protected by a regression test: after removing those two bridge blocks, its Git blob SHA must remain exactly `823635f039ff3b59c39867a7b59dfa3ed6fafaf1`. The title, short title, signal calculations, Entry/SL/TP1/TP2 logic, animation setting, chart drawings, table and existing human-readable alerts remain unchanged. No second indicator is introduced.

This service is isolated from the legacy `server.js`/port 4000 and from the `tradingview-analyzer` extension. Do not reuse the old project, its ports, or its Cloudflare tunnel.

## Data flow

1. One TradingView chart/alert is configured for each market: BTC, GOLD, NASDAQ.
2. In the canonical v25 indicator settings, enable **Envoyer les snapshots au ROBOT V12** and select exactly one market: `BTCUSD`, `XAUUSD`, or `NAS100`.
3. Create an alert with condition **Any alert() function call**. While the chart is receiving real-time updates, the bridge export sends a JSON snapshot every 20 seconds. Existing human-readable Pine alerts remain unchanged; the bridge ignores non-JSON alert messages.
4. The payload contains the active chart timeframe, actual TradingView price, the indicator's current Entry/SL/TP1/TP2 plan, confirmation state, and independent MTF direction/RSI/bar-time data for M1, M5, M15, M30, H1, H2, H4, D1 and W1.
5. The dedicated bridge validates the source, symbol, active timeframe, source timestamp, each timeframe's own candle timestamp, plan geometry and ingress token. It never places orders.
6. GitHub Actions reads `GET /bridge/robot-v12/mtf?symbol=...` using `ALIGN_TV_READ_TOKEN`. It blocks the bot if the active price or required M5/M15/H1/H4/D1/W1 snapshots are missing or stale.
7. The existing bot displays the indicator plan in Telegram separately from its own safety verdict. Once the existing bot run completes successfully, its publisher updates `live-data/live.json`; the ALIGN live band continues to read that file. The live band/userscript is not changed here.

## Local service

- Default listener: `127.0.0.1:4100`.
- Do not use ports 3000, 4000 or 5001; do not stop or repurpose their existing services.
- Python standard library only.
- Snapshots are held in memory. A restart clears the cache; the bot stays blocked until fresh TradingView alerts repopulate it.
- `/health` is a non-secret health check.
- `POST /ingest/<ALIGN_TV_INGEST_TOKEN>` accepts TradingView payloads. The token is checked in constant time and request paths are never logged.
- `GET /bridge/robot-v12/mtf?symbol=...` requires `Authorization: Bearer <ALIGN_TV_READ_TOKEN>`.

Generate two independent random tokens (32–128 URL-safe characters). They must be different. Never place either token in this repository, Pine source, logs or chat. The ingress token belongs only in the dedicated TradingView webhook URL and the bridge process environment. The read token belongs in the bridge process environment and the GitHub Actions secret `ALIGN_TV_READ_TOKEN`. Treat the full webhook URL as secret.

Start the service in a PowerShell session after setting the two environment variables in that session:

```powershell
$env:ALIGN_TV_INGEST_TOKEN = '<private ingress token>'
$env:ALIGN_TV_READ_TOKEN = '<different private read token>'
python .\align-bot\align_tv_bridge.py
```

Expose the service only through a **dedicated HTTPS tunnel/hostname** forwarding to `http://127.0.0.1:4100`. Do not expose port 4100 directly to the internet and do not reuse an existing tunnel configuration. Tunnel creation, DNS and credentials are intentionally not performed by this code change.

## TradingView configuration

For each market (BTC, GOLD, NASDAQ):

1. Add the canonical **ALIGN MTF PRO v25 (Inside)** indicator.
2. Open its settings and expand **Bridge ALIGN (optionnel)**.
3. Enable **Envoyer les snapshots au ROBOT V12**.
4. Set **Marché ALIGN** to the matching symbol: `BTCUSD`, `XAUUSD`, or `NAS100`.
5. Use an active chart timeframe supported by the bridge: M1, M5, M15, M30, H1, H2, H4, D1 or W1. The Pine retains its internal calculations for the other timeframes.
6. Create one alert per market with condition **Any alert() function call** and webhook URL:
   `https://<dedicated-https-host>/ingest/<ALIGN_TV_INGEST_TOKEN>`

The MTF readings are included in the same payload; separate alerts for each timeframe are not required.

## GitHub Actions secrets

Only after the dedicated HTTPS endpoint is running, set these repository Actions secrets:

- `ALIGN_TV_API_URL`: base HTTPS hostname, without `/bridge/robot-v12/mtf` and without the ingress token.
- `ALIGN_TV_READ_TOKEN`: the same read token configured in the bridge process.

The existing workflow already checks these secrets and validates BTCUSD, XAUUSD and NAS100, active price freshness (30 seconds), ROBOT V12 readings and required MTF freshness. No fallback to unrelated data sources is introduced.

## Validation and limits

- `test_align_tv_bridge.py` covers authentication, source/symbol/timeframe validation, MTF completeness, candle freshness, plan geometry, TP1/TP2 and HTTP response shape.
- `test_align_pine_bridge_contract.py` verifies the canonical Pine identity and animation default, existing human alerts, opt-in export, all MTF timestamps and byte-identical original Pine outside the bridge blocks.
- CI does not compile Pine in TradingView and cannot prove live webhook delivery. The final end-to-end test remains pending until the dedicated HTTPS tunnel, three TradingView alerts and GitHub secrets are configured.
- No broker order endpoint exists in this service. No real order is sent.
