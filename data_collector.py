import json
import math
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


DATA_DIR = Path("data")
CACHE_FILE = DATA_DIR / "live_market_data.json"
HISTORY_CACHE_FILE = DATA_DIR / "market_history.json"
CACHE_SECONDS = 60 * 15
HISTORY_CACHE_SECONDS = 60 * 60 * 12


REGION_META = {
    "india": {"name": "India", "iso3": "IND", "lat": 28.61, "lon": 77.21},
    "usa": {"name": "United States", "iso3": "USA", "lat": 38.90, "lon": -77.04},
    "brazil": {"name": "Brazil", "iso3": "BRA", "lat": -15.79, "lon": -47.88},
    "china": {"name": "China", "iso3": "CHN", "lat": 39.90, "lon": 116.41},
    "eu": {"name": "European Union", "iso3": "EUU", "lat": 50.85, "lon": 4.35},
    "ukraine": {"name": "Ukraine", "iso3": "UKR", "lat": 50.45, "lon": 30.52},
    "nigeria": {"name": "Nigeria", "iso3": "NGA", "lat": 9.08, "lon": 7.40},
    "australia": {"name": "Australia", "iso3": "AUS", "lat": -35.28, "lon": 149.13},
    "canada": {"name": "Canada", "iso3": "CAN", "lat": 45.42, "lon": -75.70},
    "argentina": {"name": "Argentina", "iso3": "ARG", "lat": -34.60, "lon": -58.38},
    "russia": {"name": "Russia", "iso3": "RUS", "lat": 55.75, "lon": 37.62},
    "thailand": {"name": "Thailand", "iso3": "THA", "lat": 13.75, "lon": 100.50},
    "vietnam": {"name": "Vietnam", "iso3": "VNM", "lat": 21.03, "lon": 105.83},
    "indonesia": {"name": "Indonesia", "iso3": "IDN", "lat": -6.20, "lon": 106.82},
}

CROP_MARKET_SYMBOLS = {
    "wheat": {"symbol": "ZW=F", "name": "Wheat futures", "unit": "USD per tonne", "kind": "cents_per_bushel", "kg_per_bushel": 27.2155},
    "maize": {"symbol": "ZC=F", "name": "Corn futures", "unit": "USD per tonne", "kind": "cents_per_bushel", "kg_per_bushel": 25.4012},
    "soybean": {"symbol": "ZS=F", "name": "Soybean futures", "unit": "USD per tonne", "kind": "cents_per_bushel", "kg_per_bushel": 27.2155},
    "rice": {"symbol": "ZR=F", "name": "Rough rice futures", "unit": "USD per tonne", "kind": "usd_per_cwt"},
    "rice_basmati": {"symbol": "ZR=F", "name": "Rough rice benchmark adjusted for basmati", "unit": "USD per tonne", "kind": "usd_per_cwt", "benchmark_multiplier": 2.26, "basis_note": "Basmati has no direct public futures quote here; this is a benchmark estimate adjusted for the variety premium."},
    "rice_non_basmati": {"symbol": "ZR=F", "name": "Rough rice benchmark adjusted for non-basmati", "unit": "USD per tonne", "kind": "usd_per_cwt", "benchmark_multiplier": 1.02, "basis_note": "Non-basmati rice is a benchmark estimate from rough rice futures."},
    "rice_paddy": {"symbol": "ZR=F", "name": "Rough rice benchmark adjusted for paddy", "unit": "USD per tonne", "kind": "usd_per_cwt", "benchmark_multiplier": 0.67, "basis_note": "Paddy is a benchmark estimate from rough rice futures."},
    "rice_parboiled": {"symbol": "ZR=F", "name": "Rough rice benchmark adjusted for parboiled rice", "unit": "USD per tonne", "kind": "usd_per_cwt", "benchmark_multiplier": 1.12, "basis_note": "Parboiled rice is a benchmark estimate from rough rice futures."},
    "rice_broken": {"symbol": "ZR=F", "name": "Rough rice benchmark adjusted for broken rice", "unit": "USD per tonne", "kind": "usd_per_cwt", "benchmark_multiplier": 0.86, "basis_note": "Broken rice is a benchmark estimate from rough rice futures."},
    "cotton": {"symbol": "CT=F", "name": "Cotton futures", "unit": "USD per bale", "kind": "cents_per_pound_bale", "pounds_per_bale": 480},
    "sugarcane": {"symbol": "SB=F", "name": "Sugar futures benchmark", "unit": "USD per tonne", "kind": "cents_per_pound_tonne"},
    "coffee": {"symbol": "KC=F", "name": "Coffee futures", "unit": "USD per tonne", "kind": "cents_per_pound_tonne"},
    "cocoa": {"symbol": "CC=F", "name": "Cocoa futures", "unit": "USD per tonne", "kind": "usd_per_tonne"},
}


def collect_market_signals(region_key, crop_key):
    cached = _read_cache(region_key, crop_key)
    if cached:
        cached["from_cache"] = True
        return cached

    region = REGION_META[region_key]
    signals = {
        "region": region_key,
        "crop": crop_key,
        "updated_at": int(time.time()),
        "from_cache": False,
        "sources": [],
        "errors": [],
        "inflation": None,
        "gdp_growth": None,
        "temperature_max_avg": None,
        "rainfall_sum": None,
        "climate": None,
        "economy": None,
        "war_risk": None,
        "live_price_usd": None,
        "live_price_unit": None,
        "live_price_source": None,
        "live_price_time": None,
        "live_price_note": None,
    }

    jobs = {
        "Yahoo Finance": lambda: ("market", _yahoo_live_market_price(crop_key)),
        "World Bank inflation": lambda: ("inflation", _world_bank_latest(region["iso3"], "FP.CPI.TOTL.ZG")),
        "World Bank GDP": lambda: ("gdp", _world_bank_latest(region["iso3"], "NY.GDP.MKTP.KD.ZG")),
        "Open-Meteo": lambda: ("weather", _open_meteo_weather(region["lat"], region["lon"])),
        "GDELT": lambda: ("risk", _gdelt_conflict_risk(region["name"])),
    }
    with ThreadPoolExecutor(max_workers=len(jobs)) as executor:
        futures = {executor.submit(job): name for name, job in jobs.items()}
        for future in as_completed(futures):
            name = futures[future]
            try:
                kind, value = future.result()
                _apply_signal(signals, kind, value)
            except Exception as exc:
                signals["errors"].append(f"{name}: {exc}")

    _write_cache(region_key, crop_key, signals)
    return signals


def _apply_signal(signals, kind, value):
    if kind == "market" and value:
        signals.update(value)
        signals["sources"].append("Yahoo Finance futures benchmark")
    elif kind == "inflation":
        signals["inflation"] = value
        signals["sources"].append("World Bank inflation")
    elif kind == "gdp":
        signals["gdp_growth"] = value
        signals["economy"] = _economy_from_gdp(value)
        signals["sources"].append("World Bank GDP growth")
    elif kind == "weather":
        signals.update(value)
        signals["climate"] = _climate_from_weather(value["temperature_max_avg"], value["rainfall_sum"])
        signals["sources"].append("Open-Meteo forecast")
    elif kind == "risk":
        signals["war_risk"] = value
        signals["sources"].append("GDELT news")


def collect_market_history(crop_key):
    market = CROP_MARKET_SYMBOLS.get(crop_key)
    if not market:
        return None

    cached = _read_history_cache(crop_key)
    if cached:
        cached["from_cache"] = True
        return cached

    symbol = quote(market["symbol"])
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=10y&interval=1mo&events=history"
    data = _request_json(url)
    result = data.get("chart", {}).get("result", [{}])[0]
    timestamps = result.get("timestamp", [])
    closes = result.get("indicators", {}).get("quote", [{}])[0].get("close", [])
    points = []
    for timestamp, close in zip(timestamps, closes):
        if close is None:
            continue
        converted = _convert_market_price(float(close), market) * market.get("benchmark_multiplier", 1)
        points.append(
            {
                "date": datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%Y-%m"),
                "price_usd": round(converted, 4),
            }
        )

    if len(points) < 36:
        raise ValueError("insufficient monthly market history")

    payload = {
        "crop": crop_key,
        "symbol": market["symbol"],
        "source": f"{market['name']} monthly closes",
        "note": market.get("basis_note") or "Public futures benchmark history; not a local mandi or farmgate series.",
        "updated_at": int(time.time()),
        "from_cache": False,
        "points": points[-120:],
    }
    _write_history_cache(crop_key, payload)
    return payload


def _request_json(url):
    request = Request(url, headers={"User-Agent": "crop-price-prediction-local/1.0"})
    with urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def _world_bank_latest(country_code, indicator):
    url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/{indicator}?format=json&per_page=8"
    data = _request_json(url)
    rows = data[1] if isinstance(data, list) and len(data) > 1 else []
    for row in rows:
        value = row.get("value")
        if value is not None:
            return float(value)
    raise ValueError("no recent value found")


def _open_meteo_weather(lat, lon):
    params = urlencode(
        {
            "latitude": lat,
            "longitude": lon,
            "daily": "temperature_2m_max,precipitation_sum",
            "forecast_days": 7,
            "timezone": "auto",
        }
    )
    data = _request_json(f"https://api.open-meteo.com/v1/forecast?{params}")
    daily = data.get("daily", {})
    temps = [float(value) for value in daily.get("temperature_2m_max", []) if value is not None]
    rainfall = [float(value) for value in daily.get("precipitation_sum", []) if value is not None]
    if not temps:
        raise ValueError("temperature forecast missing")
    return {
        "temperature_max_avg": round(sum(temps) / len(temps), 2),
        "rainfall_sum": round(sum(rainfall), 2),
    }


def _gdelt_conflict_risk(country_name):
    query = quote(f'("{country_name}") (war OR conflict OR sanctions OR unrest)')
    url = f"https://api.gdeltproject.org/api/v2/doc/doc?query={query}&mode=timelinevol&format=json&timespan=30d"
    data = _request_json(url)
    timeline = data.get("timeline", [])
    values = [float(item.get("value", 0)) for item in timeline]
    if not values:
        return 0.08
    avg = sum(values) / len(values)
    return round(max(0.02, min(0.70, math.log1p(avg) / 8)), 3)


def _yahoo_live_market_price(crop_key):
    market = CROP_MARKET_SYMBOLS.get(crop_key)
    if not market:
        return None

    symbol = quote(market["symbol"])
    data = _request_json(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=5d&interval=1d")
    result = data.get("chart", {}).get("result", [{}])[0]
    meta = result.get("meta", {})
    raw_price = meta.get("regularMarketPrice") or meta.get("previousClose")
    if raw_price is None:
        raise ValueError("market price missing")

    converted = _convert_market_price(float(raw_price), market) * market.get("benchmark_multiplier", 1)
    return {
        "live_price_usd": round(converted, 2),
        "live_price_unit": market["unit"],
        "live_price_source": market["name"],
        "live_price_symbol": market["symbol"],
        "live_price_raw": raw_price,
        "live_price_time": meta.get("regularMarketTime"),
        "live_price_note": market.get("basis_note") or "Direct public futures benchmark quote. This is not a local mandi/farmgate price.",
        "live_price_exact": "basis_note" not in market,
    }


def _convert_market_price(raw_price, market):
    kind = market["kind"]
    if kind == "cents_per_bushel":
        usd_per_bushel = raw_price / 100
        bushels_per_tonne = 1000 / market["kg_per_bushel"]
        return usd_per_bushel * bushels_per_tonne
    if kind == "usd_per_cwt":
        return raw_price * 22.0462
    if kind == "cents_per_pound_bale":
        return (raw_price / 100) * market["pounds_per_bale"]
    if kind == "cents_per_pound_tonne":
        return (raw_price / 100) * 2204.62
    if kind == "usd_per_tonne":
        return raw_price
    raise ValueError(f"unsupported market price kind: {kind}")


def _economy_from_gdp(gdp_growth):
    if gdp_growth is None:
        return None
    if gdp_growth >= 4:
        return "strong"
    if gdp_growth >= 1:
        return "stable"
    if gdp_growth >= -2:
        return "weak"
    return "recession"


def _climate_from_weather(temp_avg, rainfall_sum):
    if temp_avg >= 36 and rainfall_sum < 8:
        return "drought"
    if rainfall_sum >= 65:
        return "flood"
    if temp_avg <= 8:
        return "cold"
    if 18 <= temp_avg <= 31 and 8 <= rainfall_sum <= 45:
        return "excellent"
    return "normal"


def _read_cache(region_key, crop_key):
    if not CACHE_FILE.exists():
        return None
    try:
        cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    key = f"{region_key}:{crop_key}"
    entry = cache.get(key)
    if not entry:
        return None
    if not entry.get("sources") and entry.get("errors"):
        return None
    if entry.get("live_price_usd") and "live_price_note" not in entry:
        return None
    if int(time.time()) - int(entry.get("updated_at", 0)) > CACHE_SECONDS:
        return None
    return entry


def _write_cache(region_key, crop_key, signals):
    DATA_DIR.mkdir(exist_ok=True)
    cache = {}
    if CACHE_FILE.exists():
        try:
            cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            cache = {}
    cache[f"{region_key}:{crop_key}"] = signals
    CACHE_FILE.write_text(json.dumps(cache, indent=2), encoding="utf-8")


def _read_history_cache(crop_key):
    if not HISTORY_CACHE_FILE.exists():
        return None
    try:
        cache = json.loads(HISTORY_CACHE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    entry = cache.get(crop_key)
    if not entry or len(entry.get("points", [])) < 36:
        return None
    if int(time.time()) - int(entry.get("updated_at", 0)) > HISTORY_CACHE_SECONDS:
        return None
    return entry


def _write_history_cache(crop_key, payload):
    DATA_DIR.mkdir(exist_ok=True)
    cache = {}
    if HISTORY_CACHE_FILE.exists():
        try:
            cache = json.loads(HISTORY_CACHE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            cache = {}
    cache[crop_key] = payload
    HISTORY_CACHE_FILE.write_text(json.dumps(cache, indent=2), encoding="utf-8")
