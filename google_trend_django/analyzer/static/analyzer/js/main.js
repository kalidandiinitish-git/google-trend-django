/* ═══════════════════════════════════════════════
   TrendPulse — main.js
   Premium: particles, scroll reveals, charts,
   AI Summary, Trend Prediction, Multi-Keyword,
   World Heatmap
═══════════════════════════════════════════════ */

// ── Chart instances ──────────────────────────────
let timeChart    = null;
let regionChart  = null;
let compareChart = null;
let multiChart   = null;

// ── Chart.js global defaults ─────────────────────
Chart.defaults.color          = '#CBD5E1';
Chart.defaults.font.family    = "'Plus Jakarta Sans', sans-serif";
Chart.defaults.font.size      = 12;
Chart.defaults.font.weight    = 500;
Chart.defaults.plugins.legend.display = false;

// ── Colour palette ───────────────────────────────
const COLORS = {
  indigo:  '#6366F1',
  violet:  '#A78BFA',
  sky:     '#38BDF8',
  emerald: '#34D399',
  amber:   '#FBBF24',
  rose:    '#FB7185',
};

const BAR_PALETTE = [
  '#6366F1', '#818CF8', '#A78BFA',
  '#38BDF8', '#22D3EE', '#34D399',
  '#A3E635', '#FBBF24', '#FB923C',
  '#FB7185',
];

const MULTI_COLORS = [
  { line: '#6366F1', area: 'rgba(99,102,241,0.15)' },
  { line: '#A78BFA', area: 'rgba(167,139,250,0.12)' },
  { line: '#38BDF8', area: 'rgba(56,189,248,0.12)' },
  { line: '#34D399', area: 'rgba(52,211,153,0.12)' },
  { line: '#FBBF24', area: 'rgba(251,191,36,0.12)' },
];

const GRID_COLOR = 'rgba(255,255,255,0.06)';

// ════════════════════════════════════════════════
//  INIT
// ════════════════════════════════════════════════

window.addEventListener('DOMContentLoaded', () => {
  initParticles();
  initScrollReveal();
  checkStatus();

  document.getElementById('keyword').addEventListener('keydown', e => {
    if (e.key === 'Enter') runAnalysis();
  });
});

// ════════════════════════════════════════════════
//  PARTICLE SYSTEM
// ════════════════════════════════════════════════

function initParticles() {
  const canvas = document.getElementById('particle-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let particles = [];
  let w, h;
  const PARTICLE_COUNT = 60;

  function resize() {
    w = canvas.width  = window.innerWidth;
    h = canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  class Particle {
    constructor() { this.reset(); }
    reset() {
      this.x  = Math.random() * w;
      this.y  = Math.random() * h;
      this.vx = (Math.random() - 0.5) * 0.3;
      this.vy = (Math.random() - 0.5) * 0.3;
      this.r  = Math.random() * 1.8 + 0.5;
      this.alpha = Math.random() * 0.4 + 0.1;
      this.pulse = Math.random() * Math.PI * 2;
    }
    update() {
      this.x += this.vx;
      this.y += this.vy;
      this.pulse += 0.02;
      if (this.x < -10 || this.x > w + 10 || this.y < -10 || this.y > h + 10) this.reset();
    }
    draw() {
      const a = this.alpha * (0.5 + 0.5 * Math.sin(this.pulse));
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(99, 102, 241, ${a})`;
      ctx.fill();
    }
  }

  for (let i = 0; i < PARTICLE_COUNT; i++) particles.push(new Particle());

  function drawLines() {
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 150) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(99, 102, 241, ${0.06 * (1 - dist / 150)})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }
  }

  function animate() {
    ctx.clearRect(0, 0, w, h);
    particles.forEach(p => { p.update(); p.draw(); });
    drawLines();
    requestAnimationFrame(animate);
  }
  animate();
}

// ════════════════════════════════════════════════
//  SCROLL REVEAL
// ════════════════════════════════════════════════

function initScrollReveal() {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) entry.target.classList.add('visible');
      });
    },
    { threshold: 0.1, rootMargin: '0px 0px -40px 0px' }
  );
  document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
}

// ════════════════════════════════════════════════
//  API & STATUS
// ════════════════════════════════════════════════

async function checkStatus() {
  try {
    const d = await apiFetch('/api/status/');
    const badge = document.getElementById('mode-badge');
    const label = badge.querySelector('.badge-label');
    if (d.mode === 'real') {
      badge.className = 'mode-badge real';
      label.textContent = `Live Data (${d.provider})`;
    } else {
      badge.className = 'mode-badge demo';
      label.textContent = 'Demo Mode';
    }
  } catch (_) {}
}

function toggleCompare() {
  const on = document.getElementById('compare-toggle').checked;
  document.getElementById('compare-box').classList.toggle('hidden', !on);
  document.getElementById('card-compare').classList.toggle('hidden', !on);
  if (on) {
    document.getElementById('multi-toggle').checked = false;
    document.getElementById('multi-box').classList.add('hidden');
    document.getElementById('card-multi').classList.add('hidden');
  }
}

function toggleMulti() {
  const on = document.getElementById('multi-toggle').checked;
  document.getElementById('multi-box').classList.toggle('hidden', !on);
  document.getElementById('card-multi').classList.toggle('hidden', !on);
  if (on) {
    document.getElementById('compare-toggle').checked = false;
    document.getElementById('compare-box').classList.add('hidden');
    document.getElementById('card-compare').classList.add('hidden');
  }
}

// ── Main analysis (now includes AI Summary + Prediction) ──
async function runAnalysis() {
  const keyword   = document.getElementById('keyword').value.trim();
  const timeframe = document.getElementById('timeframe').value;

  if (!keyword) { showError('Please enter a keyword to analyze.'); return; }
  hideError();
  setLoading(true);

  try {
    const [trends, regions, related, summary] = await Promise.all([
      apiFetch(`/api/trends/?keyword=${enc(keyword)}&timeframe=${enc(timeframe)}`),
      apiFetch(`/api/regions/?keyword=${enc(keyword)}&timeframe=${enc(timeframe)}`),
      apiFetch(`/api/related/?keyword=${enc(keyword)}&timeframe=${enc(timeframe)}`),
      apiFetch(`/api/summary/?keyword=${enc(keyword)}&timeframe=${enc(timeframe)}`),
    ]);

    if (trends.error)  throw new Error(trends.error);
    if (regions.error) throw new Error(regions.error);

    renderTimeChart(trends);
    renderRegionChart(regions);
    renderRelatedTags(related);
    renderHeatmap(regions);
    renderSummary(summary);
    updateStats(trends, regions);
    updateModeBadge(trends.demo_mode);

  } catch (err) {
    showError(`Error: ${err.message}`);
  } finally {
    setLoading(false);
  }
}

// ── Keyword comparison ───────────────────────────
async function runCompare() {
  const kw1       = document.getElementById('kw1').value.trim();
  const kw2       = document.getElementById('kw2').value.trim();
  const timeframe = document.getElementById('timeframe').value;
  if (!kw1 || !kw2) { showError('Please enter both keywords to compare.'); return; }
  hideError(); setLoading(true);
  try {
    const data = await apiFetch(`/api/compare/?kw1=${enc(kw1)}&kw2=${enc(kw2)}&timeframe=${enc(timeframe)}`);
    if (data.error) throw new Error(data.error);
    renderCompareChart(data);
  } catch (err) { showError(`Compare error: ${err.message}`); }
  finally { setLoading(false); }
}

// ── Multi-keyword analysis ───────────────────────
async function runMulti() {
  const raw       = document.getElementById('multi-kw').value.trim();
  const timeframe = document.getElementById('timeframe').value;
  if (!raw) { showError('Please enter comma-separated keywords.'); return; }
  hideError(); setLoading(true);
  try {
    const data = await apiFetch(`/api/multi/?keywords=${enc(raw)}&timeframe=${enc(timeframe)}`);
    if (data.error) throw new Error(data.error);
    renderMultiChart(data);
  } catch (err) { showError(`Multi error: ${err.message}`); }
  finally { setLoading(false); }
}

// ── Fetch helper ─────────────────────────────────
async function apiFetch(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}
const enc = s => encodeURIComponent(s);

// ── Loading state ────────────────────────────────
function setLoading(on) {
  document.getElementById('btn-text').textContent = on ? 'Analyzing...' : 'Analyze';
  document.getElementById('btn-spinner').classList.toggle('hidden', !on);
  const arrow = document.querySelector('.btn-arrow');
  if (arrow) arrow.classList.toggle('hidden', on);
  document.getElementById('btn-analyze').disabled = on;
}

// ── Error helpers ────────────────────────────────
function showError(msg) {
  const el = document.getElementById('error-msg');
  el.textContent = msg; el.classList.remove('hidden');
}
function hideError() { document.getElementById('error-msg').classList.add('hidden'); }

// ── Mode badge ───────────────────────────────────
function updateModeBadge(isDemoMode) {
  const badge = document.getElementById('mode-badge');
  const label = badge.querySelector('.badge-label');
  if (!isDemoMode) { badge.className = 'mode-badge real'; label.textContent = 'Live Google Data'; }
  else { badge.className = 'mode-badge demo'; label.textContent = 'Demo Mode'; }
}

// ── Stats strip ──────────────────────────────────
function updateStats(trends, regions) {
  const strip = document.getElementById('stats-strip');
  strip.classList.remove('hidden');
  document.getElementById('stat-kw').textContent      = trends.keyword;
  document.getElementById('stat-peak').textContent    = trends.peak;
  document.getElementById('stat-avg').textContent     = trends.average;
  document.getElementById('stat-country').textContent = regions.countries?.[0] ?? '—';
  strip.querySelectorAll('.reveal').forEach(el => {
    el.classList.remove('visible');
    requestAnimationFrame(() => el.classList.add('visible'));
  });
}

// ════════════════════════════════════════════════
//  AI SUMMARY RENDERER
// ════════════════════════════════════════════════

function renderSummary(data) {
  const section = document.getElementById('summary-section');
  section.classList.remove('hidden');

  document.getElementById('summary-text').textContent = data.summary || '';

  const list = document.getElementById('insights-list');
  if (!data.insights || !data.insights.length) {
    list.innerHTML = '';
    return;
  }

  list.innerHTML = data.insights.map((ins, i) => `
    <div class="insight-item" style="animation-delay:${i * 0.1}s">
      <div class="insight-icon">${ins.icon}</div>
      <div class="insight-content">
        <div class="insight-title">${ins.title}</div>
        <div class="insight-text">${ins.text}</div>
      </div>
    </div>
  `).join('');
}

// ════════════════════════════════════════════════
//  WORLD HEATMAP RENDERER
// ════════════════════════════════════════════════

function renderHeatmap(data) {
  const ph    = document.getElementById('ph-heatmap');
  const grid  = document.getElementById('heatmap-grid');
  const legend = document.getElementById('heatmap-legend');

  if (ph) ph.style.display = 'none';
  grid.classList.remove('hidden');
  legend.classList.remove('hidden');

  const maxVal = Math.max(...data.values, 1);

  // Country flag emojis from ISO codes
  const getFlag = (iso) => {
    if (!iso || iso.length !== 2) return '🌐';
    return String.fromCodePoint(...[...iso.toUpperCase()].map(c => 0x1F1E6 + c.charCodeAt(0) - 65));
  };

  // Color interpolation based on value
  const getColor = (val, max) => {
    const t = val / max; // 0-1
    if (t > 0.75) return { bg: 'rgba(52, 211, 153, 0.15)', border: 'rgba(52,211,153,0.3)', bar: '#34D399', text: '#34D399' };
    if (t > 0.5)  return { bg: 'rgba(56, 189, 248, 0.12)', border: 'rgba(56,189,248,0.25)', bar: '#38BDF8', text: '#38BDF8' };
    if (t > 0.25) return { bg: 'rgba(167, 139, 250, 0.1)', border: 'rgba(167,139,250,0.2)', bar: '#A78BFA', text: '#A78BFA' };
    return { bg: 'rgba(99, 102, 241, 0.06)', border: 'rgba(99,102,241,0.15)', bar: '#6366F1', text: '#6366F1' };
  };

  grid.innerHTML = data.countries.map((country, i) => {
    const val = data.values[i];
    const iso = data.iso_codes?.[i] || '';
    const flag = getFlag(iso);
    const c = getColor(val, maxVal);
    const pct = (val / maxVal) * 100;
    return `
      <div class="heatmap-tile" style="background:${c.bg};border-color:${c.border};animation-delay:${i*0.06}s">
        <div class="heatmap-country">${flag} ${country}</div>
        <div class="heatmap-value" style="color:${c.text}">${val}</div>
        <div class="heatmap-bar" style="background:linear-gradient(90deg,${c.bar} ${pct}%,transparent ${pct}%)"></div>
      </div>
    `;
  }).join('');

  document.getElementById('heatmap-sub').textContent =
    `Top: ${data.countries[0] || '—'} (${data.values[0] || 0})`;
}

// ════════════════════════════════════════════════
//  CHART RENDERERS
// ════════════════════════════════════════════════

// ── Interest Over Time (with prediction) ─────────
function renderTimeChart(data) {
  hidePlaceholder('ph-time');
  document.getElementById('time-sub').textContent =
    `${data.keyword} · avg ${data.average} · peak ${data.peak}`;

  const ctx = document.getElementById('timeChart').getContext('2d');

  // Main area gradient
  const grad = ctx.createLinearGradient(0, 0, 0, 300);
  grad.addColorStop(0, 'rgba(99,102,241,0.25)');
  grad.addColorStop(0.5, 'rgba(56,189,248,0.1)');
  grad.addColorStop(1, 'rgba(56,189,248,0)');

  // Build labels: actual + forecast
  const allLabels = [...data.labels];
  const actualValues = [...data.values];
  const predValues = new Array(data.values.length).fill(null);

  // Prediction data
  const hasPrediction = data.predicted_values && data.predicted_values.length > 0;
  if (hasPrediction) {
    data.predicted_labels.forEach(l => allLabels.push(l));
    data.predicted_values.forEach(() => actualValues.push(null));
    // Bridge: last actual value connects to first prediction
    predValues[predValues.length - 1] = data.values[data.values.length - 1];
    data.predicted_values.forEach(v => predValues.push(v));
  }

  // Show prediction badge
  const predBadge = document.getElementById('pred-badge');
  if (predBadge) predBadge.classList.toggle('hidden', !hasPrediction);

  const datasets = [{
    label: data.keyword,
    data: actualValues,
    borderColor: COLORS.indigo,
    borderWidth: 3,
    backgroundColor: grad,
    fill: true,
    tension: 0.4,
    pointRadius: 0,
    pointHoverRadius: 7,
    pointHoverBackgroundColor: '#FFF',
    pointHoverBorderColor: COLORS.indigo,
    pointHoverBorderWidth: 3,
  }];

  if (hasPrediction) {
    datasets.push({
      label: 'Forecast',
      data: predValues,
      borderColor: COLORS.emerald,
      borderWidth: 2.5,
      borderDash: [8, 4],
      backgroundColor: 'rgba(52,211,153,0.06)',
      fill: true,
      tension: 0.4,
      pointRadius: 3,
      pointBackgroundColor: COLORS.emerald,
      pointBorderColor: '#030712',
      pointBorderWidth: 2,
      pointHoverRadius: 6,
    });
  }

  if (timeChart) timeChart.destroy();
  timeChart = new Chart(ctx, {
    type: 'line',
    data: { labels: allLabels, datasets },
    options: {
      ...baseChartOptions({ yLabel: 'Interest (0–100)', skipLabels: true }),
      plugins: {
        legend: {
          display: hasPrediction,
          labels: {
            color: '#CBD5E1',
            font: { family: "'Plus Jakarta Sans'", size: 12, weight: 600 },
            boxWidth: 14, usePointStyle: true, pointStyle: 'circle', padding: 20,
          }
        },
        tooltip: tooltipConfig(),
      }
    }
  });
}

// ── Interest by Region ───────────────────────────
function renderRegionChart(data) {
  hidePlaceholder('ph-region');
  document.getElementById('region-sub').textContent =
    `Top country: ${data.countries?.[0] ?? '—'}`;
  const ctx = document.getElementById('regionChart').getContext('2d');
  if (regionChart) regionChart.destroy();
  regionChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.countries,
      datasets: [{
        label: 'Interest',
        data: data.values,
        backgroundColor: data.values.map((_, i) => BAR_PALETTE[i % BAR_PALETTE.length]),
        borderRadius: 8, borderSkipped: false, barThickness: 24,
      }]
    },
    options: {
      ...baseChartOptions({}),
      indexAxis: 'y',
      scales: {
        x: { grid: { color: GRID_COLOR, drawBorder: false }, ticks: { color: '#E2E8F0', font: { size: 12, weight: 600 } } },
        y: { grid: { display: false }, ticks: { color: '#F8FAFC', font: { size: 13, weight: 700 }, padding: 10 } }
      }
    }
  });
}

// ── Related queries ──────────────────────────────
function renderRelatedTags(data) {
  const wrap = document.getElementById('related-tags');
  if (!data.queries || !data.queries.length) {
    wrap.innerHTML = '<div class="chart-placeholder"><div class="ph-pulse"></div><div class="ph-text">No related queries found</div></div>';
    return;
  }
  const max = Math.max(...data.values, 1);
  wrap.innerHTML = data.queries.map((q, i) => `
    <div class="query-tag" style="animation-delay:${i * 0.06}s">
      <div class="query-bar-wrap">
        <span class="query-text">${q}</span>
        <div class="query-bar">
          <div class="query-bar-fill" style="width:${(data.values[i] / max) * 100}%"></div>
        </div>
      </div>
      <span class="query-score">${data.values[i]}</span>
    </div>
  `).join('');
}

// ── Compare chart ────────────────────────────────
function renderCompareChart(data) {
  const ctx = document.getElementById('compareChart').getContext('2d');
  const grad1 = ctx.createLinearGradient(0, 0, 0, 280);
  grad1.addColorStop(0, 'rgba(99,102,241,0.2)'); grad1.addColorStop(1, 'rgba(99,102,241,0)');
  const grad2 = ctx.createLinearGradient(0, 0, 0, 280);
  grad2.addColorStop(0, 'rgba(167,139,250,0.2)'); grad2.addColorStop(1, 'rgba(167,139,250,0)');
  document.getElementById('compare-sub').textContent = `${data.kw1.name} vs ${data.kw2.name}`;
  if (compareChart) compareChart.destroy();
  compareChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.labels,
      datasets: [
        { label: data.kw1.name, data: data.kw1.values, borderColor: COLORS.indigo, backgroundColor: grad1, fill: true, tension: 0.4, borderWidth: 3, pointRadius: 0, pointHoverRadius: 6 },
        { label: data.kw2.name, data: data.kw2.values, borderColor: COLORS.violet, backgroundColor: grad2, fill: true, tension: 0.4, borderWidth: 3, pointRadius: 0, pointHoverRadius: 6 },
      ]
    },
    options: {
      ...baseChartOptions({ yLabel: 'Interest', skipLabels: true }),
      plugins: {
        legend: {
          display: true,
          labels: { color: '#CBD5E1', font: { size: 12, weight: 600 }, boxWidth: 14, usePointStyle: true, pointStyle: 'circle', padding: 20 }
        },
        tooltip: tooltipConfig(),
      }
    }
  });
}

// ── Multi-keyword chart ──────────────────────────
function renderMultiChart(data) {
  const ctx = document.getElementById('multiChart').getContext('2d');
  document.getElementById('multi-sub').textContent =
    data.datasets.map(d => d.name).join(' · ');

  const datasets = data.datasets.map((ds, i) => {
    const c = MULTI_COLORS[i % MULTI_COLORS.length];
    return {
      label: ds.name,
      data: ds.values,
      borderColor: c.line,
      backgroundColor: c.area,
      fill: true,
      tension: 0.4,
      borderWidth: 2.5,
      pointRadius: 0,
      pointHoverRadius: 6,
      pointHoverBackgroundColor: '#FFF',
    };
  });

  if (multiChart) multiChart.destroy();
  multiChart = new Chart(ctx, {
    type: 'line',
    data: { labels: data.labels, datasets },
    options: {
      ...baseChartOptions({ yLabel: 'Interest', skipLabels: true }),
      plugins: {
        legend: {
          display: true,
          labels: { color: '#CBD5E1', font: { size: 12, weight: 600 }, boxWidth: 14, usePointStyle: true, pointStyle: 'circle', padding: 16 }
        },
        tooltip: tooltipConfig(),
      }
    }
  });
}

// ── Shared chart options ─────────────────────────
function tooltipConfig() {
  return {
    backgroundColor: 'rgba(15,23,42,0.95)',
    borderColor: 'rgba(99,102,241,0.3)', borderWidth: 1,
    titleColor: '#A5B4FC', bodyColor: '#F1F5F9',
    padding: 16, cornerRadius: 12,
    titleFont: { family: "'Plus Jakarta Sans'", size: 13, weight: 700 },
    bodyFont:  { family: "'Plus Jakarta Sans'", size: 12, weight: 500 },
    displayColors: true, boxPadding: 6,
    callbacks: { label: ctx => ` ${ctx.dataset.label}: ${ctx.parsed.y ?? ctx.parsed.x}` }
  };
}

function baseChartOptions({ yLabel = '', skipLabels = false }) {
  return {
    responsive: true, maintainAspectRatio: false,
    animation: { duration: 1000, easing: 'easeInOutQuart' },
    interaction: { intersect: false, mode: 'index' },
    plugins: { tooltip: tooltipConfig(), legend: { display: false } },
    scales: {
      x: { grid: { color: GRID_COLOR, drawBorder: false }, ticks: { color: '#CBD5E1', font: { size: 12, weight: 500 }, maxRotation: 0, autoSkip: true, maxTicksLimit: skipLabels ? 8 : 20 } },
      y: { grid: { color: GRID_COLOR, drawBorder: false }, ticks: { color: '#CBD5E1', font: { size: 12, weight: 500 } }, min: 0, max: 100,
        title: { display: !!yLabel, text: yLabel, color: '#94A3B8', font: { family: "'Plus Jakarta Sans'", size: 12, weight: 600 } }
      }
    }
  };
}

// ── Utility ──────────────────────────────────────
function hidePlaceholder(id) {
  const el = document.getElementById(id);
  if (el) el.style.display = 'none';
}
