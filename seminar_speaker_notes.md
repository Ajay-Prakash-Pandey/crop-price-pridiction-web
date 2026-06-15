---
noteId: "4bd2d38068a011f18c27c5ba47e2d819"
tags: []

---

# AgriPredict Seminar Speaker Notes

## 1 Minute Introduction

Good morning respected sir/madam. My project name is AgriPredict. It is a web-based crop price prediction system. The main purpose of this project is to show today's crop price and also predict the future price of crops for different regions.

Farmers, traders, and buyers often need to know crop prices before selling or purchasing. Crop prices change because of weather, demand, inflation, supply shortage, transport cost, and global risks. My project combines these factors and gives a simple dashboard output.

## Project Working

First, the user selects crop, country or region, currency, and forecast period. Then the frontend sends this input to the Python backend. The backend collects live public signals such as weather, inflation, GDP, market benchmark data, and risk signals. If exact market quote is available, the system uses it. If exact quote is not available, it creates a live-signal estimate.

After that, the prediction model applies weighted market factors and calculates the future predicted price. The dashboard shows today's price, future predicted price, confidence score, 12-month forecast chart, main price drivers, and data sources.

## Important Features

- Today live price or live-signal estimate
- Future predicted price for 1, 3, 6, or 12 months
- Global crops and regions
- Price driver explanation
- Confidence score
- CSV export

## Technology Used

I used HTML, CSS, and JavaScript for the frontend. I used Python for the backend server and prediction API. The data collector file collects public data signals and stores recent data in a JSON cache.

## Limitation

This system is a prediction model, so future prices are not guaranteed. Exact local prices require official mandi or market datasets for each crop grade, location, and date.

## Conclusion

This project helps users understand current crop price and future price movement in a simple way. It can be improved further by adding official mandi datasets, machine learning training, user login, maps, and price alerts.
