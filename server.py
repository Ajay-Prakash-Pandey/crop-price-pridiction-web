import json
import csv
import io
import math
import os
import sys
from datetime import date
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from data_collector import collect_market_history, collect_market_signals
from ml_model import predict_price_usd, train_and_forecast_series


API_VERSION = 2


CROPS = {
    "wheat": {"name": "Wheat", "base": 265, "unit": "per tonne", "volatility": 0.16, "climateRisk": 0.12, "demand": 0.08},
    "rice": {"name": "Rice", "base": 420, "unit": "per tonne", "volatility": 0.13, "climateRisk": 0.10, "demand": 0.10},
    "rice_basmati": {"name": "Rice - Basmati", "base": 950, "unit": "per tonne", "volatility": 0.18, "climateRisk": 0.11, "demand": 0.12},
    "rice_non_basmati": {"name": "Rice - Non-basmati", "base": 430, "unit": "per tonne", "volatility": 0.14, "climateRisk": 0.10, "demand": 0.10},
    "rice_paddy": {"name": "Rice - Paddy", "base": 280, "unit": "per tonne", "volatility": 0.15, "climateRisk": 0.12, "demand": 0.09},
    "rice_parboiled": {"name": "Rice - Parboiled", "base": 470, "unit": "per tonne", "volatility": 0.14, "climateRisk": 0.10, "demand": 0.10},
    "rice_broken": {"name": "Rice - Broken", "base": 360, "unit": "per tonne", "volatility": 0.17, "climateRisk": 0.10, "demand": 0.08},
    "maize": {"name": "Maize", "base": 230, "unit": "per tonne", "volatility": 0.18, "climateRisk": 0.14, "demand": 0.09},
    "soybean": {"name": "Soybean", "base": 510, "unit": "per tonne", "volatility": 0.20, "climateRisk": 0.13, "demand": 0.08},
    "cotton": {"name": "Cotton", "base": 1720, "unit": "per bale", "volatility": 0.22, "climateRisk": 0.12, "demand": 0.05},
    "sugarcane": {"name": "Sugarcane", "base": 42, "unit": "per tonne", "volatility": 0.11, "climateRisk": 0.08, "demand": 0.06},
    "potato": {"name": "Potato", "base": 190, "unit": "per tonne", "volatility": 0.24, "climateRisk": 0.11, "demand": 0.07},
    "onion": {"name": "Onion", "base": 310, "unit": "per tonne", "volatility": 0.32, "climateRisk": 0.16, "demand": 0.08},
    "tomato": {"name": "Tomato", "base": 360, "unit": "per tonne", "volatility": 0.35, "climateRisk": 0.18, "demand": 0.07},
    "coffee": {"name": "Coffee", "base": 4250, "unit": "per tonne", "volatility": 0.25, "climateRisk": 0.15, "demand": 0.06},
    "cocoa": {"name": "Cocoa", "base": 7600, "unit": "per tonne", "volatility": 0.30, "climateRisk": 0.17, "demand": 0.06},
    "pulses": {"name": "Pulses", "base": 760, "unit": "per tonne", "volatility": 0.19, "climateRisk": 0.12, "demand": 0.11},
    "barley": {"name": "Barley", "base": 235, "unit": "per tonne", "volatility": 0.17, "climateRisk": 0.11, "demand": 0.06},
    "rapeseed": {"name": "Rapeseed / Canola", "base": 535, "unit": "per tonne", "volatility": 0.21, "climateRisk": 0.13, "demand": 0.07},
    "sunflower": {"name": "Sunflower seed", "base": 470, "unit": "per tonne", "volatility": 0.23, "climateRisk": 0.14, "demand": 0.07},
    "banana": {"name": "Banana", "base": 560, "unit": "per tonne", "volatility": 0.18, "climateRisk": 0.16, "demand": 0.08},
    "apple": {"name": "Apple", "base": 980, "unit": "per tonne", "volatility": 0.20, "climateRisk": 0.14, "demand": 0.06},
}

REGIONS = {
    "india": {"name": "India", "multiplier": 0.82, "fx": {"USD": 1, "INR": 83, "EUR": 0.92, "GBP": 0.78}, "profile": {"climate": "normal", "economy": "stable", "policy": "support", "inflation": 0.06, "currency": 0.10, "fuel": 0.12, "war": 0.08, "shortage": 0.16}},
    "usa": {"name": "United States", "multiplier": 1.08, "fx": {"USD": 1, "INR": 83, "EUR": 0.92, "GBP": 0.78}, "profile": {"climate": "normal", "economy": "strong", "policy": "neutral", "inflation": 0.03, "currency": 0.03, "fuel": 0.06, "war": 0.05, "shortage": 0.09}},
    "brazil": {"name": "Brazil", "multiplier": 0.94, "fx": {"USD": 1, "INR": 83, "EUR": 0.92, "GBP": 0.78}, "profile": {"climate": "drought", "economy": "stable", "policy": "neutral", "inflation": 0.05, "currency": 0.12, "fuel": 0.10, "war": 0.06, "shortage": 0.13}},
    "china": {"name": "China", "multiplier": 1.02, "fx": {"USD": 1, "INR": 83, "EUR": 0.92, "GBP": 0.78}, "profile": {"climate": "normal", "economy": "stable", "policy": "neutral", "inflation": 0.02, "currency": 0.04, "fuel": 0.07, "war": 0.09, "shortage": 0.11}},
    "eu": {"name": "European Union", "multiplier": 1.16, "fx": {"USD": 1, "INR": 83, "EUR": 0.92, "GBP": 0.78}, "profile": {"climate": "cold", "economy": "stable", "policy": "support", "inflation": 0.03, "currency": 0.04, "fuel": 0.09, "war": 0.11, "shortage": 0.10}},
    "ukraine": {"name": "Ukraine", "multiplier": 0.78, "fx": {"USD": 1, "INR": 83, "EUR": 0.92, "GBP": 0.78}, "profile": {"climate": "normal", "economy": "weak", "policy": "neutral", "inflation": 0.09, "currency": 0.20, "fuel": 0.18, "war": 0.58, "shortage": 0.27}},
    "nigeria": {"name": "Nigeria", "multiplier": 0.74, "fx": {"USD": 1, "INR": 83, "EUR": 0.92, "GBP": 0.78}, "profile": {"climate": "drought", "economy": "weak", "policy": "importOpen", "inflation": 0.16, "currency": 0.28, "fuel": 0.22, "war": 0.23, "shortage": 0.30}},
    "australia": {"name": "Australia", "multiplier": 1.12, "fx": {"USD": 1, "INR": 83, "EUR": 0.92, "GBP": 0.78}, "profile": {"climate": "excellent", "economy": "strong", "policy": "neutral", "inflation": 0.03, "currency": 0.04, "fuel": 0.07, "war": 0.04, "shortage": 0.08}},
    "canada": {"name": "Canada", "multiplier": 1.10, "fx": {"USD": 1, "INR": 83, "EUR": 0.92, "GBP": 0.78}, "profile": {"climate": "cold", "economy": "strong", "policy": "neutral", "inflation": 0.03, "currency": 0.04, "fuel": 0.08, "war": 0.04, "shortage": 0.09}},
    "argentina": {"name": "Argentina", "multiplier": 0.88, "fx": {"USD": 1, "INR": 83, "EUR": 0.92, "GBP": 0.78}, "profile": {"climate": "drought", "economy": "weak", "policy": "taxIncrease", "inflation": 0.18, "currency": 0.32, "fuel": 0.16, "war": 0.04, "shortage": 0.18}},
    "russia": {"name": "Russia", "multiplier": 0.84, "fx": {"USD": 1, "INR": 83, "EUR": 0.92, "GBP": 0.78}, "profile": {"climate": "cold", "economy": "stable", "policy": "neutral", "inflation": 0.07, "currency": 0.16, "fuel": 0.12, "war": 0.42, "shortage": 0.17}},
    "thailand": {"name": "Thailand", "multiplier": 0.90, "fx": {"USD": 1, "INR": 83, "EUR": 0.92, "GBP": 0.78}, "profile": {"climate": "normal", "economy": "stable", "policy": "support", "inflation": 0.03, "currency": 0.07, "fuel": 0.10, "war": 0.05, "shortage": 0.11}},
    "vietnam": {"name": "Vietnam", "multiplier": 0.86, "fx": {"USD": 1, "INR": 83, "EUR": 0.92, "GBP": 0.78}, "profile": {"climate": "normal", "economy": "strong", "policy": "support", "inflation": 0.04, "currency": 0.07, "fuel": 0.10, "war": 0.04, "shortage": 0.10}},
    "indonesia": {"name": "Indonesia", "multiplier": 0.91, "fx": {"USD": 1, "INR": 83, "EUR": 0.92, "GBP": 0.78}, "profile": {"climate": "normal", "economy": "stable", "policy": "support", "inflation": 0.04, "currency": 0.08, "fuel": 0.11, "war": 0.05, "shortage": 0.13}},
}

EFFECTS = {
    "climate": {"normal": 0, "drought": 0.18, "flood": 0.15, "cold": 0.08, "excellent": -0.08},
    "cropCondition": {"excellent": -0.09, "good": -0.03, "average": 0.03, "poor": 0.14, "damaged": 0.27},
    "economy": {"strong": 0.06, "stable": 0, "weak": -0.04, "recession": -0.09},
    "policy": {"support": 0.08, "neutral": 0, "exportBan": -0.10, "importOpen": -0.07, "taxIncrease": 0.07},
}


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.send_response(302)
            self.send_header("Location", "/index.html")
            self.end_headers()
            return
        if parsed.path == "/api/predict":
            self._handle_predict(parse_qs(parsed.query))
            return
        if parsed.path == "/api/options":
            self._json(200, options_payload())
            return
        if parsed.path == "/api/health":
            self._json(200, {"status": "ok", "apiVersion": API_VERSION})
            return
        if parsed.path == "/api/export":
            self._handle_export(parse_qs(parsed.query))
            return
        return super().do_GET()

    def _handle_predict(self, query):
        crop_key = query.get("crop", ["wheat"])[0]
        region_key = query.get("region", ["india"])[0]
        currency = query.get("currency", ["INR"])[0]
        period = int(query.get("period", ["3"])[0])

        try:
            payload = predict(crop_key, region_key, currency, period)
            self._json(200, payload)
        except (KeyError, ValueError) as exc:
            self._json(400, {"error": str(exc)})
        except Exception as exc:
            self._json(500, {"error": str(exc)})

    def _handle_export(self, query):
        crop_key = query.get("crop", ["wheat"])[0]
        region_key = query.get("region", ["india"])[0]
        currency = query.get("currency", ["INR"])[0]
        period = int(query.get("period", ["3"])[0])
        export_format = query.get("format", ["csv"])[0].lower()
        payload = predict(crop_key, region_key, currency, period)

        if export_format == "json":
            export_payload = build_export_payload(payload, period)
            body = json.dumps(export_payload, indent=2).encode("utf-8")
            self._download(
                body,
                "application/json; charset=utf-8",
                f"{crop_key}-{region_key}-prices.json",
            )
            return
        if export_format != "csv":
            self._json(400, {"error": "format must be csv or json"})
            return

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["crop", "region", "date_or_period", "price", "currency", "unit", "price_type", "source", "confidence_percent"])
        writer.writerow([payload["crop"], payload["region"], "today", payload["todayPrice"]["price"], currency, payload["unit"], payload["todayPrice"]["type"], payload["todayPrice"]["source"], payload["confidence"]])
        writer.writerow([payload["crop"], payload["region"], f'{period}_months', payload["price"], currency, payload["unit"], "future_forecast", payload["modelInfo"]["type"], payload["confidence"]])
        for item in payload["historical10Years"]:
            price_type = "observed_benchmark" if item.get("observed") else "historical_model_fallback"
            writer.writerow([payload["crop"], payload["region"], item["date"], item["price"], item["currency"], payload["unit"], price_type, payload["historySource"], payload["confidence"]])
        for item in payload["forecast24Months"]:
            writer.writerow([payload["crop"], payload["region"], item["date"], item["price"], item["currency"], payload["unit"], "monthly_forecast", payload["modelInfo"]["type"], payload["confidence"]])

        body = output.getvalue().encode("utf-8")
        self._download(
            body,
            "text/csv; charset=utf-8",
            f"{crop_key}-{region_key}-prices.csv",
        )

    def _download(self, body, content_type, filename):
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class ExclusiveThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = False


def build_export_payload(payload, selected_period):
    return {
        "metadata": {
            "crop": payload["crop"],
            "region": payload["region"],
            "currency": payload["currency"],
            "unit": payload["unit"],
            "selected_forecast_months": selected_period,
            "confidence_percent": payload["confidence"],
            "history_type": payload["historyType"],
            "history_source": payload["historySource"],
            "model": payload["modelInfo"],
        },
        "current_price": payload["todayPrice"],
        "selected_future_price": payload["futurePrice"],
        "previous_prices": payload["historical10Years"],
        "future_prices": payload["forecast24Months"],
    }


def predict(crop_key, region_key, currency, period):
    crop = CROPS[crop_key]
    region = REGIONS[region_key]
    scenario = build_scenario(crop_key, region_key, period)
    market_history = get_market_history(crop_key)

    current_factor_details = [
        {"name": "Climate", "value": EFFECTS["climate"][scenario["climate"]]},
        {"name": "Crop health", "value": EFFECTS["cropCondition"][scenario["cropCondition"]]},
        {"name": "Economy", "value": EFFECTS["economy"][scenario["economy"]]},
        {"name": "Policy", "value": EFFECTS["policy"][scenario["policy"]]},
        {"name": "Inflation", "value": scenario["inflation"] * 0.50},
        {"name": "Currency weakness", "value": scenario["currencyWeakness"] * 0.35},
        {"name": "Demand growth", "value": scenario["demandGrowth"] * 0.45},
        {"name": "Fuel and transport costs", "value": scenario["fuelCost"] * 0.28},
        {"name": "War or conflict risk", "value": scenario["warRisk"] * 0.22},
        {"name": "Supply shortage", "value": scenario["supplyShortage"] * 0.62},
    ]
    forecast_factor = {"name": f"{period}-month forecast", "value": period * crop["volatility"] * 0.015}
    factor_details = [*current_factor_details, forecast_factor]
    model_base_usd = crop["base"] * region["multiplier"]
    today_usd = scenario["liveData"].get("live_price_usd") or predict_price_usd(crop, region, scenario, 0)
    series_model = None
    if market_history:
        series_model = train_and_forecast_series(
            [item["price_usd"] for item in market_history["points"]],
            24,
        )
        future_index = max(1, min(24, period)) - 1
        future_usd = series_model["forecast"][future_index]
    else:
        future_usd = predict_price_usd(crop, region, scenario, period)
    price = future_usd * region["fx"][currency]
    confidence = confidence_score(crop["volatility"], scenario["warRisk"], scenario["supplyShortage"], EFFECTS["climate"][scenario["climate"]], period)
    forecast = build_month_forecast(crop, region, currency, scenario, 24, series_model)
    history = build_historical_prices(crop, region, currency, market_history)

    return {
        "price": round(price, 2),
        "futurePrice": {
            "price": round(price, 2),
            "currency": currency,
            "periodMonths": period,
            "unit": crop["unit"],
            "type": "future_forecast",
        },
        "todayPrice": build_today_price_payload(scenario, region, currency, crop, today_usd, model_base_usd),
        "currency": currency,
        "unit": crop["unit"],
        "confidence": confidence,
        "crop": crop["name"],
        "region": region["name"],
        "scenario": scenario,
        "factors": factor_details,
        "totalEffect": round(sum(item["value"] for item in factor_details), 4),
        "modelInfo": {
            "type": series_model["model_type"] if series_model else "Scenario ridge fallback model",
            "trainingData": market_history["source"] if market_history else "Synthetic scenario data (fallback)",
            "metrics": series_model["metrics"] if series_model else None,
            "observations": len(market_history["points"]) if market_history else 0,
        },
        "livePrice": build_today_price_payload(scenario, region, currency, crop, today_usd, model_base_usd),
        "forecast12Months": forecast[:12],
        "forecast24Months": forecast,
        "historical10Years": history,
        "historyType": "observed_benchmark" if market_history else "model_generated_fallback",
        "historySource": market_history["source"] if market_history else "Scenario model",
        "forecastNote": "Forecasts are planning estimates, not guaranteed market prices. Historical values are observed benchmark closes when the selected crop has a public series.",
        "sources": scenario["liveData"].get("sources", []),
        "errors": scenario["liveData"].get("errors", []),
    }


def options_payload():
    return {
        "crops": [{"key": key, **value} for key, value in CROPS.items()],
        "regions": [{"key": key, "name": value["name"]} for key, value in REGIONS.items()],
        "currencies": ["USD", "INR", "EUR", "GBP"],
    }


def build_scenario(crop_key, region_key, period):
    crop = CROPS[crop_key]
    region = REGIONS[region_key]
    profile = dict(region["profile"])
    live = collect_market_signals(region_key, crop_key)

    crop_condition = "average" if crop["volatility"] > 0.30 else "good" if crop["climateRisk"] > 0.14 else "excellent"
    demand_growth = crop["demand"] + (0.02 if period >= 6 else 0)
    supply_shortage = min(0.70, profile["shortage"] + crop["climateRisk"] + crop["volatility"] * 0.10)

    inflation = _decimal_or_default(live.get("inflation"), profile["inflation"])
    if live.get("gdp_growth") is not None and live["gdp_growth"] < 1:
        demand_growth -= 0.02

    scenario = {
        "climate": live.get("climate") or profile["climate"],
        "cropCondition": crop_condition,
        "economy": live.get("economy") or profile["economy"],
        "policy": profile["policy"],
        "inflation": inflation,
        "currencyWeakness": profile["currency"],
        "demandGrowth": max(-0.20, demand_growth),
        "fuelCost": profile["fuel"],
        "warRisk": live.get("war_risk") if live.get("war_risk") is not None else profile["war"],
        "supplyShortage": supply_shortage,
        "liveData": live,
    }
    scenario["effects"] = {
        "climate": EFFECTS["climate"][scenario["climate"]],
        "cropCondition": EFFECTS["cropCondition"][scenario["cropCondition"]],
        "economy": EFFECTS["economy"][scenario["economy"]],
        "policy": EFFECTS["policy"][scenario["policy"]],
    }
    return scenario


def _decimal_or_default(percent_value, fallback):
    if percent_value is None:
        return fallback
    return max(0, min(0.40, float(percent_value) / 100))


def confidence_score(volatility, war_risk, shortage, climate_effect, period):
    risk_penalty = (volatility * 100) + (war_risk * 18) + (shortage * 14) + abs(climate_effect * 30) + (period * 1.2)
    return max(42, min(91, round(96 - risk_penalty)))


def build_today_price_payload(scenario, region, currency, crop, today_usd, model_base_usd):
    live = scenario["liveData"]
    live_price_usd = live.get("live_price_usd")
    if live_price_usd:
        return {
            "available": True,
            "price": round(today_usd * region["fx"][currency], 2),
            "currency": currency,
            "unit": crop["unit"],
            "source": live.get("live_price_source"),
            "symbol": live.get("live_price_symbol"),
            "quoteTime": live.get("live_price_time"),
            "note": live.get("live_price_note"),
            "exactTodayQuote": bool(live.get("live_price_exact")),
            "type": "direct_quote" if live.get("live_price_exact") else "benchmark_estimate",
            "label": "Live market quote" if live.get("live_price_exact") else "Live benchmark estimate",
        }

    return {
        "available": True,
        "price": round(today_usd * region["fx"][currency], 2),
        "currency": currency,
        "unit": crop["unit"],
        "source": "Live-signal model",
        "symbol": None,
        "quoteTime": live.get("updated_at"),
        "note": "No public exchange quote was found for this crop, so today's price is estimated from the crop base price, region profile, weather, inflation, GDP, and risk signals.",
        "exactTodayQuote": False,
        "type": "live_signal_estimate",
        "label": "Estimated live spot price",
        "baseModelPrice": round(model_base_usd * region["fx"][currency], 2),
    }


def build_month_forecast(crop, region, currency, scenario, months, series_model=None):
    forecast = []
    today = date.today()

    for month in range(1, months + 1):
        price_usd = (
            series_model["forecast"][month - 1]
            if series_model
            else predict_price_usd(crop, region, scenario, month)
        )
        forecast.append(
            {
                "month": month,
                "date": add_months(today.year, today.month, month),
                "price": round(max(0, price_usd * region["fx"][currency]), 2),
                "currency": currency,
            }
        )
    return forecast


def add_months(year, month, offset):
    absolute_month = year * 12 + month - 1 + offset
    return f"{absolute_month // 12}-{absolute_month % 12 + 1:02d}"


def build_historical_prices(crop, region, currency, market_history=None):
    if market_history:
        return [
            {
                "date": item["date"],
                "year": int(item["date"][:4]),
                "month": int(item["date"][5:7]),
                "price": round(item["price_usd"] * region["fx"][currency], 2),
                "currency": currency,
                "observed": True,
            }
            for item in market_history["points"]
        ]

    history = []
    today = date.today()
    start_year = today.year - 10
    start_month = today.month

    for index in range(120):
        month_number = ((start_month - 1 + index) % 12) + 1
        year = start_year + ((start_month - 1 + index) // 12)
        months_from_start = index - 119
        scenario = historical_scenario(crop, region, month_number, months_from_start)
        price_usd = predict_price_usd(crop, region, scenario, month_number)
        history.append(
            {
                "date": f"{year}-{month_number:02d}",
                "year": year,
                "month": month_number,
                "price": round(max(0, price_usd * region["fx"][currency]), 2),
                "currency": currency,
                "observed": False,
            }
        )

    return history


def get_market_history(crop_key):
    try:
        return collect_market_history(crop_key)
    except Exception:
        return None


def historical_scenario(crop, region, month_number, months_from_start):
    profile = region["profile"]
    climate_cycle = ["normal", "excellent", "normal", "drought", "normal", "flood", "normal", "cold"]
    condition_cycle = ["good", "excellent", "good", "average", "good", "poor"]
    economy_cycle = ["stable", "strong", "stable", "weak", "stable"]
    policy_cycle = ["neutral", "support", "neutral", profile["policy"]]
    cycle_offset = int(crop["base"] + region["multiplier"] * 100)
    trend = months_from_start / 120

    scenario = {
        "climate": climate_cycle[(month_number + cycle_offset) % len(climate_cycle)],
        "cropCondition": condition_cycle[(month_number + cycle_offset) % len(condition_cycle)],
        "economy": economy_cycle[(month_number + cycle_offset) % len(economy_cycle)],
        "policy": policy_cycle[(month_number + cycle_offset) % len(policy_cycle)],
        "inflation": bounded(profile["inflation"] + trend * 0.025 + math.sin(month_number + cycle_offset) * 0.012, 0, 0.36),
        "currencyWeakness": bounded(profile["currency"] + trend * 0.030 + math.sin(month_number * 0.7 + cycle_offset) * 0.018, 0, 0.42),
        "demandGrowth": bounded(crop["demand"] + trend * 0.018 + math.cos(month_number + cycle_offset) * 0.010, -0.08, 0.24),
        "fuelCost": bounded(profile["fuel"] + trend * 0.020 + math.sin(month_number * 1.3 + cycle_offset) * 0.014, 0.01, 0.38),
        "warRisk": bounded(profile["war"] + math.sin(month_number * 0.5 + cycle_offset) * 0.020, 0, 0.70),
        "supplyShortage": bounded(profile["shortage"] + crop["climateRisk"] + math.cos(month_number * 0.9 + cycle_offset) * 0.035, 0.02, 0.72),
        "liveData": {"live_price_usd": None},
    }
    scenario["effects"] = {
        "climate": EFFECTS["climate"][scenario["climate"]],
        "cropCondition": EFFECTS["cropCondition"][scenario["cropCondition"]],
        "economy": EFFECTS["economy"][scenario["economy"]],
        "policy": EFFECTS["policy"][scenario["policy"]],
    }
    return scenario


def bounded(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def math_sin(month):
    # Small deterministic seasonal wave without adding another dependency.
    pattern = [0.15, 0.30, 0.42, 0.25, 0.05, -0.12, -0.25, -0.34, -0.20, 0.02, 0.16, 0.26]
    return pattern[(month - 1) % len(pattern)]


if __name__ == "__main__":
    port = int(os.environ.get("PORT") or (sys.argv[1] if len(sys.argv) > 1 else 8080))
    host = os.environ.get("HOST", "0.0.0.0")
    try:
        server = ExclusiveThreadingHTTPServer((host, port), Handler)
    except OSError:
        print(f"Port {port} is already in use by another server.")
        print("Stop the old server or run: python server.py 8765")
        raise SystemExit(1)
    local_url = f"http://localhost:{port}/"
    print(f"Crop price app running at {local_url}")
    server.serve_forever()
