from copy import deepcopy
from pathlib import Path

from pptx import Presentation


PPTX_PATH = Path("AgriPredict_Seminar_Presentation.pptx")
OUTPUT_PATH = Path("CropSmart_Project_Presentation.pptx")


def paragraph_style(paragraph):
    run = paragraph.runs[0] if paragraph.runs else None
    return {
        "pPr": deepcopy(paragraph._p.get_or_add_pPr()),
        "rPr": deepcopy(run._r.get_or_add_rPr()) if run else None,
    }


def set_text(shape, text):
    text_frame = shape.text_frame
    styles = [paragraph_style(p) for p in text_frame.paragraphs]
    text_frame.clear()

    lines = text.split("\n")
    for index, line in enumerate(lines):
        paragraph = text_frame.paragraphs[0] if index == 0 else text_frame.add_paragraph()
        paragraph.text = line
        style = styles[min(index, len(styles) - 1)]
        old_pPr = paragraph._p.get_or_add_pPr()
        paragraph._p.replace(old_pPr, deepcopy(style["pPr"]))
        if style["rPr"] is not None and paragraph.runs:
            run = paragraph.runs[0]
            old_rPr = run._r.get_or_add_rPr()
            run._r.replace(old_rPr, deepcopy(style["rPr"]))


def update_cards(slide, values):
    for shape_index, value in values.items():
        set_text(slide.shapes[shape_index], value)


def main():
    presentation = Presentation(PPTX_PATH)

    for slide in presentation.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text") and "AgriPredict" in shape.text:
                set_text(shape, shape.text.replace("AgriPredict", "CropSmart"))

    update_cards(
        presentation.slides[1],
        {
            1: (
                "Crop prices change because of weather, demand, inflation, supply, transport cost, "
                "seasonality, and global risk.\nFarmers and buyers need one place to view current "
                "market signals, historical trends, and future estimates.\nThe project combines "
                "public data, observed benchmark history, and forecasting in a browser dashboard."
            ),
            2: (
                "Main Goal\nShow today's price and predict the next 1, 3, 6, 12, or 24 months for a "
                "selected crop, region, and currency."
            ),
            4: (
                "Output\nCurrent price, 10-year history, 24-month forecast, holdout accuracy, price "
                "drivers, sources, and CSV/JSON export."
            ),
        },
    )

    update_cards(
        presentation.slides[2],
        {
            2: (
                "2. Future Prediction\nForecast selected periods and generate a complete 24-month "
                "monthly outlook."
            ),
            4: (
                "4. Explainability\nShow climate, supply, inflation, demand, fuel, policy, and risk "
                "drivers with source notes."
            ),
            5: (
                "5. Historical View\nDisplay up to 10 years of observed benchmark closes, clearly "
                "separated from model-generated fallback history."
            ),
            6: (
                "6. Export\nDownload current, historical, and future prices as CSV or JSON."
            ),
        },
    )

    update_cards(
        presentation.slides[3],
        {
            2: (
                "Backend API\nserver.py\nAPI v2 handles health, options, prediction, and CSV/JSON export."
            ),
            4: (
                "Forecast Models\nml_model.py\nRidge autoregression for observed series; ridge "
                "scenario fallback for other crops."
            ),
            5: (
                "Data and Cache\ndata/*.json and *.csv\nStores live signals, benchmark history, "
                "training data, and model metadata."
            ),
            6: (
                "Export\n/api/export\nCreates CSV or JSON containing current, historical, and "
                "24-month forecast data."
            ),
        },
    )

    update_cards(
        presentation.slides[4],
        {
            1: "User Browser\nHTML/CSS/JS dashboard",
            2: "Python Server\nAPI v2\n/api/predict",
            3: "Public Sources\nYahoo, World Bank,\nOpen-Meteo, GDELT",
            4: "Forecast Engine\nObserved-series ridge\nor scenario fallback",
            5: "Output\nToday + 10-year history\n24-month forecast + export",
            11: (
                "Flow: User input -> API health check -> live signals and benchmark history -> "
                "forecast model -> dashboard and CSV/JSON output."
            ),
        },
    )

    update_cards(
        presentation.slides[5],
        {
            1: (
                "Market Benchmark\nYahoo Finance monthly futures closes provide observed history "
                "for supported benchmark crops."
            ),
            4: (
                "Risk Signal\nGDELT news data contributes a conflict or unrest risk signal."
            ),
            5: (
                "Fallback and Cache\nCached responses reduce repeated calls. Missing exact quotes "
                "are labeled as live-signal or scenario estimates."
            ),
        },
    )

    update_cards(
        presentation.slides[6],
        {
            1: (
                "1. Validate API v2 and read crop, region, currency, and forecast period.\n"
                "2. Collect live market, weather, economy, and risk signals; use cache when needed.\n"
                "3. Load up to 10 years of monthly benchmark closes for supported crops.\n"
                "4. Train a chronological ridge autoregression using trend, seasonality, and 1-, "
                "3-, and 12-month lags.\n"
                "5. Evaluate on a 6-12 month holdout, then recursively forecast 24 months.\n"
                "6. For crops without a public series, use the labeled ridge scenario-model fallback."
            ),
            2: (
                "Observed-Series Model\nLog price = ridge(trend + seasonality + lagged prices)"
            ),
            3: (
                "Validation\nThe dashboard reports holdout MAPE when observed benchmark history is available."
            ),
            4: (
                "Important\nBenchmark futures are reference prices, not exact local mandi or farmgate prices."
            ),
        },
    )

    update_cards(
        presentation.slides[7],
        {
            2: (
                "Today Price\nDirect quote when available; otherwise a clearly labeled live-signal estimate."
            ),
            3: (
                "Future Price\nSelected-period estimate plus a full 24-month monthly forecast."
            ),
            5: "Trend Views\n24-month forecast and 10-year historical chart.",
            6: (
                "Model Details\nModel type, observations, holdout MAPE, assumptions, and source quality."
            ),
            7: (
                "Drivers\nMain factors increasing or decreasing the expected price."
            ),
            8: "CSV + JSON\nExport current, historical, and future prices.",
        },
    )

    update_cards(
        presentation.slides[8],
        {
            1: (
                "1. Run the project: python server.py 8100\n"
                "2. Open browser: http://localhost:8100/\n"
                "3. Select crop: Wheat or Rice - Basmati\n"
                "4. Select region: India\n"
                "5. Select currency: INR\n"
                "6. Select period: 3, 6, 12, or 24 months\n"
                "7. Show current price, observed history, forecast, model details, drivers, and export."
            ),
            2: (
                "What to Explain\nObserved benchmark history uses a time-series model. Unsupported "
                "crops are explicitly shown as scenario-model fallback."
            ),
            3: (
                "Sample Output\nToday price + 10-year history + 24-month forecast + confidence + "
                "holdout MAPE where available."
            ),
            4: (
                "Export Files\nUse Export CSV or Export JSON to download all price series and model metadata."
            ),
        },
    )

    update_cards(
        presentation.slides[9],
        {
            0: "Model, Data and Validation",
            1: (
                "22 crops and crop variants across 14 global regions.\n"
                "19 model features in the scenario fallback: crop, region, market, risk, and seasonality.\n"
                "Local training dataset contains 36,960 generated feature rows for fallback model development.\n"
                "Observed benchmark forecasting requires at least 36 monthly prices.\n"
                "Chronological holdout uses 6-12 recent months and reports MAPE and R2.\n"
                "Prediction responses include model type, source, observation count, confidence, and limitations."
            ),
        },
    )

    update_cards(
        presentation.slides[10],
        {
            1: (
                "Limitations\n- Public futures benchmarks do not equal exact local mandi prices.\n"
                "- Only supported crops currently have observed benchmark history.\n"
                "- The fallback training dataset is generated, so its accuracy metrics are not "
                "evidence of real-market performance.\n"
                "- Internet or API failures can require cached data and fallback estimates."
            ),
            2: (
                "Future Scope\n- Add official Agmarknet/APMC and crop-grade datasets.\n"
                "- Expand observed series and perform rolling backtests.\n"
                "- Add uncertainty intervals, alerts, maps, and saved watchlists.\n"
                "- Deploy with a database, authentication, and scheduled model refresh."
            ),
        },
    )

    update_cards(
        presentation.slides[11],
        {
            1: (
                "CropSmart combines current public signals, observed benchmark history, and "
                "transparent forecasting in one dashboard.\nIt provides a 10-year historical view, "
                "24-month outlook, model metadata, source notes, and reusable exports.\nIts strongest "
                "next step is adding verified local mandi data for location- and grade-specific forecasts."
            ),
        },
    )

    presentation.save(OUTPUT_PATH)
    print(f"Saved {OUTPUT_PATH} with {len(presentation.slides)} slides")


if __name__ == "__main__":
    main()
