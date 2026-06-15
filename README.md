---
noteId: "9d69bfd066f511f18c27c5ba47e2d819"
tags: []

---

# CropSmart Global Crop Prices

A browser-based crop price prediction and market intelligence dashboard. The user chooses the crop, region, currency, and forecast period. For crops with a public futures benchmark, the app downloads up to 10 years of observed monthly closes, trains a chronological ridge autoregression, validates it on a holdout period, and predicts the next 24 months.

## Run

For the full version with live web data collection, run:

```powershell
python server.py
```

Then open:

```text
http://localhost:8080/
```

You can also choose a port:

```powershell
python server.py 8082
```

Do not open `index.html` directly and do not use `python -m http.server`. Historical prices, future prices, live data, and exports require `server.py`.

If port `8080` is occupied by an older server, run:

```powershell
python server.py 8765
```

Then open `http://localhost:8765/`. The page checks API version 2 before loading prices or exports.

## Free Hosting

No-card free host: GitHub Pages. See `STATIC_FREE_HOSTING.md`.

GitHub Pages runs the static browser demo mode. It does not run Python, so live market APIs are unavailable, but forecasts, charts, and exports still work from saved assumptions.

Python backend host: Render Web Service.

This project includes `render.yaml`, so Render can detect the Python service automatically.

1. Push this folder to a GitHub repository.
2. Open Render and choose **New +** > **Blueprint**.
3. Connect your GitHub repository.
4. Select the repository and apply the blueprint.
5. After the deploy finishes, open the public `.onrender.com` URL.

Manual Render settings, if you do not use the blueprint:

- Runtime: Python
- Build command: `pip install -r requirements.txt`
- Start command: `python server.py`
- Plan: Free

The server reads Render's `PORT` environment variable automatically. For local development it still uses port `8080` by default.

## Files

- `index.html` contains the app layout.
- `styles.css` contains the responsive design.
- `app.js` contains the browser prediction logic and automatic market scenario selection.
- `server.py` runs the localhost app and prediction API.
- `data_collector.py` collects live public signals from web APIs and caches them in `data/live_market_data.json`.
- The app shows today's price and a future predicted price. Today's price is a direct public quote when available; otherwise it is a live-signal estimate from crop, region, weather, inflation, GDP, and risk data.
- The app creates a 24-month future price forecast, a 10-year historical price view, and CSV/JSON export.
- Both export formats include the current price, previous monthly prices, future monthly prices, source information, and model metadata.
- Supported benchmark crops use observed monthly market history and show holdout MAPE in the UI.
- Crops without a public historical series use an explicitly labeled scenario-model fallback.
- The dashboard includes crop quick-pick cards, global region options, trend bars, market assumptions, price drivers, and source quality notes.
- Rice includes separate options for basmati, non-basmati, paddy, parboiled, and broken rice. These use different model base prices; live benchmark quotes use rough rice futures unless an exact local source is added.
- `model.py` contains the same model idea in Python for future backend or training work.

## Important Note

This is not a market oracle. Futures benchmarks are global reference prices, not exact local mandi or farmgate prices. Exact local prices require an official data feed for the crop grade, market, date, and unit. The UI never labels generated fallback history as observed history.
