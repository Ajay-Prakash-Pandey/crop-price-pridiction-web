# CropSmart Exam Preparation Guide

## 1. Project Introduction

My project name is **CropSmart Global Crop Prices**. It is a web-based crop price prediction and market intelligence dashboard.

The user selects:

- Crop
- Region or country
- Currency
- Forecast period

The system then shows:

- Today's crop price or estimated live price
- Future predicted price
- 10-year historical price chart
- 24-month forecast chart
- Confidence score
- Price driver explanation
- CSV and JSON export

The main purpose is to help farmers, traders, buyers, and students understand how crop prices may change because of climate, demand, inflation, supply shortage, fuel cost, currency weakness, and global risks.

## 2. Technology Stack

### Frontend

- **HTML**: Page structure and input form
- **CSS**: Responsive design and dashboard styling
- **JavaScript**: User interaction, API calls, chart rendering, static fallback prediction, export handling

### Backend

- **Python**: Main backend language
- **http.server / ThreadingHTTPServer**: Lightweight local web server
- **JSON**: API response format, cache files, trained model storage
- **CSV**: Training data and export format

### Data Sources

- **Yahoo Finance**: Futures benchmark prices and 10-year monthly history for supported crops
- **World Bank API**: Inflation and GDP growth
- **Open-Meteo API**: Weather signals
- **GDELT API**: Conflict and risk signals

### Hosting

- **GitHub Pages**: Static demo hosting
- **Render**: Python backend hosting option

## 3. Main Files

- `index.html`: Main dashboard UI
- `styles.css`: Dashboard styling
- `app.js`: Frontend logic, API calls, chart rendering, static demo fallback
- `server.py`: Python API server and prediction endpoints
- `data_collector.py`: Collects live market, weather, economy, and risk signals
- `ml_model.py`: Machine learning prediction logic
- `train_model.py`: Builds fallback training data and trains the scenario model
- `data/trained_crop_price_model.json`: Saved trained model
- `data/market_history.json`: Cached market history
- `data/live_market_data.json`: Cached live signal data

## 4. System Flow

1. User opens the dashboard.
2. Frontend checks `/api/health` to confirm backend API version.
3. User selects crop, region, currency, and forecast period.
4. JavaScript sends a request to `/api/predict`.
5. Python backend builds a market scenario.
6. Backend collects or reads cached live signals.
7. If public historical benchmark data is available, the backend trains a time-series model.
8. If public history is not available, the backend uses the scenario ridge fallback model.
9. Backend returns today's price, forecast, history, confidence, sources, and model details.
10. Frontend renders charts, summary cards, factors, and export buttons.

## 5. Algorithm Used

The project uses **Ridge Regression** in two ways.

### A. Time-Series Ridge Autoregression

This is used when public benchmark history is available.

The model uses previous monthly prices to predict future monthly prices.

Features used:

- Trend
- Seasonality using sine and cosine
- Previous 1-month price lag
- Previous 3-month price lag
- Previous 12-month price lag

Steps:

1. Collect up to 10 years of monthly crop benchmark prices.
2. Clean the price series.
3. Create feature rows from previous prices.
4. Keep the latest 6 to 12 rows as holdout test data.
5. Train Ridge Regression on older rows.
6. Evaluate using MAPE and R2 score.
7. Predict future prices recursively for 24 months.

Simple explanation:

> The model learns price trend, seasonal behavior, and relation with previous months. Ridge regularization prevents overfitting by penalizing very large weights.

### B. Scenario Ridge Fallback Model

This is used when exact public historical data is not available.

Features used:

- Base crop price
- Region multiplier
- Crop volatility
- Climate risk
- Base demand
- Forecast period
- Inflation
- Currency weakness
- Demand growth
- Fuel cost
- War risk
- Supply shortage
- Climate effect
- Crop condition effect
- Economy effect
- Policy effect
- Live price ratio
- Seasonal sine
- Seasonal cosine

Target:

- Log crop price in USD

Why log price?

> Log price makes price changes more stable and helps the model handle crops with very different price ranges.

## 6. Why Ridge Regression?

Ridge Regression is used because:

- It is simple and explainable.
- It works well with many numeric features.
- It reduces overfitting using L2 regularization.
- It is suitable for an academic project where model logic must be clearly explained.
- It gives stable predictions even when some features are correlated.

Formula:

```text
Predicted value = intercept + w1*x1 + w2*x2 + ... + wn*xn
```

Ridge adds a penalty:

```text
Loss = Mean Squared Error + lambda * sum(weights^2)
```

## 7. Model Evaluation

The project uses:

- **MAPE**: Mean Absolute Percentage Error
- **R2 Score**: Explains how well predictions follow actual values
- **Chronological holdout**: The latest months are kept for testing

Important viva line:

> I used chronological holdout instead of random split because price data is time-based. Random split could leak future information into training.

## 8. API Endpoints

- `/`: Redirects to `index.html`
- `/api/health`: Checks backend status and API version
- `/api/options`: Returns supported crops, regions, and currencies
- `/api/predict`: Returns prediction result
- `/api/export`: Downloads CSV or JSON export

## 9. Supported Crops and Regions

The app supports 22 crops and crop variants, including:

- Wheat
- Rice
- Basmati rice
- Non-basmati rice
- Maize
- Soybean
- Cotton
- Sugarcane
- Potato
- Onion
- Tomato
- Coffee
- Cocoa
- Pulses
- Barley
- Rapeseed
- Sunflower
- Banana
- Apple

It supports 14 regions, including India, USA, Brazil, China, EU, Ukraine, Nigeria, Australia, Canada, Argentina, Russia, Thailand, Vietnam, and Indonesia.

## 10. Important Limitations

Be honest about limitations. This makes your answer stronger.

- It is a prediction system, not a guaranteed market oracle.
- Futures prices are benchmark prices, not exact local mandi prices.
- Exact local accuracy needs official crop-grade, mandi, date, and unit-level data.
- Some crops use fallback generated scenario data.
- Static GitHub Pages mode cannot call Python APIs.
- More real datasets would improve accuracy.

## 11. Future Scope

- Add official Agmarknet or APMC mandi datasets.
- Add user login and saved searches.
- Add price alerts through SMS or email.
- Add map-based regional price view.
- Add more real crop benchmark series.
- Add uncertainty intervals for best-case and worst-case predictions.
- Add mobile app version.

## 12. One-Minute Viva Answer

Good morning sir/madam. My project is CropSmart, a crop price prediction dashboard. It helps users see today's crop price and predict future prices for different crops, countries, currencies, and forecast periods.

The frontend is built using HTML, CSS, and JavaScript. The backend is built using Python. The backend collects live signals such as market benchmark price, weather, inflation, GDP, and conflict risk. For crops with public benchmark history, the system trains a ridge autoregression model using trend, seasonality, and previous price lags. For crops without public history, it uses a ridge scenario fallback model based on crop, region, climate, economy, demand, supply, and risk features.

The output includes current price, future forecast, 10-year history, 24-month chart, confidence score, model information, and CSV or JSON export. The model is evaluated using holdout MAPE and R2 score. The main limitation is that futures benchmarks are not exact local mandi prices, so official local datasets are needed for production-level accuracy.

## 13. Common Viva Questions and Answers

### Q1. What problem does your project solve?

It helps users estimate current and future crop prices using market data, region profile, weather, economic indicators, and risk signals.

### Q2. Which algorithm did you use?

I used Ridge Regression. For crops with benchmark history, I used ridge autoregression. For crops without benchmark history, I used a scenario-based ridge regression fallback.

### Q3. Why did you choose Ridge Regression?

Because it is explainable, stable, works with numeric features, and reduces overfitting using L2 regularization.

### Q4. What is autoregression?

Autoregression means predicting future values using previous values of the same variable. In this project, future crop price is predicted using previous monthly prices.

### Q5. What is seasonality?

Seasonality means repeating patterns over time. Crop prices often change during sowing, harvesting, storage, and demand seasons. I represent seasonality using sine and cosine features.

### Q6. What is MAPE?

MAPE means Mean Absolute Percentage Error. It shows average prediction error in percentage form.

### Q7. What is the backend used for?

The backend serves the website, collects live data, builds scenarios, runs prediction models, returns JSON responses, and exports CSV or JSON files.

### Q8. What happens if live APIs fail?

The project uses cached data when available. If exact live data is not available, it uses a clearly labeled fallback estimate.

### Q9. Is your prediction 100% accurate?

No. Crop prices depend on many uncertain factors. The system gives planning estimates, not guaranteed prices.

### Q10. How can the project be improved?

By adding official mandi data, more real historical series, rolling validation, uncertainty intervals, alerts, and user accounts.

## 14. Best Demo Steps

1. Run:

```powershell
python server.py
```

2. Open:

```text
http://localhost:8080/
```

3. Select a crop such as wheat or rice.
4. Select India and INR.
5. Change forecast period to 6 or 12 months.
6. Show today's price, forecast chart, historical chart, confidence, and price drivers.
7. Download CSV or JSON export.

## 15. Short Algorithm Explanation for Examiner

The algorithm first checks whether observed benchmark history exists for the selected crop. If yes, it builds a time-series dataset using trend, seasonal sine-cosine values, and lag prices. It trains Ridge Regression and validates it using the latest months as holdout data. Then it forecasts the next 24 months recursively.

If observed history is not available, the system builds a scenario feature vector using crop properties, region profile, inflation, currency weakness, fuel cost, demand, supply shortage, climate, policy, and risk. These features are standardized and passed into a saved ridge regression model to predict log price. The log prediction is converted back into normal price using exponentiation.

