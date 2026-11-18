# ALIGN TradingView → ROBOT V12 bridge

## Scope

This bridge connects the recovered `ALIGN MTF PRO (Inside)` indicator (the A file with progressive FVG consumption) to the existing ALIGN MTF BOT preflight contract. It is a separate service; it does not reuse `server.js` on port 4000 or the `tradingview-analyzer` extension, which belongs to the legacy Trading Auto project.

The Pine file added with this bridge is `align-bot/pine/ALIGN_MTF_PRO_INSIDE_FVG_EVOLUTIVE.pine`. It is the recovered A source (original upload SHA-256: `b9041d455f0a3c6d7110e25a7fe1bc1f13636f4efd3e8a082c67d29243cb06ca`) plus only the bridge input group and structured alert block. Its indicator title, existing human-readable alerts, table, animation settings, FVG box reduction, proximity recoloring, and OB/FVG drawings are preserved. The bridge is opt-in and disabled by default.

## Data flow

1. One TradingView alert is configured for each market: BTC, GOLD, NASDAQ.
2. Each alert uses **Any alert() function call**. The script sends a structured JSON snapshot every 20 seconds while the chart is receiving real-time updates. Existing human-readable alert messages remain; the bridge ignores those non-JSON messages.
3. The payload includes the active chart timeframe, current TradingView price, Entry/SL/TP1/TP2, confirmation state, RSI and direction readings, and the six required higher-timeframe snapshots (M5, M15, H1, H4, D1, W1).
4. The dedicated bridge validates the source, symbol, timeframe, timestamp, MTF values, plan geometry, and ingress token. It never places orders.
5. GitHub Actions reads `GET /bridge/robot-v12/mtf?symbol=...` using `ALIGN_TV_READ_TOKEN` and blocks the bot if the active price or required snapshots are missing or stale.
6. Once the existing bot run completes successfully, its existing publisher updates `live-data/live.json`; the ALIGN live band continues to read that file. The band/userscript is not changed here.

## Local service

- Default listener: `127.0.0.1:4100`.
- Do not use ports 3000, 4000, or 5001; do not stop or repurpose their existing services.
- The service uses only the Python standard library.
- It keeps snapshots in memory. A restart clears the cache; the bot correctly remains blocked until fresh TradingView alerts repopulate it.
- `/health` is a non-secret health check.
- `POST /ingest/<ALIGN_TV_INGEST_TOKEN>` accepts the TradingView payload. The token is checked in constant time and the URL path is never written to logs.
- `GET /bridge/robot-v12/mtf?symbol=...` requires `Authorization: Bearer <ALIGN_TV_READ_TOKEN>`.

Both tokens must be independently generated random values of 32–128 URL-safe characters and must be different. Never put either token in this repository, a Pine source file, a log, or a chat message. The ingress token is entered only in the dedicated TradingView webhook URL and the bridge process environment. Treat the full webhook URL as secret; configure the HTTPS tunnel not to log full request paths. The read token is entered in the bridge process environment and the GitHub Actions secret `ALIGN_TV_READ_TOKEN`.

Start the service in a PowerShell session after setting the two environment variables in that session:

```powershell
$env:ALIGN_TV_INGEST_TOKEN = '<private ingress token>'
$env:ALIGN_TV_READ_TOKEN = '<different private read token>'
python .\align-bot\align_tv_bridge.py
```

The bridge must be exposed only through a **dedicated HTTPS tunnel/hostname** forwarding to `http://127.0.0.1:4100`. Do not expose port 4100 directly to the internet and do not reuse an existing tunnel configuration. Tunnel creation, DNS, and credentials are intentionally not performed by this code change.

## TradingView configuration

For each of the three markets:

1. Add `ALIGN MTF PRO (Inside)` from the bridge-enabled Pine file.
2. In the indicator settings, enable **Envoyer les snapshots au ROBOT V12**.
3. Set **Marché ALIGN** to exactly one of `BTCUSD`, `XAUUSD`, or `NAS100` for that chart.
4. Use an active chart timeframe supported by the current bot contract: M1, M5, M15, M30, H1, H2, H4, D1, or W1. The indicator's internal 3m, 10m, and 45m calculations remain visible, but those three are not valid active chart timeframes for this bridge contract.
5. Create an alert with condition **Any alert() function call** and enable the webhook URL:
   `https://<dedicated-https-host>/ingest/<ALIGN_TV_INGEST_TOKEN>`

Use one alert per symbol for the chosen active chart timeframe. The script sends the internal MTF readings in the same payload, so the required higher-timeframe snapshots do not need separate chart alerts.

## GitHub Actions secrets

Set these repository Actions secrets only after the dedicated HTTPS endpoint is running:

- `ALIGN_TV_API_URL`: the base HTTPS hostname, without `/bridge/robot-v12/mtf` and without the ingress token.
- `ALIGN_TV_READ_TOKEN`: the same read token configured in the local bridge environment.

The existing workflow already checks these secrets and validates all three symbols, active price freshness (30 seconds), ROBOT V12 readings, and the six required higher-timeframe snapshots. No workflow fallback to another data source is introduced.

## Validation and limits

- `test_align_tv_bridge.py` exercises authentication, freshness, symbol/timeframe validation, snapshot completeness, plan geometry, TP1/TP2, and response shape.
- `test_align_pine_bridge_contract.py` checks that the original A indicator identity, animation settings, human alerts, and progressive FVG behavior remain present alongside the opt-in bridge payload.
- These tests do **not** replace compiling the bridge-enabled Pine file in TradingView and confirming three live webhook deliveries. That final end-to-end check remains pending until the user configures the dedicated HTTPS tunnel, the three TradingView alerts, and the GitHub secrets.
- No broker order endpoint exists in this service. No real order is sent.