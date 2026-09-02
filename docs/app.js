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
let chart;

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
  $("periodButtons").innerHTML = PERIODS.map(([label], index) => `<button class="secondary ${index === 5 ? "active" : ""}" data-period="${label}">${label}</button>`).join("");
  ["symbolFilter", "dateFilter", "startDateFilter", "endDateFilter", "tableSearch"].forEach((id) => $(id).addEventListener("input", render));
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
  renderChart(visible);
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

function renderChart(list) {
  const ctx = $("rangeChart");
  const datasets = ["NZDUSD", "GBPUSD", "AUDUSD", "BTCUSD"].map((symbol, index) => {
    const colors = ["#0c7c66", "#ba4a35", "#3867a6", "#c2952e"];
    return {
      label: displaySymbol(symbol),
      data: list.filter((record) => record.symbol === symbol).map((record) => ({ x: record.date, y: Number(record.range_percent) })),
      borderColor: colors[index],
      backgroundColor: colors[index],
      tension: 0.25,
      pointRadius: 2,
    };
  });
  if (chart) chart.destroy();
  chart = new Chart(ctx, {
    type: "line",
    data: { datasets },
    options: {
      parsing: false,
      responsive: true,
      scales: { x: { type: "category" }, y: { title: { display: true, text: "Range %" } } },
      plugins: { legend: { position: "bottom" } },
    },
  });
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
