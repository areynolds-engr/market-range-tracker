const SYMBOLS = ["All", "NZD/USD", "GBP/USD", "AUD/USD", "BTC/USD"];
const PERIODS = [
  ["7 Days", 7],
  ["30 Days", 30],
  ["90 Days", 90],
  ["6 Months", 183],
  ["1 Year", 365],
  ["All", null],
];

let records = [];
let trendChart;

const $ = (id) => document.getElementById(id);
const fmt = (n, digits = 5) => Number(n).toLocaleString("en-US", { maximumFractionDigits: digits, minimumFractionDigits: digits });
const pct = (n) => `${Number(n).toFixed(3)}%`;
const displaySymbol = (symbol) => symbol.replace(/(NZD|GBP|AUD|BTC)USD/, "$1/USD");
const timeOnly = (iso) => iso ? new Date(iso).toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" }) : "";

async function loadData() {
  const response = await fetch("data/daily_ranges.json", { cache: "no-store" });
  const payload = await response.json();
  records = (payload.records || []).map((record) => ({ ...record, displaySymbol: displaySymbol(record.symbol) }));
  setupControls();
  render();
}

function setupControls() {
  $("symbolFilter").innerHTML = SYMBOLS.map((symbol) => `<option>${symbol}</option>`).join("");
  $("chartSymbol").innerHTML = SYMBOLS.filter((symbol) => symbol !== "All").map((symbol) => `<option>${symbol}</option>`).join("");
  $("periodButtons").innerHTML = PERIODS.map(([label], index) => `<button class="secondary ${index === 5 ? "active" : ""}" data-period="${label}">${label}</button>`).join("");
  ["symbolFilter", "dateFilter", "startDateFilter", "endDateFilter", "tableSearch"].forEach((id) => $(id).addEventListener("input", render));
  ["chartSymbol", "chartDate"].forEach((id) => $(id).addEventListener("input", renderTrend));
  const latest = latestDate(records);
  if (latest) $("chartDate").value = latest;
  $("periodButtons").addEventListener("click", (event) => {
    const button = event.target.closest("button");
    if (!button) return;
    document.querySelectorAll("#periodButtons button").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    const period = PERIODS.find(([label]) => label === button.dataset.period);
    if (period?.[1]) {
      const latest = latestDate(records);
      const start = new Date(`${latest}T00:00:00`);
      start.setDate(start.getDate() - period[1] + 1);
      $("startDateFilter").value = start.toISOString().slice(0, 10);
      $("endDateFilter").value = latest;
      $("dateFilter").value = "";
    } else {
      $("startDateFilter").value = "";
      $("endDateFilter").value = "";
      $("dateFilter").value = "";
    }
    render();
  });
  $("questionForm").addEventListener("submit", (event) => {
    event.preventDefault();
    $("answerBox").textContent = answerQuestion($("questionInput").value, filteredRecords());
  });
}

function latestDate(list) {
  return list.map((record) => record.date).sort().at(-1) || "";
}

function filteredRecords() {
  const symbol = $("symbolFilter").value;
  const exact = $("dateFilter").value;
  const start = $("startDateFilter").value;
  const end = $("endDateFilter").value;
  const search = $("tableSearch").value.trim().toLowerCase();
  return records.filter((record) => {
    if (symbol !== "All" && record.displaySymbol !== symbol) return false;
    if (exact && record.date !== exact) return false;
    if (start && record.date < start) return false;
    if (end && record.date > end) return false;
    if (search && !Object.values(record).join(" ").toLowerCase().includes(search)) return false;
    return true;
  });
}

function render() {
  const visible = filteredRecords();
  renderSummary();
  renderTrend();
  renderTable(visible);
  $("rowCount").textContent = `${visible.length} rows`;
}

function renderSummary() {
  const latest = latestDate(records);
  $("latestUpdate").textContent = latest || "No data yet";
  const latestRows = records.filter((record) => record.date === latest);
  $("summaryGrid").innerHTML = ["NZDUSD", "GBPUSD", "AUDUSD", "BTCUSD"].map((symbol) => {
    const record = latestRows.find((row) => row.symbol === symbol);
    if (!record) return `<article class="card"><h3>${displaySymbol(symbol)}</h3><p class="empty">No stored observation yet.</p></article>`;
    return `<article class="card">
      <h3>${record.displaySymbol}</h3>
      <time>${new Date(`${record.date}T00:00:00`).toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })}</time>
      <div class="metric-grid">
        <div class="metric"><span>High</span><b>${fmt(record.high)}</b></div>
        <div class="metric"><span>Low</span><b>${fmt(record.low)}</b></div>
        <div class="metric"><span>Range</span><b>${fmt(record.range)}</b></div>
        <div class="metric"><span>Range %</span><b>${pct(record.range_percent)}</b></div>
        <div class="metric"><span>High Time</span><b>${timeOnly(record.high_time)}</b></div>
        <div class="metric"><span>Low Time</span><b>${timeOnly(record.low_time)}</b></div>
      </div>
    </article>`;
  }).join("");
}

async function renderTrend() {
  const selectedSymbol = $("chartSymbol").value || "NZD/USD";
  const symbol = selectedSymbol.replace("/", "");
  const date = $("chartDate").value || latestDate(records);
  const range = records.find((record) => record.symbol === symbol && record.date === date);
  $("trendMeta").textContent = `${selectedSymbol} on ${date || "no date selected"}`;
  $("rangeLegend").innerHTML = range
    ? `<span class="range-pill high">08:00 high ${fmt(range.high)}</span><span class="range-pill low">08:00 low ${fmt(range.low)}</span>`
    : `<span class="range-pill">No stored 08:00 range for this selection</span>`;

  let candles = [];
  try {
    const response = await fetch(`data/intraday/${symbol}/${date}.json`, { cache: "no-store" });
    if (response.ok) {
      const payload = await response.json();
      candles = payload.records || [];
    }
  } catch (error) {
    candles = [];
  }
  drawTrendChart(candles, range);
}

function drawTrendChart(candles, range) {
  const ctx = $("trendChart");
  const labels = candles.map((candle) => timeOnly(candle.datetime));
  const closeData = candles.map((candle) => Number(candle.close));
  const highLine = range ? candles.map(() => Number(range.high)) : [];
  const lowLine = range ? candles.map(() => Number(range.low)) : [];
  if (trendChart) trendChart.destroy();
  trendChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Price",
          data: closeData,
          borderColor: "#171915",
          backgroundColor: "#171915",
          tension: 0.18,
          pointRadius: 0,
          borderWidth: 2,
        },
        {
          label: "08:00-08:30 High",
          data: highLine,
          borderColor: "#ba4a35",
          borderDash: [8, 6],
          pointRadius: 0,
          borderWidth: 2,
        },
        {
          label: "08:00-08:30 Low",
          data: lowLine,
          borderColor: "#0c7c66",
          borderDash: [8, 6],
          pointRadius: 0,
          borderWidth: 2,
        },
      ],
    },
    options: {
      responsive: false,
      maintainAspectRatio: false,
      scales: {
        x: {
          ticks: { maxTicksLimit: 24 },
          title: { display: true, text: "Time of day, America/New_York" },
        },
        y: { title: { display: true, text: "Price" } },
      },
      plugins: { legend: { position: "bottom" } },
    },
  });
  if (!candles.length) {
    $("trendMeta").textContent = `${$("trendMeta").textContent} - no intraday file yet`;
  }
}

function renderTable(list) {
  const rows = [...list].sort((a, b) => b.date.localeCompare(a.date) || a.symbol.localeCompare(b.symbol));
  $("historyBody").innerHTML = rows.map((record) => `<tr>
    <td>${record.date}</td>
    <td>${record.displaySymbol}</td>
    <td>${fmt(record.high)}</td>
    <td>${fmt(record.low)}</td>
    <td>${fmt(record.range)}</td>
    <td>${pct(record.range_percent)}</td>
    <td>${timeOnly(record.high_time)}</td>
    <td>${timeOnly(record.low_time)}</td>
    <td class="status-${record.status}">${record.status}</td>
    <td>${record.bar_count}</td>
  </tr>`).join("") || `<tr><td colspan="10" class="empty">No rows match the current filters.</td></tr>`;
}

function answerQuestion(question, list) {
  const q = question.toLowerCase();
  if (!list.length) return "There are no matching records in the current filter.";
  const bySymbol = list.reduce((groups, record) => {
    groups[record.symbol] ||= [];
    groups[record.symbol].push(record);
    return groups;
  }, {});
  const averages = Object.entries(bySymbol).map(([symbol, rows]) => ({
    symbol: displaySymbol(symbol),
    avgRange: rows.reduce((sum, row) => sum + Number(row.range_percent || 0), 0) / rows.length,
    count: rows.length,
  })).sort((a, b) => b.avgRange - a.avgRange);
  if (q.includes("largest") || q.includes("highest") || q.includes("average")) {
    const top = averages[0];
    return `${top.symbol} has the largest average range in the current filter: ${top.avgRange.toFixed(3)}% across ${top.count} observations.`;
  }
  if (q.includes("incomplete")) {
    const count = list.filter((record) => record.status !== "complete").length;
    return `${count} of ${list.length} matching observations are marked incomplete.`;
  }
  if (q.includes("before")) {
    const count = list.filter((record) => record.high_before_low).length;
    return `The high came before the low on ${count} of ${list.length} matching observations.`;
  }
  return `Current filter: ${list.length} observations. Average ranges: ${averages.map((item) => `${item.symbol} ${item.avgRange.toFixed(3)}%`).join(", ")}.`;
}

loadData().catch((error) => {
  $("summaryGrid").innerHTML = `<article class="card"><h3>Data unavailable</h3><p class="empty">${error.message}</p></article>`;
});
