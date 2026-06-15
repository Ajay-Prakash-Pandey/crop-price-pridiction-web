import json
import math
from pathlib import Path


MODEL_PATH = Path("data/trained_crop_price_model.json")


def predict_price_usd(crop, region, scenario, period, model_path=MODEL_PATH):
    model = load_model(model_path)
    features = build_features(crop, region, scenario, period)
    scaled = []
    for name in model["feature_names"]:
        value = features[name]
        mean = model["feature_means"][name]
        scale = model["feature_scales"][name] or 1
        scaled.append((value - mean) / scale)

    log_price = model["intercept"]
    log_price += sum(weight * value for weight, value in zip(model["weights"], scaled))
    return round(math.exp(log_price), 4)


def load_model(model_path=MODEL_PATH):
    with Path(model_path).open("r", encoding="utf-8") as file:
        return json.load(file)


def build_features(crop, region, scenario, period):
    live_price = scenario.get("liveData", {}).get("live_price_usd")
    model_base = crop["base"] * region["multiplier"]
    live_ratio = (live_price / model_base) if live_price else 1.0

    return {
        "base_price": crop["base"],
        "region_multiplier": region["multiplier"],
        "volatility": crop["volatility"],
        "climate_risk": crop["climateRisk"],
        "base_demand": crop["demand"],
        "period_months": period,
        "inflation": scenario["inflation"],
        "currency_weakness": scenario["currencyWeakness"],
        "demand_growth": scenario["demandGrowth"],
        "fuel_cost": scenario["fuelCost"],
        "war_risk": scenario["warRisk"],
        "supply_shortage": scenario["supplyShortage"],
        "climate_effect": scenario["effects"]["climate"],
        "crop_condition_effect": scenario["effects"]["cropCondition"],
        "economy_effect": scenario["effects"]["economy"],
        "policy_effect": scenario["effects"]["policy"],
        "live_price_ratio": live_ratio,
        "season_sin": math.sin((period % 12) * 2 * math.pi / 12),
        "season_cos": math.cos((period % 12) * 2 * math.pi / 12),
    }


def train_ridge_regression(rows, feature_names, learning_rate=0.03, epochs=4500, ridge=0.001):
    means = {
        name: sum(row[name] for row in rows) / len(rows)
        for name in feature_names
    }
    scales = {}
    for name in feature_names:
        variance = sum((row[name] - means[name]) ** 2 for row in rows) / len(rows)
        scales[name] = math.sqrt(variance) or 1

    weights = [0.0 for _ in feature_names]
    intercept = sum(row["target_log_price"] for row in rows) / len(rows)

    for _ in range(epochs):
        weight_grads = [0.0 for _ in feature_names]
        intercept_grad = 0.0

        for row in rows:
            values = [(row[name] - means[name]) / scales[name] for name in feature_names]
            prediction = intercept + sum(weight * value for weight, value in zip(weights, values))
            error = prediction - row["target_log_price"]
            intercept_grad += error
            for index, value in enumerate(values):
                weight_grads[index] += error * value

        count = len(rows)
        intercept -= learning_rate * intercept_grad / count
        for index in range(len(weights)):
            regularized_grad = (weight_grads[index] / count) + (ridge * weights[index])
            weights[index] -= learning_rate * regularized_grad

    metrics = evaluate(rows, feature_names, means, scales, intercept, weights)
    return {
        "model_type": "Ridge linear regression on log crop price",
        "target": "USD crop price",
        "feature_names": feature_names,
        "feature_means": means,
        "feature_scales": scales,
        "intercept": intercept,
        "weights": weights,
        "metrics": metrics,
    }


def evaluate(rows, feature_names, means, scales, intercept, weights):
    actual = []
    predicted = []
    for row in rows:
        values = [(row[name] - means[name]) / scales[name] for name in feature_names]
        log_prediction = intercept + sum(weight * value for weight, value in zip(weights, values))
        actual_price = math.exp(row["target_log_price"])
        predicted_price = math.exp(log_prediction)
        actual.append(actual_price)
        predicted.append(predicted_price)

    absolute_percent_errors = [
        abs(pred - real) / real
        for pred, real in zip(predicted, actual)
        if real
    ]
    mean_actual = sum(actual) / len(actual)
    ss_total = sum((value - mean_actual) ** 2 for value in actual)
    ss_residual = sum((pred - real) ** 2 for pred, real in zip(predicted, actual))
    r2 = 1 - (ss_residual / ss_total) if ss_total else 0

    return {
        "training_rows": len(rows),
        "mape_percent": round((sum(absolute_percent_errors) / len(absolute_percent_errors)) * 100, 2),
        "r2_score": round(r2, 4),
    }


def train_and_forecast_series(prices, months=24):
    """Train a ridge autoregression on chronological prices and forecast recursively."""
    clean = [float(value) for value in prices if value is not None and float(value) > 0]
    if len(clean) < 36:
        raise ValueError("at least 36 monthly prices are required")

    rows = _series_rows(clean)
    holdout_size = min(12, max(6, len(rows) // 5))
    train_rows = rows[:-holdout_size]
    test_rows = rows[-holdout_size:]
    model = _fit_series_ridge(train_rows)
    metrics = _evaluate_series(model, test_rows)

    values = list(clean)
    forecast = []
    for _ in range(months):
        month_index = len(values)
        features = _series_features(values, month_index)
        predicted_log = _series_predict(model, features)
        predicted = max(values[-1] * 0.65, min(values[-1] * 1.35, math.exp(predicted_log)))
        values.append(predicted)
        forecast.append(round(predicted, 4))

    return {
        "model_type": "Ridge autoregression with trend, seasonality, 1-month and 12-month lags",
        "training_rows": len(train_rows),
        "holdout_rows": len(test_rows),
        "metrics": metrics,
        "forecast": forecast,
    }


def _series_rows(prices):
    rows = []
    for index in range(12, len(prices)):
        rows.append((_series_features(prices[:index], index), math.log(prices[index])))
    return rows


def _series_features(previous, index):
    return [
        1.0,
        index / 120,
        math.sin((index % 12) * 2 * math.pi / 12),
        math.cos((index % 12) * 2 * math.pi / 12),
        math.log(previous[-1]),
        math.log(previous[-3] if len(previous) >= 3 else previous[-1]),
        math.log(previous[-12] if len(previous) >= 12 else previous[0]),
    ]


def _fit_series_ridge(rows, ridge=0.08):
    size = len(rows[0][0])
    matrix = [[0.0] * size for _ in range(size)]
    vector = [0.0] * size
    for features, target in rows:
        for i in range(size):
            vector[i] += features[i] * target
            for j in range(size):
                matrix[i][j] += features[i] * features[j]
    for index in range(1, size):
        matrix[index][index] += ridge
    return {"weights": _solve_linear_system(matrix, vector)}


def _solve_linear_system(matrix, vector):
    size = len(vector)
    augmented = [row[:] + [vector[index]] for index, row in enumerate(matrix)]
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(augmented[row][column]))
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        divisor = augmented[column][column]
        if abs(divisor) < 1e-12:
            raise ValueError("time-series model matrix is singular")
        augmented[column] = [value / divisor for value in augmented[column]]
        for row in range(size):
            if row == column:
                continue
            factor = augmented[row][column]
            augmented[row] = [
                current - factor * pivot_value
                for current, pivot_value in zip(augmented[row], augmented[column])
            ]
    return [augmented[index][-1] for index in range(size)]


def _series_predict(model, features):
    return sum(weight * value for weight, value in zip(model["weights"], features))


def _evaluate_series(model, rows):
    actual = [math.exp(target) for _, target in rows]
    predicted = [math.exp(_series_predict(model, features)) for features, _ in rows]
    mape = sum(abs(estimate - real) / real for estimate, real in zip(predicted, actual)) / len(actual)
    mean_actual = sum(actual) / len(actual)
    total = sum((value - mean_actual) ** 2 for value in actual)
    residual = sum((estimate - real) ** 2 for estimate, real in zip(predicted, actual))
    return {
        "holdout_mape_percent": round(mape * 100, 2),
        "holdout_r2_score": round(1 - residual / total, 4) if total else 0,
    }
