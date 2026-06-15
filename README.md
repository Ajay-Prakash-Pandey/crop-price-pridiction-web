---
noteId: "9d69bfd066f511f18c27c5ba47e2d819"
tags: []

---

# AgriPredict Global Crop Prices

A browser-based crop price prediction and market intelligence dashboard inspired by mandi-rate sites such as AgriRate. The user chooses the crop, region, currency, and forecast period. The app shows today's price plus the future predicted price, fetches public market signals where available, explains the price drivers, and exports a 12-month forecast CSV.

## Run

For the full version with live web data collection, run:

```powershell
python server.py
```

Then open:

```text
http://localhost:8080/index.html
```

You can also choose a port:

```powershell
python server.py 8082
```

For the simple offline UI only, you can also run:

```powershell
python -m http.server 8000
```

Then open:

```text
http://localhost:8000/index.html
```

No installation is required for the user interface.

## Files

- `index.html` contains the app layout.
- `styles.css` contains the responsive design.
- `app.js` contains the browser prediction logic and automatic market scenario selection.
- `server.py` runs the localhost app and prediction API.
- `data_collector.py` collects live public signals from web APIs and caches them in `data/live_market_data.json`.
- The app shows today's price and a future predicted price. Today's price is a direct public quote when available; otherwise it is a live-signal estimate from crop, region, weather, inflation, GDP, and risk data.
- The app creates a 12-month future price forecast and CSV export.
- The dashboard includes crop quick-pick cards, global region options, trend bars, market assumptions, price drivers, and source quality notes.
- Rice includes separate options for basmati, non-basmati, paddy, parboiled, and broken rice. These use different model base prices; live benchmark quotes use rough rice futures unless an exact local source is added.
- `model.py` contains the same model idea in Python for future backend or training work.

## Important Note

This is a live-signal scenario model, not a perfect market oracle. Exact prices require verified local market, mandi, exchange, wholesale, or farmgate records for the exact crop grade, market, date, and unit. Some crops and varieties, such as onion, tomato, potato, pulses, and specific rice grades, may not have a public live futures benchmark, so the app will show a model forecast or benchmark-based estimate. For production accuracy, add verified historical local prices and train/validate the model on that dataset.
