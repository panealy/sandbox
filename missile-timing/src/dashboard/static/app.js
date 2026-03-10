"use strict";

const HOURS = Array.from({ length: 24 }, (_, i) => `${String(i).padStart(2, "0")}:00`);
const DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

const CHART_COLORS = {
  blue: "rgba(96, 165, 250, 0.85)",
  blueLight: "rgba(96, 165, 250, 0.2)",
  orange: "rgba(251, 146, 60, 0.85)",
  grid: "rgba(45, 49, 72, 0.8)",
  text: "#94a3b8",
};

Chart.defaults.color = CHART_COLORS.text;
Chart.defaults.borderColor = CHART_COLORS.grid;

let globalData = null;
let cityCharts = {};

// ── Fetch data ─────────────────────────────────────────────────────────────
async function loadData() {
  const resp = await fetch("/api/analysis");
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

// ── Helpers ────────────────────────────────────────────────────────────────
function makeChart(id, type, labels, datasets, options = {}) {
  const ctx = document.getElementById(id);
  if (!ctx) return null;
  const existing = Chart.getChart(id);
  if (existing) existing.destroy();
  return new Chart(ctx, {
    type,
    data: { labels, datasets },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: CHART_COLORS.grid }, ticks: { color: CHART_COLORS.text } },
        y: { grid: { color: CHART_COLORS.grid }, ticks: { color: CHART_COLORS.text } },
      },
      ...options,
    },
  });
}

function heatColor(value, max) {
  if (max === 0) return "#1a1d27";
  const intensity = value / max;
  const r = Math.round(30 + intensity * 200);
  const g = Math.round(20 + intensity * 40);
  const b = Math.round(40 + intensity * 20);
  return `rgb(${r},${g},${b})`;
}

// ── Render stats ───────────────────────────────────────────────────────────
function renderStats(data) {
  document.getElementById("meta-info").textContent =
    `Generated: ${new Date(data.generated_at).toLocaleString()} · ` +
    `Range: ${data.date_range.from?.slice(0, 10) ?? "?"} → ${data.date_range.to?.slice(0, 10) ?? "?"}`;

  const grid = document.getElementById("stats-grid");
  const items = [
    ["Total Alerts", data.total_alerts.toLocaleString()],
    ["Days Tracked", data.total_days_tracked.toLocaleString()],
    ["Cities", Object.keys(data.cities).length.toLocaleString()],
    ["Peak Hour (IL)", `${String(data.global.peak_hour).padStart(2, "0")}:00`],
  ];
  grid.innerHTML = items
    .map(
      ([label, value]) =>
        `<div class="stat-card"><div class="label">${label}</div><div class="value">${value}</div></div>`
    )
    .join("");
}

// ── Global charts ──────────────────────────────────────────────────────────
function renderGlobalCharts(g) {
  makeChart("global-hourly-chart", "bar", HOURS, [
    {
      label: "P(alert)",
      data: g.hourly_probabilities,
      backgroundColor: HOURS.map((_, i) =>
        i === g.peak_hour ? CHART_COLORS.orange : CHART_COLORS.blue
      ),
      borderWidth: 0,
    },
  ]);

  makeChart("global-dow-chart", "bar", DOW, [
    {
      label: "Alerts",
      data: g.dow_counts,
      backgroundColor: CHART_COLORS.blue,
      borderWidth: 0,
    },
  ]);
}

// ── Heatmap ────────────────────────────────────────────────────────────────
function renderHeatmap(data) {
  const container = document.getElementById("heatmap-container");

  // Build hour×dow matrix from all cities
  const matrix = Array.from({ length: 24 }, () => Array(7).fill(0));
  for (const city of Object.values(data.cities)) {
    for (let h = 0; h < 24; h++) {
      for (let d = 0; d < 7; d++) {
        // We don't have per-city hour×dow, use global or approximate with counts
        // For now use global data which we already have
      }
    }
  }
  // Use the global hourly counts × dow (approximate via product)
  const g = data.global;
  const totalAlerts = data.total_alerts;
  for (let h = 0; h < 24; h++) {
    for (let d = 0; d < 7; d++) {
      matrix[h][d] = Math.round(
        ((g.hourly_counts[h] / totalAlerts) * (g.dow_counts[d] / totalAlerts)) *
          totalAlerts *
          7
      );
    }
  }

  const maxVal = Math.max(...matrix.flat());

  let html =
    '<table class="heatmap"><thead><tr><th>Hour</th>' +
    DOW.map((d) => `<th>${d}</th>`).join("") +
    "</tr></thead><tbody>";

  for (let h = 0; h < 24; h++) {
    html += `<tr><th>${String(h).padStart(2, "0")}:00</th>`;
    for (let d = 0; d < 7; d++) {
      const v = matrix[h][d];
      const bg = heatColor(v, maxVal);
      const textColor = v / maxVal > 0.5 ? "#f8fafc" : "#64748b";
      html += `<td style="background:${bg};color:${textColor}" title="${DOW[d]} ${String(h).padStart(2,'0')}:00 — ${v} alerts">${v || ""}</td>`;
    }
    html += "</tr>";
  }
  html += "</tbody></table>";
  container.innerHTML = html;
}

// ── City dropdown ──────────────────────────────────────────────────────────
function populateCityDropdown(cities) {
  const select = document.getElementById("city-select");
  const sorted = Object.keys(cities).sort();
  select.innerHTML = sorted
    .map((c) => `<option value="${c}">${c}</option>`)
    .join("");
  select.value = sorted[0] || "";
}

function renderCityCharts(cityData) {
  if (!cityData) return;
  makeChart("city-hourly-chart", "bar", HOURS, [
    {
      label: "P(alert)",
      data: cityData.hourly_probabilities,
      backgroundColor: HOURS.map((_, i) =>
        i === cityData.peak_hour ? CHART_COLORS.orange : CHART_COLORS.blue
      ),
      borderWidth: 0,
    },
  ]);
  makeChart("city-dow-chart", "bar", DOW, [
    {
      label: "Alerts",
      data: cityData.dow_counts,
      backgroundColor: CHART_COLORS.blue,
      borderWidth: 0,
    },
  ]);
}

// ── City search filter ─────────────────────────────────────────────────────
function setupCitySearch() {
  const search = document.getElementById("city-search");
  const select = document.getElementById("city-select");
  search.addEventListener("input", () => {
    const q = search.value.trim().toLowerCase();
    Array.from(select.options).forEach((opt) => {
      opt.hidden = q !== "" && !opt.value.toLowerCase().includes(q);
    });
    const firstVisible = Array.from(select.options).find((o) => !o.hidden);
    if (firstVisible) {
      select.value = firstVisible.value;
      renderCityCharts(globalData.cities[firstVisible.value]);
    }
  });
}

// ── City table ─────────────────────────────────────────────────────────────
let tableSortCol = "total";
let tableSortAsc = false;

function renderCityTable(cities) {
  const rows = Object.entries(cities).map(([city, d]) => ({
    city,
    total: d.total_alerts,
    days: d.days_tracked,
    peak: d.peak_hour,
    max_prob: Math.max(...d.hourly_probabilities),
  }));

  rows.sort((a, b) => {
    const av = a[tableSortCol];
    const bv = b[tableSortCol];
    const cmp = typeof av === "string" ? av.localeCompare(bv) : av - bv;
    return tableSortAsc ? cmp : -cmp;
  });

  const tbody = document.getElementById("city-table-body");
  tbody.innerHTML = rows
    .map(
      (r) =>
        `<tr>
          <td>${r.city}</td>
          <td>${r.total.toLocaleString()}</td>
          <td>${r.days}</td>
          <td><span class="peak-badge">${String(r.peak).padStart(2,"0")}:00</span></td>
          <td>${(r.max_prob * 100).toFixed(1)}%</td>
        </tr>`
    )
    .join("");
}

function setupTableSort(cities) {
  document.querySelectorAll("table.city-table th").forEach((th) => {
    th.addEventListener("click", () => {
      const col = th.dataset.col;
      if (tableSortCol === col) tableSortAsc = !tableSortAsc;
      else { tableSortCol = col; tableSortAsc = false; }
      renderCityTable(cities);
    });
  });
}

// ── Init ───────────────────────────────────────────────────────────────────
async function init() {
  try {
    const data = await loadData();
    globalData = data;

    renderStats(data);
    renderGlobalCharts(data.global);
    renderHeatmap(data);
    populateCityDropdown(data.cities);
    renderCityCharts(data.cities[document.getElementById("city-select").value]);
    renderCityTable(data.cities);
    setupTableSort(data.cities);
    setupCitySearch();

    document.getElementById("city-select").addEventListener("change", (e) => {
      renderCityCharts(data.cities[e.target.value]);
    });
  } catch (err) {
    document.body.innerHTML = `<div style="color:#f87171;padding:2rem;font-family:monospace">Error loading data: ${err.message}<br>Make sure the collector has run and data exists.</div>`;
  }
}

init();
