from dataclasses import dataclass


@dataclass(frozen=True)
class Crop:
    base_usd: float
    volatility: float
    unit: str


CROPS = {
    "wheat": Crop(265, 0.16, "per tonne"),
    "rice": Crop(420, 0.13, "per tonne"),
    "maize": Crop(230, 0.18, "per tonne"),
    "soybean": Crop(510, 0.20, "per tonne"),
    "cotton": Crop(1720, 0.22, "per bale"),
    "sugarcane": Crop(42, 0.11, "per tonne"),
    "potato": Crop(190, 0.24, "per tonne"),
    "onion": Crop(310, 0.32, "per tonne"),
    "tomato": Crop(360, 0.35, "per tonne"),
    "coffee": Crop(4250, 0.25, "per tonne"),
    "cocoa": Crop(7600, 0.30, "per tonne"),
    "pulses": Crop(760, 0.19, "per tonne"),
}

REGION_MULTIPLIERS = {
    "india": 0.82,
    "usa": 1.08,
    "brazil": 0.94,
    "china": 1.02,
    "eu": 1.16,
    "ukraine": 0.78,
    "nigeria": 0.74,
    "australia": 1.12,
}

CLIMATE_EFFECTS = {
    "normal": 0,
    "drought": 0.18,
    "flood": 0.15,
    "cold": 0.08,
    "excellent": -0.08,
}

CROP_CONDITION_EFFECTS = {
    "excellent": -0.09,
    "good": -0.03,
    "average": 0.03,
    "poor": 0.14,
    "damaged": 0.27,
}

ECONOMY_EFFECTS = {
    "strong": 0.06,
    "stable": 0,
    "weak": -0.04,
    "recession": -0.09,
}

POLICY_EFFECTS = {
    "support": 0.08,
    "neutral": 0,
    "exportBan": -0.10,
    "importOpen": -0.07,
    "taxIncrease": 0.07,
}


def predict_crop_price(
    crop: str,
    region: str,
    climate: str = "normal",
    crop_condition: str = "good",
    economy: str = "stable",
    policy: str = "neutral",
    inflation_percent: float = 6,
    currency_weakness_percent: float = 10,
    demand_growth_percent: float = 8,
    fuel_cost_percent: float = 12,
    war_risk_percent: float = 15,
    supply_shortage_percent: float = 20,
    months: int = 3,
) -> dict:
    selected_crop = CROPS[crop]
    total_effect = sum(
        [
            CLIMATE_EFFECTS[climate],
            CROP_CONDITION_EFFECTS[crop_condition],
            ECONOMY_EFFECTS[economy],
            POLICY_EFFECTS[policy],
            (inflation_percent / 100) * 0.50,
            (currency_weakness_percent / 100) * 0.35,
            (demand_growth_percent / 100) * 0.45,
            (fuel_cost_percent / 100) * 0.28,
            (war_risk_percent / 100) * 0.22,
            (supply_shortage_percent / 100) * 0.62,
            months * selected_crop.volatility * 0.015,
        ]
    )

    price_usd = selected_crop.base_usd * REGION_MULTIPLIERS[region] * max(0.35, 1 + total_effect)
    confidence = _confidence(
        selected_crop.volatility,
        war_risk_percent / 100,
        supply_shortage_percent / 100,
        CLIMATE_EFFECTS[climate],
        months,
    )

    return {
        "price_usd": round(price_usd, 2),
        "unit": selected_crop.unit,
        "confidence_percent": confidence,
        "total_effect_percent": round(total_effect * 100, 2),
    }


def _confidence(volatility: float, war_risk: float, shortage: float, climate_effect: float, months: int) -> int:
    risk_penalty = (volatility * 100) + (war_risk * 18) + (shortage * 14) + abs(climate_effect * 30) + (months * 1.2)
    return max(42, min(91, round(96 - risk_penalty)))


if __name__ == "__main__":
    print(
        predict_crop_price(
            crop="wheat",
            region="india",
            climate="drought",
            crop_condition="average",
            economy="stable",
            policy="neutral",
        )
    )
