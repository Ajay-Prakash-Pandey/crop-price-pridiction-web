import csv
import json
import math
from pathlib import Path

from ml_model import build_features, train_ridge_regression
from server import CROPS, EFFECTS, REGIONS, math_sin


DATA_DIR = Path("data")
TRAINING_DATA_PATH = DATA_DIR / "historical_crop_prices.csv"
MODEL_PATH = DATA_DIR / "trained_crop_price_model.json"


def main():
    DATA_DIR.mkdir(exist_ok=True)
    rows = build_training_rows()
    write_training_csv(rows)
    feature_names = [name for name in rows[0] if name != "target_log_price"]
    model = train_ridge_regression(rows, feature_names)
    model["training_data"] = str(TRAINING_DATA_PATH)
    model["note"] = (
        "Trained locally from 10 years of monthly historical-style crop, region, climate, economy, "
        "risk, seasonality, and market-signal samples. Replace the CSV with "
        "verified mandi/market records to improve production accuracy."
    )

    with MODEL_PATH.open("w", encoding="utf-8") as file:
        json.dump(model, file, indent=2)

    print(f"Training rows: {model['metrics']['training_rows']}")
    print(f"MAPE: {model['metrics']['mape_percent']}%")
    print(f"R2 score: {model['metrics']['r2_score']}")
    print(f"Saved model: {MODEL_PATH}")


def build_training_rows():
    rows = []
    climates = ["normal", "drought", "flood", "cold", "excellent"]
    crop_conditions = ["excellent", "good", "average", "poor", "damaged"]
    economies = ["strong", "stable", "weak", "recession"]
    policies = ["support", "neutral", "exportBan", "importOpen", "taxIncrease"]

    for crop_index, (crop_key, crop) in enumerate(CROPS.items()):
        for region_index, (region_key, region) in enumerate(REGIONS.items()):
            for month_index in range(120):
                period = (month_index % 12) + 1
                climate = climates[(month_index + crop_index + region_index) % len(climates)]
                crop_condition = crop_conditions[(month_index + crop_index * 2) % len(crop_conditions)]
                economy = economies[(month_index + region_index) % len(economies)]
                policy = policies[(month_index + crop_index + region_index * 2) % len(policies)]
                profile = region["profile"]
                scenario = {
                    "climate": climate,
                    "cropCondition": crop_condition,
                    "economy": economy,
                    "policy": policy,
                    "inflation": bounded(profile["inflation"] + wave(month_index, 0.025, crop_index), 0.00, 0.36),
                    "currencyWeakness": bounded(profile["currency"] + wave(month_index + 2, 0.035, region_index), 0.00, 0.42),
                    "demandGrowth": bounded(crop["demand"] + wave(month_index + 4, 0.025, crop_index), -0.08, 0.24),
                    "fuelCost": bounded(profile["fuel"] + wave(month_index + 1, 0.035, region_index), 0.01, 0.38),
                    "warRisk": bounded(profile["war"] + wave(month_index + 3, 0.03, region_index), 0.00, 0.70),
                    "supplyShortage": bounded(profile["shortage"] + crop["climateRisk"] + wave(month_index + 5, 0.05, crop_index), 0.02, 0.72),
                    "liveData": {"live_price_usd": None},
                }
                scenario["effects"] = effect_values(scenario)
                target_price = synthetic_historical_price(crop, region, scenario, period, month_index)
                row = build_features(crop, region, scenario, period)
                row["target_log_price"] = math.log(max(0.01, target_price))
                rows.append(row)

    return rows


def synthetic_historical_price(crop, region, scenario, period, month_index):
    effects = scenario["effects"]
    total_effect = (
        effects["climate"]
        + effects["cropCondition"]
        + effects["economy"]
        + effects["policy"]
        + scenario["inflation"] * 0.50
        + scenario["currencyWeakness"] * 0.35
        + scenario["demandGrowth"] * 0.45
        + scenario["fuelCost"] * 0.28
        + scenario["warRisk"] * 0.22
        + scenario["supplyShortage"] * 0.62
        + period * crop["volatility"] * 0.015
    )
    seasonal = crop["volatility"] * 0.035 * math_sin(period)
    market_noise = wave(month_index, crop["volatility"] * 0.025, int(crop["base"]))
    return crop["base"] * region["multiplier"] * max(0.35, 1 + total_effect + seasonal + market_noise)


def effect_values(scenario):
    return {
        "climate": EFFECTS["climate"][scenario["climate"]],
        "cropCondition": EFFECTS["cropCondition"][scenario["cropCondition"]],
        "economy": EFFECTS["economy"][scenario["economy"]],
        "policy": EFFECTS["policy"][scenario["policy"]],
    }


def write_training_csv(rows):
    with TRAINING_DATA_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def wave(index, amplitude, offset):
    return math.sin((index + offset) * 1.618) * amplitude


def bounded(value, minimum, maximum):
    return max(minimum, min(maximum, value))


if __name__ == "__main__":
    main()
