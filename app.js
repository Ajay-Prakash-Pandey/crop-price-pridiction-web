const fallbackCrops = [
  { key: "wheat", name: "Wheat", base: 265, unit: "per tonne", volatility: 0.16, climateRisk: 0.12, demand: 0.08 },
  { key: "rice", name: "Rice", base: 420, unit: "per tonne", volatility: 0.13, climateRisk: 0.10, demand: 0.10 },
  { key: "maize", name: "Maize", base: 230, unit: "per tonne", volatility: 0.18, climateRisk: 0.14, demand: 0.09 },
  { key: "soybean", name: "Soybean", base: 510, unit: "per tonne", volatility: 0.20, climateRisk: 0.13, demand: 0.08 },
  { key: "cotton", name: "Cotton", base: 1720, unit: "per bale", volatility: 0.22, climateRisk: 0.12, demand: 0.05 },
  { key: "onion", name: "Onion", base: 310, unit: "per tonne", volatility: 0.32, climateRisk: 0.16, demand: 0.08 },
  { key: "tomato", name: "Tomato", base: 360, unit: "per tonne", volatility: 0.35, climateRisk: 0.18, demand: 0.07 },
  { key: "coffee", name: "Coffee", base: 4250, unit: "per tonne", volatility: 0.25, climateRisk: 0.15, demand: 0.06 },
  { key: "cocoa", name: "Cocoa", base: 7600, unit: "per tonne", volatility: 0.30, climateRisk: 0.17, demand: 0.06 }
];

const fallbackRegions = [
  { key: "india", name: "India" },
  { key: "usa", name: "United States" },
  { key: "brazil", name: "Brazil" },
  { key: "china", name: "China" },
  { key: "eu", name: "European Union" },
  { key: "ukraine", name: "Ukraine" },
  { key: "nigeria", name: "Nigeria" },
  { key: "australia", name: "Australia" }
];

const fallbackCurrencies = ["USD", "INR", "EUR", "GBP"];
const requiredApiVersion = 2;

const effects = {
  climate: {
    normal: "Normal season",
    drought: "Dry season risk",
    flood: "Heavy rain risk",
    cold: "Cool weather risk",
    excellent: "Good growing weather"
  },
  cropCondition: {
    excellent: "Excellent crop condition",
    good: "Good crop condition",
    average: "Average crop condition",
    poor: "Poor crop condition",
    damaged: "Damaged crop"
  },
  economy: {
    strong: "Strong economy",
    stable: "Stable economy",
    weak: "Weak economy",
    recession: "Recession pressure"
  },
  policy: {
    support: "Government price support",
    neutral: "Neutral policy",
    exportBan: "Export restriction",
    importOpen: "Import relaxed",
    taxIncrease: "Higher tax or fees"
  }
};

const currencySymbols = { USD: "USD ", INR: "INR ", EUR: "EUR ", GBP: "GBP " };

let options = {
  crops: fallbackCrops,
  regions: fallbackRegions,
  currencies: fallbackCurrencies
};
let apiAvailable = false;
let lastPrediction = null;

const form = document.querySelector("#prediction-form");
const cropInput = document.querySelector("#crop");
const regionInput = document.querySelector("#region");
const currencyInput = document.querySelector("#currency");
const periodInput = document.querySelector("#period");
const priceEl = document.querySelector("#price");
const unitEl = document.querySelector("#unit");
const summaryEl = document.querySelector("#summary");
const confidenceText = document.querySelector("#confidenceText");
const confidenceBar = document.querySelector("#confidenceBar");
const driversEl = document.querySelector("#drivers");
const assumptionsEl = document.querySelector("#assumptions");
const notesEl = document.querySelector("#notes");
const livePriceEl = document.querySelector("#live-price");
const liveSourceEl = document.querySelector("#live-source");
const forecastEl = document.querySelector("#forecast-list");
const forecastChartEl = document.querySelector("#forecast-chart");
const historyChartEl = document.querySelector("#history-chart");
const historySummaryEl = document.querySelector("#history-summary");
const tickerEl = document.querySelector("#markets");
const sourceListEl = document.querySelector("#source-list");
const exportCsvButton = document.querySelector("#export-csv");
const exportJsonButton = document.querySelector("#export-json");

async function init() {
  try {
    await verifyApiServer();
    apiAvailable = true;
    await loadOptions();
  } catch (error) {
    apiAvailable = false;
    options = { crops: fallbackCrops, regions: fallbackRegions, currencies: fallbackCurrencies };
  }
  populateSelects();
  renderTicker();
  bindEvents();
  predict();
}

function isAppServer() {
  return location.protocol === "http:" || location.protocol === "https:";
}

async function verifyApiServer() {
  const response = await fetch("/api/health", { cache: "no-store" });
  if (!response.ok) {
    throw new Error("This address is serving an old or static website");
  }
  const health = await response.json();
  if (health.apiVersion !== requiredApiVersion) {
    throw new Error(`API version ${requiredApiVersion} is required`);
  }
}

async function loadOptions() {
  try {
    const response = await fetch("/api/options");
    if (!response.ok) throw new Error(`Options API returned ${response.status}`);
    options = await response.json();
  } catch (error) {
    options = { crops: fallbackCrops, regions: fallbackRegions, currencies: fallbackCurrencies };
  }
}

function populateSelects() {
  cropInput.innerHTML = "";
  regionInput.innerHTML = "";
  currencyInput.innerHTML = "";

  options.crops.forEach(crop => cropInput.add(new Option(crop.name, crop.key)));
  options.regions.forEach(region => regionInput.add(new Option(region.name, region.key)));
  options.currencies.forEach(currency => currencyInput.add(new Option(currency, currency)));

  cropInput.value = "wheat";
  regionInput.value = "india";
  currencyInput.value = "INR";
}

function renderTicker() {
  tickerEl.innerHTML = "";
  options.crops.slice(0, 14).forEach(crop => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "commodity-chip";
    button.innerHTML = `<span>${crop.name}</span><strong>${riskText(crop.volatility)}</strong>`;
    button.addEventListener("click", () => {
      cropInput.value = crop.key;
      predict();
    });
    tickerEl.appendChild(button);
  });
}

function bindEvents() {
  form.addEventListener("submit", predict);
  cropInput.addEventListener("change", predict);
  regionInput.addEventListener("change", predict);
  currencyInput.addEventListener("change", predict);
  periodInput.addEventListener("change", predict);
  exportCsvButton.addEventListener("click", () => exportData("csv"));
  exportJsonButton.addEventListener("click", () => exportData("json"));
}

async function predict(event) {
  if (event) event.preventDefault();

  setLoadingState();
  const params = new URLSearchParams({
    crop: cropInput.value,
    region: regionInput.value,
    currency: currencyInput.value,
    period: periodInput.value
  });

  try {
    if (apiAvailable) {
      const response = await fetch(`/api/predict?${params.toString()}`);
      if (!response.ok) {
        const failure = await response.json().catch(() => ({}));
        throw new Error(failure.error || `Prediction API returned ${response.status}`);
      }
      lastPrediction = await response.json();
    } else {
      lastPrediction = buildStaticPrediction(cropInput.value, regionInput.value, currencyInput.value, Number(periodInput.value));
    }
    renderPrediction(lastPrediction);
  } catch (error) {
    renderApiError(error);
  }
}

function setLoadingState() {
  summaryEl.textContent = "Collecting market signals...";
  livePriceEl.textContent = "Checking...";
  liveSourceEl.textContent = "Looking for live quote or signal estimate";
  sourceListEl.innerHTML = "";
}

function renderPrediction(result) {
  if (!Array.isArray(result.forecast24Months) || !Array.isArray(result.historical10Years)) {
    throw new Error("The running server is outdated. Restart server.py.");
  }
  const future = result.futurePrice || result;
  priceEl.textContent = formatMoney(future.price, future.currency || result.currency);
  unitEl.textContent = `${future.periodMonths || periodInput.value} month forecast, ${result.unit}`;
  summaryEl.textContent = `${result.crop} in ${result.region}`;
  confidenceText.textContent = `${result.confidence}%`;
  confidenceBar.style.width = `${result.confidence}%`;
  confidenceBar.style.background = result.confidence >= 75 ? "var(--green)" : result.confidence >= 60 ? "var(--amber)" : "var(--red)";

  renderLivePrice(result.todayPrice || result.livePrice);
  renderAssumptions(result.scenario);
  renderDrivers(result.factors);
  renderForecast(result.forecast24Months || result.forecast12Months, result.currency);
  renderHistory(result.historical10Years, result.currency);
  renderSources(result.sources, result.errors);
  notesEl.textContent = buildNotes(result);
  const model = result.modelInfo || {};
  if (model.metrics) {
    document.querySelector("#confidence-note").textContent =
      `Holdout MAPE ${model.metrics.holdout_mape_percent}% / ${model.observations} observed months`;
  } else {
    document.querySelector("#confidence-note").textContent = "Fallback model; no observed series available";
  }
}

function renderApiError(error) {
  summaryEl.textContent = "Prediction data could not be loaded";
  priceEl.textContent = "--";
  livePriceEl.textContent = "Offline";
  liveSourceEl.textContent = "The crop-price API did not respond";
  notesEl.textContent = `${error && error.message ? error.message : "Unknown API error"}. Run python server.py and open http://localhost:8080/.`;
  assumptionsEl.innerHTML = "";
  driversEl.innerHTML = "";
  forecastEl.innerHTML = '<p class="empty-state">Future prices require the Python app server.</p>';
  forecastChartEl.innerHTML = "";
  historyChartEl.innerHTML = '<p class="empty-state">Historical prices require the Python app server.</p>';
  historySummaryEl.innerHTML = "";
  sourceListEl.innerHTML = "<span>No API response.</span>";
}

function renderServerRequired() {
  document.body.innerHTML = `
    <main class="server-required">
      <section class="panel">
        <p class="eyebrow">Python server required</p>
        <h1>Open the working CropSmart website</h1>
        <p>Future and historical crop prices come from the Python API and cannot load when this HTML file is opened directly.</p>
        <code>python server.py</code>
        <p>Then open <strong>http://localhost:8080/</strong>.</p>
      </section>
    </main>
  `;
}

function renderWrongServer(error) {
  document.body.innerHTML = `
    <main class="server-required">
      <section class="panel">
        <p class="eyebrow">Wrong or outdated server</p>
        <h1>Restart CropSmart</h1>
        <p>${error.message}. A previous Python server is probably still using this port.</p>
        <code>python server.py 8765</code>
        <p>Then open <strong>http://localhost:8765/</strong>.</p>
      </section>
    </main>
  `;
}

function renderLivePrice(livePrice) {
  if (!livePrice || !livePrice.available) {
    livePriceEl.textContent = "No quote";
    liveSourceEl.textContent = livePrice && livePrice.message ? livePrice.message : "Using signal estimate.";
    return;
  }

  livePriceEl.textContent = formatMoney(livePrice.price, livePrice.currency);
  const symbolText = livePrice.symbol ? ` (${livePrice.symbol})` : "";
  liveSourceEl.textContent = `${livePrice.label || "Today price"}: ${livePrice.source}${symbolText}`;
}

function renderAssumptions(scenario) {
  const live = scenario.liveData || {};
  const items = [
    ["Climate", labelFor("climate", scenario.climate)],
    ["Crop health", labelFor("cropCondition", scenario.cropCondition)],
    ["Economy", labelFor("economy", scenario.economy)],
    ["Policy", labelFor("policy", scenario.policy)],
    ["Inflation", percent(scenario.inflation)],
    ["Demand", percent(scenario.demandGrowth)],
    ["Supply risk", percent(scenario.supplyShortage)],
    ["Weather", live.temperature_max_avg ? `${live.temperature_max_avg} C max` : "Model profile"]
  ];

  assumptionsEl.innerHTML = "";
  items.forEach(([label, value]) => {
    const div = document.createElement("div");
    div.className = "assumption";
    div.innerHTML = `<span>${label}</span><strong>${value}</strong>`;
    assumptionsEl.appendChild(div);
  });
}

function renderDrivers(factors) {
  driversEl.innerHTML = "";
  factors
    .filter(item => Math.abs(item.value) > 0.01)
    .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
    .slice(0, 6)
    .forEach(item => {
      const direction = item.value >= 0 ? "raises" : "lowers";
      const li = document.createElement("li");
      li.textContent = `${item.name} ${direction} the forecast by about ${Math.abs(item.value * 100).toFixed(1)}%.`;
      driversEl.appendChild(li);
    });
}

function renderForecast(forecast, currency) {
  forecastEl.innerHTML = "";
  forecastChartEl.innerHTML = "";
  if (!forecast || !forecast.length) {
    forecastEl.innerHTML = '<p class="empty-state">No future-price data was returned.</p>';
    return;
  }

  const validForecast = forecast.filter(item => Number.isFinite(Number(item.price)));
  if (!validForecast.length) {
    forecastEl.innerHTML = '<p class="empty-state">Future-price values are invalid.</p>';
    return;
  }
  const max = Math.max(...validForecast.map(item => Number(item.price)));
  validForecast.forEach(item => {
    const row = document.createElement("div");
    row.className = "forecast-row";
    row.innerHTML = `<span>${item.date || `Month ${item.month}`}</span><strong>${formatMoney(item.price, item.currency || currency)}</strong>`;
    forecastEl.appendChild(row);

    const bar = document.createElement("div");
    bar.className = "bar";
    bar.style.height = `${Math.max(12, (item.price / max) * 100)}%`;
    bar.title = `${item.date || `Month ${item.month}`}: ${formatMoney(item.price, item.currency || currency)}`;
    bar.innerHTML = `<span>${item.month % 3 === 0 ? item.month : ""}</span>`;
    forecastChartEl.appendChild(bar);
  });
}

function renderHistory(history, currency) {
  historyChartEl.innerHTML = "";
  historySummaryEl.innerHTML = "";
  if (!history || !history.length) {
    historyChartEl.innerHTML = '<p class="empty-state">No historical-price data was returned.</p>';
    return;
  }

  const validHistory = history.filter(item => Number.isFinite(Number(item.price)));
  if (!validHistory.length) {
    historyChartEl.innerHTML = '<p class="empty-state">Historical-price values are invalid.</p>';
    return;
  }
  const prices = validHistory.map(item => Number(item.price));
  const max = Math.max(...prices);
  const min = Math.min(...prices);
  const first = validHistory[0];
  const last = validHistory[validHistory.length - 1];
  const change = first.price ? ((last.price - first.price) / first.price) * 100 : 0;

  validHistory.forEach((item, index) => {
    const bar = document.createElement("div");
    bar.className = "history-bar";
    bar.style.height = `${Math.max(8, (item.price / max) * 100)}%`;
    bar.title = `${item.date}: ${formatMoney(item.price, item.currency || currency)}`;
    if (index % 12 === 0) {
      bar.dataset.year = item.year;
    }
    historyChartEl.appendChild(bar);
  });

  [
    ["Start", `${first.date} / ${formatMoney(first.price, first.currency || currency)}`],
    ["Latest", `${last.date} / ${formatMoney(last.price, last.currency || currency)}`],
    ["10 year change", `${change >= 0 ? "+" : ""}${change.toFixed(1)}%`],
    ["Range", `${formatMoney(min, currency)} - ${formatMoney(max, currency)}`]
  ].forEach(([label, value]) => {
    const div = document.createElement("div");
    div.className = "assumption";
    div.innerHTML = `<span>${label}</span><strong>${value}</strong>`;
    historySummaryEl.appendChild(div);
  });
}

function renderSources(sources = [], errors = []) {
  sourceListEl.innerHTML = "";
  const visibleSources = sources.length ? sources : ["Saved model assumptions"];
  visibleSources.forEach(source => {
    const item = document.createElement("span");
    item.textContent = source;
    sourceListEl.appendChild(item);
  });
  if (errors.length) {
    const item = document.createElement("span");
    item.textContent = `${errors.length} source issue(s), fallback used where needed`;
    sourceListEl.appendChild(item);
  }
}

function buildNotes(result) {
  const today = result.todayPrice || result.livePrice;
  const live = today && today.type === "direct_quote"
    ? "Today's price starts from a direct public market quote."
    : today && today.type === "benchmark_estimate"
      ? "Today's price starts from a public benchmark adjusted by the model."
      : "Today's price is estimated from live signals because no public quote exists for this crop.";
  const history = result.historyType === "observed_benchmark"
    ? `The history contains observed monthly prices from ${result.historySource}.`
    : "No public history was available, so the history is a clearly labeled model fallback.";
  return `${live} ${history} Future values are predictions for planning, not guaranteed prices.`;
}

const staticRegionProfiles = {
  india: { name: "India", multiplier: 0.82, fx: { USD: 1, INR: 83, EUR: 0.92, GBP: 0.78 }, profile: { climate: "normal", economy: "stable", policy: "support", inflation: 0.06, currency: 0.10, fuel: 0.12, war: 0.08, shortage: 0.16 } },
  usa: { name: "United States", multiplier: 1.08, fx: { USD: 1, INR: 83, EUR: 0.92, GBP: 0.78 }, profile: { climate: "normal", economy: "strong", policy: "neutral", inflation: 0.03, currency: 0.03, fuel: 0.06, war: 0.05, shortage: 0.09 } },
  brazil: { name: "Brazil", multiplier: 0.94, fx: { USD: 1, INR: 83, EUR: 0.92, GBP: 0.78 }, profile: { climate: "drought", economy: "stable", policy: "neutral", inflation: 0.05, currency: 0.12, fuel: 0.10, war: 0.06, shortage: 0.13 } },
  china: { name: "China", multiplier: 1.02, fx: { USD: 1, INR: 83, EUR: 0.92, GBP: 0.78 }, profile: { climate: "normal", economy: "stable", policy: "neutral", inflation: 0.02, currency: 0.04, fuel: 0.07, war: 0.09, shortage: 0.11 } },
  eu: { name: "European Union", multiplier: 1.16, fx: { USD: 1, INR: 83, EUR: 0.92, GBP: 0.78 }, profile: { climate: "cold", economy: "stable", policy: "support", inflation: 0.03, currency: 0.04, fuel: 0.09, war: 0.11, shortage: 0.10 } },
  ukraine: { name: "Ukraine", multiplier: 0.78, fx: { USD: 1, INR: 83, EUR: 0.92, GBP: 0.78 }, profile: { climate: "normal", economy: "weak", policy: "neutral", inflation: 0.09, currency: 0.20, fuel: 0.18, war: 0.58, shortage: 0.27 } },
  nigeria: { name: "Nigeria", multiplier: 0.74, fx: { USD: 1, INR: 83, EUR: 0.92, GBP: 0.78 }, profile: { climate: "drought", economy: "weak", policy: "importOpen", inflation: 0.16, currency: 0.28, fuel: 0.22, war: 0.23, shortage: 0.30 } },
  australia: { name: "Australia", multiplier: 1.12, fx: { USD: 1, INR: 83, EUR: 0.92, GBP: 0.78 }, profile: { climate: "excellent", economy: "strong", policy: "neutral", inflation: 0.03, currency: 0.04, fuel: 0.07, war: 0.04, shortage: 0.08 } }
};

const effectValues = {
  climate: { normal: 0, drought: 0.18, flood: 0.15, cold: 0.08, excellent: -0.08 },
  cropCondition: { excellent: -0.09, good: -0.03, average: 0.03, poor: 0.14, damaged: 0.27 },
  economy: { strong: 0.06, stable: 0, weak: -0.04, recession: -0.09 },
  policy: { support: 0.08, neutral: 0, exportBan: -0.10, importOpen: -0.07, taxIncrease: 0.07 }
};

function buildStaticPrediction(cropKey, regionKey, currency, period) {
  const crop = options.crops.find(item => item.key === cropKey) || fallbackCrops[0];
  const region = staticRegionProfiles[regionKey] || staticRegionProfiles.india;
  const scenario = buildStaticScenario(crop, region, period);
  const modelBaseUsd = crop.base * region.multiplier;
  const todayUsd = staticPriceUsd(crop, region, scenario, 0);
  const futureUsd = staticPriceUsd(crop, region, scenario, period);
  const price = futureUsd * region.fx[currency];
  const factors = [
    { name: "Climate", value: effectValues.climate[scenario.climate] },
    { name: "Crop health", value: effectValues.cropCondition[scenario.cropCondition] },
    { name: "Economy", value: effectValues.economy[scenario.economy] },
    { name: "Policy", value: effectValues.policy[scenario.policy] },
    { name: "Inflation", value: scenario.inflation * 0.50 },
    { name: "Currency weakness", value: scenario.currencyWeakness * 0.35 },
    { name: "Demand growth", value: scenario.demandGrowth * 0.45 },
    { name: "Fuel and transport costs", value: scenario.fuelCost * 0.28 },
    { name: "War or conflict risk", value: scenario.warRisk * 0.22 },
    { name: "Supply shortage", value: scenario.supplyShortage * 0.62 },
    { name: `${period}-month forecast`, value: period * crop.volatility * 0.015 }
  ];

  return {
    price: roundMoney(price),
    futurePrice: { price: roundMoney(price), currency, periodMonths: period, unit: crop.unit, type: "future_forecast" },
    todayPrice: buildStaticTodayPrice(scenario, region, currency, crop, todayUsd, modelBaseUsd),
    currency,
    unit: crop.unit,
    confidence: staticConfidence(crop.volatility, scenario.warRisk, scenario.supplyShortage, effectValues.climate[scenario.climate], period),
    crop: crop.name,
    region: region.name,
    scenario,
    factors,
    totalEffect: Number(factors.reduce((sum, item) => sum + item.value, 0).toFixed(4)),
    modelInfo: { type: "Static browser demo model", trainingData: "Saved crop and region assumptions", metrics: null, observations: 0 },
    livePrice: buildStaticTodayPrice(scenario, region, currency, crop, todayUsd, modelBaseUsd),
    forecast12Months: buildStaticForecast(crop, region, currency, scenario, 12),
    forecast24Months: buildStaticForecast(crop, region, currency, scenario, 24),
    historical10Years: buildStaticHistory(crop, region, currency),
    historyType: "model_generated_fallback",
    historySource: "Static browser model",
    forecastNote: "Static hosted demo. Live market APIs require the Python server.",
    sources: ["Static browser model", "Saved crop and region assumptions"],
    errors: []
  };
}

function buildStaticScenario(crop, region, period) {
  const profile = region.profile;
  const cropCondition = crop.volatility > 0.30 ? "average" : crop.climateRisk > 0.14 ? "good" : "excellent";
  const scenario = {
    climate: profile.climate,
    cropCondition,
    economy: profile.economy,
    policy: profile.policy,
    inflation: profile.inflation,
    currencyWeakness: profile.currency,
    demandGrowth: Math.max(-0.20, crop.demand + (period >= 6 ? 0.02 : 0)),
    fuelCost: profile.fuel,
    warRisk: profile.war,
    supplyShortage: Math.min(0.70, profile.shortage + crop.climateRisk + crop.volatility * 0.10),
    liveData: { live_price_usd: null, sources: ["Static browser model"], errors: [] }
  };
  scenario.effects = {
    climate: effectValues.climate[scenario.climate],
    cropCondition: effectValues.cropCondition[scenario.cropCondition],
    economy: effectValues.economy[scenario.economy],
    policy: effectValues.policy[scenario.policy]
  };
  return scenario;
}

function staticPriceUsd(crop, region, scenario, month) {
  const seasonal = Math.sin((month % 12) * 2 * Math.PI / 12) * crop.volatility * 0.09;
  const trend = month * (0.004 + crop.demand * 0.012);
  const risk =
    scenario.effects.climate +
    scenario.effects.cropCondition +
    scenario.effects.economy +
    scenario.effects.policy +
    scenario.inflation * 0.50 +
    scenario.currencyWeakness * 0.35 +
    scenario.demandGrowth * 0.45 +
    scenario.fuelCost * 0.28 +
    scenario.warRisk * 0.22 +
    scenario.supplyShortage * 0.62;
  return Math.max(1, crop.base * region.multiplier * (1 + risk + trend + seasonal));
}

function buildStaticTodayPrice(scenario, region, currency, crop, todayUsd, modelBaseUsd) {
  return {
    available: true,
    price: roundMoney(todayUsd * region.fx[currency]),
    currency,
    unit: crop.unit,
    source: "Static hosted demo",
    symbol: null,
    quoteTime: new Date().toISOString(),
    note: "This free static version estimates today's price from saved crop and region assumptions. Live quotes require the Python server.",
    exactTodayQuote: false,
    type: "live_signal_estimate",
    label: "Estimated spot price",
    baseModelPrice: roundMoney(modelBaseUsd * region.fx[currency])
  };
}

function buildStaticForecast(crop, region, currency, scenario, months) {
  return Array.from({ length: months }, (_, index) => {
    const month = index + 1;
    return {
      month,
      date: addMonths(new Date(), month),
      price: roundMoney(staticPriceUsd(crop, region, scenario, month) * region.fx[currency]),
      currency
    };
  });
}

function buildStaticHistory(crop, region, currency) {
  const today = new Date();
  return Array.from({ length: 120 }, (_, index) => {
    const date = new Date(today.getFullYear() - 10, today.getMonth() + index, 1);
    const age = index - 119;
    const month = date.getMonth() + 1;
    const trend = age / 120;
    const cycle = Math.sin(index * 0.45 + crop.base) * crop.volatility * 0.18;
    const priceUsd = crop.base * region.multiplier * (1 + trend * 0.22 + cycle);
    return {
      date: `${date.getFullYear()}-${String(month).padStart(2, "0")}`,
      year: date.getFullYear(),
      month,
      price: roundMoney(Math.max(1, priceUsd * region.fx[currency])),
      currency,
      observed: false
    };
  });
}

function staticConfidence(volatility, warRisk, shortage, climateEffect, period) {
  const riskPenalty = volatility * 100 + warRisk * 18 + shortage * 14 + Math.abs(climateEffect * 30) + period * 1.2;
  return Math.max(42, Math.min(91, Math.round(96 - riskPenalty)));
}

function addMonths(start, offset) {
  const date = new Date(start.getFullYear(), start.getMonth() + offset, 1);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
}

function downloadStaticExport(prediction, format) {
  const filename = `${cropInput.value}-${regionInput.value}-prices.${format}`;
  const body = format === "json" ? JSON.stringify(prediction, null, 2) : toCsv(prediction);
  const type = format === "json" ? "application/json" : "text/csv";
  const url = URL.createObjectURL(new Blob([body], { type }));
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function toCsv(prediction) {
  const rows = [["type", "date", "price", "currency"]];
  prediction.historical10Years.forEach(item => rows.push(["history", item.date, item.price, item.currency]));
  prediction.forecast24Months.forEach(item => rows.push(["forecast", item.date, item.price, item.currency]));
  rows.push(["selected_future", `${prediction.futurePrice.periodMonths} months`, prediction.futurePrice.price, prediction.currency]);
  return rows.map(row => row.map(value => `"${String(value).replaceAll('"', '""')}"`).join(",")).join("\n");
}

function roundMoney(value) {
  return Math.round(Number(value) * 100) / 100;
}

async function exportData(format) {
  const params = new URLSearchParams({
    crop: cropInput.value,
    region: regionInput.value,
    currency: currencyInput.value,
    period: periodInput.value,
    format
  });
  const button = format === "json" ? exportJsonButton : exportCsvButton;
  const originalText = button.textContent;
  button.disabled = true;
  button.textContent = "Preparing...";
  try {
    if (!apiAvailable) {
      const prediction = lastPrediction || buildStaticPrediction(cropInput.value, regionInput.value, currencyInput.value, Number(periodInput.value));
      downloadStaticExport(prediction, format);
      return;
    }
    const response = await fetch(`/api/export?${params.toString()}`);
    if (!response.ok) throw new Error(`Export failed with HTTP ${response.status}`);
    const disposition = response.headers.get("Content-Disposition") || "";
    const filenameMatch = disposition.match(/filename="([^"]+)"/);
    const filename = filenameMatch
      ? filenameMatch[1]
      : `${cropInput.value}-${regionInput.value}-prices.${format}`;
    const url = URL.createObjectURL(await response.blob());
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  } catch (error) {
    notesEl.textContent = `${error.message}. Restart with python server.py 8765 and open http://localhost:8765/.`;
  } finally {
    button.disabled = false;
    button.textContent = originalText;
  }
}

function formatMoney(value, currency) {
  const amount = Number(value || 0);
  const maximumFractionDigits = amount >= 100 ? 0 : 2;
  return `${currencySymbols[currency] || `${currency} `}${amount.toLocaleString(undefined, { maximumFractionDigits })}`;
}

function labelFor(group, value) {
  return effects[group][value] || value || "Unknown";
}

function percent(value) {
  return `${Math.round(Number(value || 0) * 100)}%`;
}

function riskText(volatility) {
  if (volatility >= 0.30) return "High volatility";
  if (volatility >= 0.20) return "Medium volatility";
  return "Stable";
}

init();
