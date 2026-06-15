---
noteId: "4bd2d38068a011f18c27c5ba47e2d819"
tags: []

---

# CropSmart Seminar Speaker Notes

## 1 Minute Introduction

Good morning respected sir/madam. My project name is CropSmart. It is a web-based crop price prediction system. The main purpose of this project is to show today's crop price and also predict the future price of crops for different regions.

Farmers, traders, and buyers often need to know crop prices before selling or purchasing. Crop prices change because of weather, demand, inflation, supply shortage, transport cost, and global risks. My project combines these factors and gives a simple dashboard output.

## Project Working

First, the user selects crop, country or region, currency, and forecast period. The frontend checks API version 2 and sends the request to the Python backend. The backend collects public signals such as weather, inflation, GDP, market benchmark data, and risk signals. If an exact market quote is available, the system uses it. Otherwise, it creates a clearly labeled live-signal estimate.

For crops with observed public benchmark history, the system loads up to 10 years of monthly closes. It trains a ridge autoregression using trend, seasonality, and lagged prices, validates it on the latest 6 to 12 months, and forecasts the next 24 months. For crops without a public historical series, it uses a labeled ridge scenario-model fallback.

The dashboard shows today's price, a 10-year historical chart, a 24-month forecast, confidence, holdout MAPE where available, main price drivers, model details, and data sources.

## Important Features

- Today live price or live-signal estimate
- Future predicted price for 1, 3, 6, 12, or 24 months
- Up to 10 years of observed benchmark history
- Chronological holdout validation and MAPE
- Global crops and regions
- Price driver explanation
- Confidence score
- CSV and JSON export

## Technology Used

I used HTML, CSS, and JavaScript for the frontend. I used Python for the API server, data collection, ridge models, validation, forecasting, and export. JSON cache files reduce repeated API calls, while CSV and model files store fallback training data and metadata.

## Model and Data

The application supports 22 crops and crop variants across 14 regions. The scenario fallback uses 19 features covering crop properties, region effects, market signals, risks, and seasonality. Its local dataset contains 36,960 generated feature rows, so it is useful for demonstrating the pipeline but is not a substitute for verified market records.

Observed benchmark forecasting requires at least 36 monthly prices. The model keeps the most recent 6 to 12 rows as a chronological holdout and reports MAPE and R2.

## Limitation

This system is a prediction model, so future prices are not guaranteed. Futures benchmarks are global reference prices, not exact local mandi or farmgate prices. Exact local prices require official datasets for each crop grade, location, unit, and date. Metrics from generated fallback data should not be presented as proof of real-market accuracy.

## Conclusion

This project helps users understand current crop prices, historical movement, and future estimates in a simple way. It can be improved by adding official Agmarknet or APMC data, more observed series, rolling backtests, uncertainty intervals, user accounts, maps, and price alerts.
