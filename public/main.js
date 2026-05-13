// ============================================================
//  AccountingBench — Application Logic
//  Depends on: data.js (must be loaded first)
// ============================================================

// ===== MOBILE CARD EXPAND / COLLAPSE =====

function toggleMCard(card) {
  const isExp = card.classList.contains('expanded');
  document.querySelectorAll('.m-lb-card.expanded').forEach(c => {
    if (c !== card) c.classList.remove('expanded');
  });
  card.classList.toggle('expanded', !isExp);
}

// ===== METHODOLOGY TABS =====

function showMeth(id, btn) {
  document.querySelectorAll('.meth-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.meth-nav-tab').forEach(t => t.classList.remove('active'));
  document.getElementById('meth-' + id).classList.add('active');
  btn.classList.add('active');
}

// ===== LEADERBOARD =====

function renderLeaderboard(sortKey) {
  const sorted    = [...lbData].sort((a, b) => b[sortKey] - a[sortKey]);
  const container = document.getElementById('leaderboard-rows');
  if (!container) return;

  container.innerHTML = sorted.map((m, i) => {
    const r      = i + 1;
    const cls    = r === 1 ? 'rank-1' : r === 2 ? 'rank-2' : r === 3 ? 'rank-3' : '';
    const badgeC = r === 1 ? 'var(--gold)' : r === 2 ? 'var(--silver)' : r === 3 ? 'var(--bronze)' : 'var(--text-dim)';
    const chip   = r === 1 ? '<span class="winner-chip">🏆 #1</span>' : '';
    const nStyle = m.n.includes('/') ? 'color:var(--amber);' : 'color:var(--text-dim);';

    const finVal  = sortKey === 'financial'
      ? `<span style="background:rgba(0,89,179,0.1);color:var(--wu-blue);font-weight:700;padding:2px 7px;font-size:14px;">${m.financial}%</span>`
      : `<span style="color:var(--wu-blue2);">${m.financial}%</span>`;
    const mgmtVal = sortKey === 'management'
      ? `<span style="background:rgba(13,122,78,0.1);color:var(--green);font-weight:700;padding:2px 7px;font-size:14px;">${m.management}%</span>`
      : `<span style="color:var(--green);">${m.management}%</span>`;
    const taxVal  = sortKey === 'tax'
      ? `<span style="background:rgba(146,64,14,0.1);color:var(--amber);font-weight:700;padding:2px 7px;font-size:14px;">${m.tax}%</span>`
      : `<span style="color:var(--amber);">${m.tax}%</span>`;

    return `<div class="leaderboard-row ${cls}">
      <div class="rank-badge" style="color:${badgeC};">${r}</div>
      <div class="model-info">
        <div class="model-name">${m.name} ${chip}</div>
        <div class="model-org">${m.org}</div>
      </div>
      <div class="score-cell">
        <div class="score-main" style="color:${m.oc};">${m.overall}%</div>
        <div class="score-bar-wrapper"><div class="score-bar-fill" style="width:${m.overall}%;background:${m.oc};"></div></div>
      </div>
      <div class="score-cat">${finVal}</div>
      <div class="score-cat">${mgmtVal}</div>
      <div class="score-cat">${taxVal}</div>
      <div class="score-cat" style="${nStyle}">${m.n}</div>
    </div>`;
  }).join('');
}

function sortLeaderboard(key, btn) {
  document.querySelectorAll('#page-leaderboard .ctrl-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');

  const headers = document.querySelectorAll('#full-leaderboard .lh-cell');
  const colMap  = { overall:2, financial:3, management:4, tax:5 };
  headers.forEach(h => h.classList.remove('lh-cell-active'));
  if (colMap[key] !== undefined && headers[colMap[key]]) {
    headers[colMap[key]].classList.add('lh-cell-active');
  }
  renderLeaderboard(key);
}

// ===== INTERACTIVE RADAR / BAR CHART =====

let activeChartType = 'radar';
let activeMetric    = 'overall';
let selectedModels  = [0, 1, 3]; // gpt-5.4, gpt-5.2, claude-sonnet-4-6

function updateRadar() {
  selectedModels = [];
  document.querySelectorAll('[data-model]').forEach(cb => {
    if (cb.checked) selectedModels.push(parseInt(cb.dataset.model));
  });
  drawChart();
  updateLegend();
}

function setChartType(type, btn) {
  activeChartType = type;
  btn.classList.add('active');
  drawChart();
}

function setMetric(metric, btn) {
  activeMetric = metric;
  btn.classList.add('active');
  drawChart();
  updateLegend();
}

function drawChart() {
  const canvas = document.getElementById('radarCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (activeChartType === 'radar') drawRadar(ctx, canvas);
  else drawBarChart(ctx, canvas);
}

function drawRadar(ctx, canvas) {
  const cx = canvas.width / 2, cy = canvas.height / 2, r = 170;
  const n = AXES.length;
  const angleStep = (Math.PI * 2) / n;

  // Grid rings
  ctx.strokeStyle = '#d6dce8'; ctx.lineWidth = 1;
  [0.2, 0.4, 0.6, 0.8, 1.0].forEach(scale => {
    ctx.beginPath();
    for (let i = 0; i < n; i++) {
      const a = i * angleStep - Math.PI / 2;
      const x = cx + Math.cos(a) * r * scale;
      const y = cy + Math.sin(a) * r * scale;
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.closePath(); ctx.stroke();
    ctx.fillStyle = '#8693a8'; ctx.font = '9px IBM Plex Mono,monospace';
    ctx.fillText(Math.round(scale * 100) + '%', cx + 3, cy - r * scale + 3);
  });

  // Axes + labels
  for (let i = 0; i < n; i++) {
    const a = i * angleStep - Math.PI / 2;
    ctx.beginPath(); ctx.moveTo(cx, cy);
    ctx.lineTo(cx + Math.cos(a) * r, cy + Math.sin(a) * r);
    ctx.strokeStyle = '#d6dce8'; ctx.lineWidth = 1; ctx.stroke();
    const lx = cx + Math.cos(a) * (r + 22), ly = cy + Math.sin(a) * (r + 22);
    ctx.fillStyle = '#003c78'; ctx.font = 'bold 10px IBM Plex Sans,sans-serif';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(AXES[i], lx, ly);
  }

  // Data polygons
  selectedModels.forEach(idx => {
    if (idx >= MODELS.length) return;
    const m = MODELS[idx];
    ctx.beginPath();
    AXIS_KEYS.forEach((key, i) => {
      const a   = i * angleStep - Math.PI / 2;
      const val = (m[key] || 0) / 100;
      const x   = cx + Math.cos(a) * r * val;
      const y   = cy + Math.sin(a) * r * val;
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.closePath();
    ctx.strokeStyle = m.color; ctx.lineWidth = 2; ctx.stroke();
    ctx.fillStyle = m.color + '33'; ctx.fill();

    AXIS_KEYS.forEach((key, i) => {
      const a   = i * angleStep - Math.PI / 2;
      const val = (m[key] || 0) / 100;
      const x   = cx + Math.cos(a) * r * val;
      const y   = cy + Math.sin(a) * r * val;
      ctx.beginPath(); ctx.arc(x, y, 3, 0, Math.PI * 2);
      ctx.fillStyle = m.color; ctx.fill();
    });
  });
}

function drawBarChart(ctx, canvas) {
  const key = activeMetric;
  const W = canvas.width, H = canvas.height;
  const ml = 120, mr = 20, mt = 20, mb = 30;
  const plotW = W - ml - mr, plotH = H - mt - mb;

  ctx.fillStyle = '#f0f2f6';
  ctx.fillRect(ml, mt, plotW, plotH);

  const models = selectedModels.length > 0
    ? selectedModels.map(i => MODELS[i]).sort((a, b) => b[key] - a[key])
    : MODELS.slice().sort((a, b) => b[key] - a[key]);

  const barH = Math.min(36, (plotH - (models.length - 1) * 6) / models.length);
  const gap  = (plotH - models.length * barH) / (models.length + 1);

  ctx.strokeStyle = '#d6dce8'; ctx.lineWidth = 0.5;
  [25, 50, 75, 100].forEach(v => {
    const x = ml + (v / 100) * plotW;
    ctx.beginPath(); ctx.moveTo(x, mt); ctx.lineTo(x, mt + plotH); ctx.stroke();
    ctx.fillStyle = '#8693a8'; ctx.font = '9px IBM Plex Mono,monospace';
    ctx.textAlign = 'center'; ctx.fillText(v + '%', x, mt + plotH + 14);
  });

  models.forEach((m, i) => {
    const val = m[key] || 0;
    const y   = mt + gap + i * (barH + gap);
    const w   = (val / 100) * plotW;
    ctx.fillStyle = m.color + 'cc';
    ctx.fillRect(ml, y, w, barH);
    ctx.fillStyle = '#1a1f2e'; ctx.font = '11px IBM Plex Mono,monospace';
    ctx.textAlign = 'right'; ctx.textBaseline = 'middle';
    ctx.fillText(m.name, ml - 8, y + barH / 2);
    ctx.fillStyle = '#fff'; ctx.font = 'bold 11px IBM Plex Mono,monospace';
    ctx.textAlign = 'right';
    if (w > 40) {
      ctx.fillText(val + '%', ml + w - 6, y + barH / 2);
    } else {
      ctx.fillStyle = m.color; ctx.textAlign = 'left';
      ctx.fillText(val + '%', ml + w + 4, y + barH / 2);
    }
  });
}

function updateLegend() {
  const legendEl = document.getElementById('radar-legend');
  if (!legendEl) return;
  const key = activeMetric;
  legendEl.innerHTML = selectedModels.map(idx => {
    if (idx >= MODELS.length) return '';
    const m = MODELS[idx];
    return `<div class="legend-item">
      <div class="legend-dot" style="background:${m.color};"></div>
      <span class="legend-name">${m.name}</span>
      <span class="legend-score" style="color:${m.color};">${m[key] || '—'}%</span>
    </div>`;
  }).join('');
}

// ===== DASHBOARD CHARTS =====

// ===== SCROLL ANIMATIONS =====

const observer = new IntersectionObserver(entries => {
  entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); });
}, { threshold: 0.08 });
document.querySelectorAll('.animate-on-scroll').forEach(el => observer.observe(el));

window.addEventListener('DOMContentLoaded', () => {
  // KPI gauge widths — must be set before the animation loop below reads el.style.width
  if (document.getElementById('kpi-top-gauge')) {
    const _scored = BENCHMARK_RESULTS.filter(m => m.overall > 0);
    const _top    = [..._scored].sort((a, b) => b.overall - a.overall)[0];
    const _avg    = _scored.reduce((s, m) => s + m.overall, 0) / _scored.length;
    const _avgPct = Math.round(_avg * 10) / 10;
    document.getElementById('kpi-top-score').textContent    = _top ? _top.overall + '%' : '—';
    document.getElementById('kpi-top-gauge').style.width    = _top ? _top.overall + '%' : '0%';
    document.getElementById('kpi-avg-score').textContent    = _avgPct + '%';
    document.getElementById('kpi-avg-gauge').style.width    = _avgPct + '%';
    document.getElementById('kpi-tasks').textContent        = BENCHMARK_META.totalTasks;
    document.getElementById('kpi-models').textContent       = BENCHMARK_RESULTS.length;
    document.getElementById('kpi-models-gauge').style.width = '100%';
  }

  // fw-fills
  document.querySelectorAll('.fw-fill').forEach(el => {
    const w = el.style.getPropertyValue('--fw-w');
    el.style.setProperty('--fw-w', '0%');
    const io = new IntersectionObserver(entries => {
      entries.forEach(e => { if (e.isIntersecting) { el.style.setProperty('--fw-w', w); io.disconnect(); } });
    }, { threshold: 0.2 });
    io.observe(el);
  });

  // KPI gauges
  document.querySelectorAll('.kpi-gauge-fill').forEach(el => {
    const w = el.style.width;
    el.style.width = '0%';
    const io = new IntersectionObserver(entries => {
      entries.forEach(e => { if (e.isIntersecting) { el.style.width = w; io.disconnect(); } });
    }, { threshold: 0.3 });
    io.observe(el);
  });

  // tok-bar-fill
  document.querySelectorAll('.tok-bar-fill').forEach((el, i) => {
    const targetW = el.style.width;
    el.style.width = '0%';
    el.style.transition = `width 0.9s cubic-bezier(0.4,0,0.2,1) ${0.08 + i * 0.06}s`;
    const io = new IntersectionObserver(entries => {
      entries.forEach(e => { if (e.isIntersecting) { el.style.width = targetW; io.disconnect(); } });
    }, { threshold: 0.2 });
    io.observe(el);
  });

  // token bars (CSS variable)
  document.querySelectorAll('.token-bar-in, .token-bar-out').forEach(el => {
    const w = el.style.getPropertyValue('--tw');
    el.style.setProperty('--tw', '0%');
    const io = new IntersectionObserver(entries => {
      entries.forEach(e => { if (e.isIntersecting) { el.style.setProperty('--tw', w); io.disconnect(); } });
    }, { threshold: 0.2 });
    io.observe(el);
  });
});

// Bar fill animation on scroll-in
const barObs = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      e.target.querySelectorAll('.bar-fill, .score-bar-fill').forEach(bar => {
        const t = bar.style.width;
        bar.style.width = '0%';
        setTimeout(() => bar.style.width = t, 80);
      });
    }
  });
}, { threshold: 0.15 });
document.querySelectorAll('.chart-card, .leaderboard-container').forEach(el => barObs.observe(el));

// ===== COST-EFFICIENCY SCATTER CHART =====

// ── Shared scatter helpers ────────────────────────────────────

function _setupScatterCanvas(canvasId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return null;
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width  = rect.width  * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);
  const W = rect.width, H = rect.height;
  const ml = 52, mr = 28, mt = 28, mb = 50;
  return { ctx, W, H, ml, mr, mt, mb, pw: W - ml - mr, ph: H - mt - mb };
}

function _drawScatterYGridlines(ctx, toY, minScore, maxScore, ml, pw) {
  [45, 50, 55, 60, 65, 70, 75].forEach(s => {
    if (s < minScore || s > maxScore) return;
    const y = toY(s), isMajor = (s === 50 || s === 70);
    ctx.strokeStyle = isMajor ? 'rgba(0,60,120,0.22)' : 'rgba(0,60,120,0.09)';
    ctx.lineWidth   = isMajor ? 1.2 : 0.7;
    ctx.beginPath(); ctx.moveTo(ml, y); ctx.lineTo(ml + pw, y); ctx.stroke();
    ctx.fillStyle = isMajor ? '#4a5568' : '#9aabb8';
    ctx.font = isMajor ? 'bold 10px IBM Plex Mono,monospace' : '9px IBM Plex Mono,monospace';
    ctx.textAlign = 'right'; ctx.textBaseline = 'middle';
    ctx.fillText(s + '%', ml - 6, y);
  });
}

function _drawScatterYLabel(ctx, mt, ph) {
  ctx.save(); ctx.translate(16, mt + ph / 2); ctx.rotate(-Math.PI / 2);
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.font = 'bold 12px IBM Plex Sans,sans-serif'; ctx.fillStyle = '#003c78';
  ctx.fillText('Score (%)', 0, 0); ctx.restore();
}

function _drawScatterXTicks(ctx, ticks, tickLabels, toX, minLogX, maxLogX, mt, ph) {
  ticks.forEach((v, i) => {
    const logV = Math.log10(v);
    if (logV < minLogX || logV > maxLogX) return;
    const x = toX(v);
    ctx.strokeStyle = 'rgba(0,60,120,0.13)'; ctx.lineWidth = 0.8;
    ctx.beginPath(); ctx.moveTo(x, mt); ctx.lineTo(x, mt + ph); ctx.stroke();
    ctx.strokeStyle = 'rgba(0,60,120,0.35)'; ctx.lineWidth = 1.2;
    ctx.beginPath(); ctx.moveTo(x, mt + ph); ctx.lineTo(x, mt + ph + 5); ctx.stroke();
    ctx.fillStyle = '#4a5568'; ctx.font = 'bold 9px IBM Plex Mono,monospace';
    ctx.textAlign = 'center'; ctx.textBaseline = 'top';
    ctx.fillText(tickLabels[i], x, mt + ph + 8);
  });
}

function _drawScatterDots(ctx, positions) {
  positions.forEach(({ m, x, y }) => {
    ctx.beginPath(); ctx.arc(x, y, 9, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(0,0,0,0.08)'; ctx.fill();
    ctx.beginPath(); ctx.arc(x, y, 8, 0, Math.PI * 2);
    ctx.fillStyle = m.color; ctx.fill();
    ctx.strokeStyle = '#fff'; ctx.lineWidth = 2; ctx.stroke();
  });
}

function _initScatterTooltip({ wrapId, tipId, getPositions, getMeta, buildContent, tipHeight }) {
  const wrap = document.getElementById(wrapId);
  if (!wrap) return;
  const tip = document.createElement('div');
  tip.id = tipId;
  tip.className = 'chart-tip';
  wrap.appendChild(tip);
  wrap.addEventListener('mousemove', e => {
    const rect = wrap.getBoundingClientRect();
    const mx = e.clientX - rect.left, my = e.clientY - rect.top;
    let closest = null, minDist = 20;
    getPositions().forEach(p => {
      const dist = Math.sqrt((p.x - mx) ** 2 + (p.y - my) ** 2);
      if (dist < minDist) { minDist = dist; closest = p; }
    });
    if (closest) {
      const m = closest.m, meta = getMeta(m.name);
      tip.style.borderTopColor = m.color;
      tip.innerHTML = buildContent(m, meta);
      let tx = mx + 14, ty = my - 10;
      if (tx + 200 > rect.width)  tx = mx - 214;
      if (ty + tipHeight > rect.height) ty = my - (tipHeight + 10);
      tip.style.left = tx + 'px'; tip.style.top = ty + 'px';
      tip.style.display = 'block'; wrap.style.cursor = 'crosshair';
    } else {
      tip.style.display = 'none'; wrap.style.cursor = 'default';
    }
  });
  wrap.addEventListener('mouseleave', () => {
    tip.style.display = 'none'; wrap.style.cursor = 'default';
  });
}

// ===== COST vs SCORE SCATTER CHART =====

let scatterPositions = [];

function drawCostScatter() {
  const c = _setupScatterCanvas('costScatterCanvas');
  if (!c) return;
  if (!SCATTER_MODELS.some(m => m.score !== null && m.cost !== null)) return;
  const { ctx, W, H, ml, mt, pw, ph } = c;

  const validCosts  = SCATTER_MODELS.filter(m => m.cost).map(m => m.cost);
  const validScores = SCATTER_MODELS.filter(m => m.score).map(m => m.score);
  const minCostLog  = Math.log10(Math.min(...validCosts)) - 0.2;
  const maxCostLog  = Math.log10(Math.max(...validCosts)) + 0.2;
  const minScore    = Math.min(...validScores) - 5;
  const maxScore    = Math.max(...validScores) + 6;

  const toX = v => ml + ((Math.log10(v) - minCostLog) / (maxCostLog - minCostLog)) * pw;
  const toY = s => mt + ((maxScore - s) / (maxScore - minScore)) * ph;

  ctx.fillStyle = '#f0f2f6'; ctx.fillRect(ml, mt, pw, ph);
  _drawScatterYGridlines(ctx, toY, minScore, maxScore, ml, pw);
  _drawScatterYLabel(ctx, mt, ph);
  _drawScatterXTicks(ctx,
    [0.0003, 0.001, 0.003, 0.01, 0.03],
    ['$0.0003', '$0.001', '$0.003', '$0.01', '$0.03'],
    toX, minCostLog, maxCostLog, mt, ph);

  ctx.fillStyle = '#003c78'; ctx.font = 'bold 12px IBM Plex Sans,sans-serif';
  ctx.textAlign = 'center'; ctx.textBaseline = 'bottom';
  ctx.fillText('Cost per Task (USD, log scale)', ml + pw / 2, H - 3);

  scatterPositions = [];
  SCATTER_MODELS.forEach(m => {
    if (m.score === null || m.cost === null) return;
    scatterPositions.push({ m, x: toX(m.cost), y: toY(m.score) });
  });
  _drawScatterDots(ctx, scatterPositions);

  const SHORT = {
    'grok-4-fast-reasoning': 'grok-4-fast',
    'claude-opus-4-6':       'claude-opus-4-6',
    'claude-sonnet-4-6':     'claude-sonnet-4-6',
    'DeepSeek-V3.2-2':       'DeepSeek-V3.2-2',
  };
  _drawScatterLabels(ctx, scatterPositions, { ml, pw, mt, ph, W, SHORT });
}

function initScatterTooltip() {
  _initScatterTooltip({
    wrapId:    'costScatterWrap',
    tipId:     'scatterTip',
    getPositions: () => scatterPositions,
    getMeta:   name => SCATTER_META[name] || {},
    tipHeight: 120,
    buildContent: (m, meta) => {
      const costFmt = m.cost < 0.001 ? '$' + m.cost.toFixed(5) : '$' + m.cost.toFixed(4);
      return `
        <div style="font-weight:700;font-size:13px;margin-bottom:6px;color:${m.color};">${m.name}</div>
        <div style="color:rgba(255,255,255,0.6);font-size:10px;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;">${meta.org || ''} · Rank #${meta.rank || '—'}</div>
        <div style="display:grid;grid-template-columns:auto auto;gap:2px 14px;">
          <span style="color:rgba(255,255,255,0.6);">Score</span>
          <span style="font-family:'IBM Plex Mono',monospace;font-weight:700;">${m.score}%</span>
          <span style="color:rgba(255,255,255,0.6);">Cost / Task</span>
          <span style="font-family:'IBM Plex Mono',monospace;font-weight:700;">${costFmt}</span>
          <span style="color:rgba(255,255,255,0.6);">Tokens / Task</span>
          <span style="font-family:'IBM Plex Mono',monospace;font-weight:700;">${(meta.tokTask || 0).toLocaleString()}</span>
        </div>`;
    },
  });
}

// ===== SPEED vs SCORE SCATTER CHART =====

let speedPositions = [];

function drawSpeedScatter() {
  const c = _setupScatterCanvas('speedScatterCanvas');
  if (!c) return;
  const { ctx, W, H, ml, mt, pw, ph } = c;

  const validSpeeds = SPEED_MODELS_CLEAN.filter(m => m.speed > 0).map(m => m.speed);
  const validScores = SPEED_MODELS_CLEAN.filter(m => m.speed > 0).map(m => m.score);
  if (validSpeeds.length === 0) return;
  const minSpeedLog = Math.log10(Math.min(...validSpeeds)) - 0.15;
  const maxSpeedLog = Math.log10(Math.max(...validSpeeds)) + 0.15;
  const minScore    = Math.min(...validScores) - 5;
  const maxScore    = Math.max(...validScores) + 6;

  const toX = v => ml + ((Math.log10(v) - minSpeedLog) / (maxSpeedLog - minSpeedLog)) * pw;
  const toY = s => mt + ((maxScore - s) / (maxScore - minScore)) * ph;

  ctx.fillStyle = '#f0f2f6'; ctx.fillRect(ml, mt, pw, ph);
  _drawScatterYGridlines(ctx, toY, minScore, maxScore, ml, pw);
  _drawScatterYLabel(ctx, mt, ph);
  _drawScatterXTicks(ctx,
    [30, 50, 100, 200, 500, 1000],
    ['30', '50', '100', '200', '500', '1,000'],
    toX, minSpeedLog, maxSpeedLog, mt, ph);

  ctx.fillStyle = '#003c78'; ctx.font = 'bold 12px IBM Plex Sans,sans-serif';
  ctx.textAlign = 'center'; ctx.textBaseline = 'bottom';
  ctx.fillText('Output Speed (tokens/sec, log scale)', ml + pw / 2, H - 3);

  speedPositions = [];
  SPEED_MODELS_CLEAN.filter(m => m.speed > 0).forEach(m => speedPositions.push({ m, x: toX(m.speed), y: toY(m.score) }));
  _drawScatterDots(ctx, speedPositions);
  _drawScatterLabels(ctx, speedPositions, { ml, pw, mt, ph, W });
}

function initSpeedTooltip() {
  _initScatterTooltip({
    wrapId:    'speedScatterWrap',
    tipId:     'speedTip',
    getPositions: () => speedPositions,
    getMeta:   name => SPEED_META[name] || {},
    tipHeight: 110,
    buildContent: (m, meta) => {
      const speedFmt = m.speed >= 100 ? m.speed.toFixed(0) : m.speed.toFixed(1);
      return `
        <div style="font-weight:700;font-size:13px;margin-bottom:6px;color:${m.color};">${m.name}</div>
        <div style="color:rgba(255,255,255,0.6);font-size:10px;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;">${meta.org || ''} · Rank #${meta.rank || '—'}</div>
        <div style="display:grid;grid-template-columns:auto auto;gap:2px 14px;">
          <span style="color:rgba(255,255,255,0.6);">Score</span>
          <span style="font-family:'IBM Plex Mono',monospace;font-weight:700;">${m.score}%</span>
          <span style="color:rgba(255,255,255,0.6);">Output Speed</span>
          <span style="font-family:'IBM Plex Mono',monospace;font-weight:700;">${speedFmt} t/s</span>
        </div>`;
    },
  });
}

// ── Shared: draw overlap-free labels for scatter charts ──
function _drawScatterLabels(ctx, positions, { ml, pw, mt, ph, W, SHORT = {} }) {
  const FONT_SIZE = W < 500 ? 9 : 11;
  const FONT_STR  = `bold ${FONT_SIZE}px IBM Plex Sans,sans-serif`;
  const LINE_H = FONT_SIZE + 7, PAD = 12, MARGIN = 4;

  ctx.font = FONT_STR;
  const items = positions.map(({ m, x, y }) => {
    const label = SHORT[m.name] || m.name;
    const tw    = ctx.measureText(label).width;
    return { x, y, label, color: m.color, tw };
  });

  items.forEach(d => {
    const wouldOverflow = d.x + PAD + d.tw + MARGIN > ml + pw;
    d.side = wouldOverflow ? 'right' : 'left';
    d.lx   = d.side === 'left' ? d.x + PAD : d.x - PAD;
    d.ly   = d.y;
  });

  const boxes = [];
  items.forEach(d => {
    const bx1 = d.side === 'left' ? d.lx - 2       : d.lx - d.tw - 2;
    const bx2 = d.side === 'left' ? d.lx + d.tw + 2 : d.lx + 2;
    let by1 = d.ly - FONT_SIZE / 2 - 2;
    let by2 = d.ly + FONT_SIZE / 2 + 2;
    for (let attempt = 0; attempt < 30; attempt++) {
      let conflict = false;
      for (const b of boxes) {
        if (bx1 < b.x2 + MARGIN && bx2 + MARGIN > b.x1 && by1 < b.y2 + MARGIN && by2 + MARGIN > b.y1) {
          conflict = true; break;
        }
      }
      if (!conflict) break;
      const dir  = attempt % 2 === 0 ? 1 : -1;
      const step = LINE_H * Math.ceil((attempt + 1) / 2);
      by1 = d.ly - FONT_SIZE / 2 - 2 + dir * step;
      by2 = d.ly + FONT_SIZE / 2 + 2 + dir * step;
      d.ly += dir * step;
    }
    if (d.ly < mt + FONT_SIZE / 2 + 2) d.ly = mt + FONT_SIZE / 2 + 2;
    if (d.ly > mt + ph - FONT_SIZE / 2 - 2) d.ly = mt + ph - FONT_SIZE / 2 - 2;
    boxes.push({ x1: bx1, y1: by1, x2: bx2, y2: by2 });
  });

  items.forEach(d => {
    ctx.font = FONT_STR;
    if (Math.abs(d.y - d.ly) > 6) {
      const ex = d.side === 'left' ? d.x + 9 : d.x - 9;
      const ax = d.side === 'left' ? d.lx - 2 : d.lx + 2;
      ctx.strokeStyle = d.color + '99'; ctx.lineWidth = 0.9;
      ctx.setLineDash([2, 3]);
      ctx.beginPath(); ctx.moveTo(ex, d.y); ctx.lineTo(ax, d.ly); ctx.stroke();
      ctx.setLineDash([]);
    }
    const bx = d.side === 'left' ? d.lx - 3 : d.lx - d.tw - 3;
    ctx.fillStyle = 'rgba(247,248,250,0.92)';
    ctx.fillRect(bx, d.ly - FONT_SIZE / 2 - 3, d.tw + 6, FONT_SIZE + 6);
    ctx.fillStyle = d.color;
    ctx.textAlign = d.side === 'left' ? 'left' : 'right';
    ctx.textBaseline = 'middle';
    ctx.fillText(d.label, d.lx, d.ly);
  });
}

// ===== CONFIDENCE CALIBRATION CHART =====

const CALIB_MODELS = Object.keys(CALIB_DATA);
let calibSelected   = new Set(['gpt-5.4', 'gpt-5.2', 'claude-sonnet-4-6']);
let calibHoverModel = null, calibHoverPt = null;

function buildCalibSelector() {
  const sel = document.getElementById('calibSelector');
  if (!sel) return;
  sel.innerHTML = '';
  CALIB_MODELS.forEach(m => {
    const active = calibSelected.has(m);
    const btn    = document.createElement('button');
    btn.dataset.model = m;
    btn.className = 'calib-btn';
    btn.style.cssText = `border:1.5px solid ${active ? CALIB_COLORS[m] : 'var(--border)'};background:${active ? CALIB_COLORS[m] + '18' : 'transparent'};color:${active ? CALIB_COLORS[m] : 'var(--text-dim)'};font-weight:${active ? '700' : '400'};`;
    const dot = document.createElement('span');
    dot.className = 'calib-dot';
    dot.style.cssText = `background:${CALIB_COLORS[m]};opacity:${active ? 1 : 0.35};`;
    btn.appendChild(dot);
    btn.appendChild(document.createTextNode(m));
    btn.addEventListener('click', () => {
      calibSelected.has(m) ? calibSelected.delete(m) : calibSelected.add(m);
      buildCalibSelector();
      drawCalib();
    });
    sel.appendChild(btn);
  });
}

function drawCalib() {
  const canvas = document.getElementById('calibCanvas');
  if (!canvas) return;
  const ctx    = canvas.getContext('2d');
  const dpr    = window.devicePixelRatio || 1;
  const W_CSS  = canvas.parentElement.clientWidth;
  const H_CSS  = Math.max(260, Math.min(380, W_CSS * 0.52));
  canvas.width  = W_CSS * dpr;
  canvas.height = H_CSS * dpr;
  canvas.style.height = H_CSS + 'px';
  ctx.scale(dpr, dpr);
  const W = W_CSS, H = H_CSS;

  const ml = 48, mr = 20, mt = 20, mb = 42;
  const pw = W - ml - mr, ph = H - mt - mb;
  const toX = v => ml + v * pw;
  const toY = v => mt + (1 - v / 100) * ph;

  ctx.fillStyle = '#f0f2f6'; ctx.fillRect(ml, mt, pw, ph);

  [0, 20, 40, 60, 80, 100].forEach(s => {
    const y = toY(s), isMajor = (s === 0 || s === 50 || s === 100);
    ctx.strokeStyle = isMajor ? 'rgba(0,60,120,0.2)' : 'rgba(0,60,120,0.08)';
    ctx.lineWidth   = isMajor ? 1.0 : 0.6;
    ctx.beginPath(); ctx.moveTo(ml, y); ctx.lineTo(ml + pw, y); ctx.stroke();
    ctx.fillStyle = isMajor ? '#4a5568' : '#9aabb8';
    ctx.font = isMajor ? 'bold 9px IBM Plex Mono,monospace' : '8.5px IBM Plex Mono,monospace';
    ctx.textAlign = 'right'; ctx.textBaseline = 'middle';
    ctx.fillText(s + '%', ml - 5, y);
  });
  [0, 0.2, 0.4, 0.6, 0.8, 1.0].forEach(v => {
    const x = toX(v);
    ctx.strokeStyle = 'rgba(0,60,120,0.1)'; ctx.lineWidth = 0.6;
    ctx.beginPath(); ctx.moveTo(x, mt); ctx.lineTo(x, mt + ph); ctx.stroke();
    ctx.fillStyle = '#4a5568'; ctx.font = 'bold 9px IBM Plex Mono,monospace';
    ctx.textAlign = 'center'; ctx.textBaseline = 'top';
    ctx.fillText(v.toFixed(1), x, mt + ph + 6);
  });

  // Perfect-calibration reference line
  ctx.strokeStyle = 'rgba(0,0,0,0.18)'; ctx.lineWidth = 1; ctx.setLineDash([5, 4]);
  ctx.beginPath(); ctx.moveTo(toX(0), toY(0)); ctx.lineTo(toX(1), toY(100)); ctx.stroke();
  ctx.setLineDash([]);

  // Axis labels
  ctx.save(); ctx.translate(14, mt + ph / 2); ctx.rotate(-Math.PI / 2);
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.font = 'bold 12px IBM Plex Sans,sans-serif'; ctx.fillStyle = '#003c78';
  ctx.fillText('Mean Score (%)', 0, 0); ctx.restore();
  ctx.fillStyle = '#003c78'; ctx.font = 'bold 12px IBM Plex Sans,sans-serif';
  ctx.textAlign = 'center'; ctx.textBaseline = 'bottom';
  ctx.fillText('Mean Model Confidence (bin)', ml + pw / 2, H - 3);

  // Draw lines — dim first, selected on top
  const dimModels    = CALIB_MODELS.filter(m => !calibSelected.has(m));
  const brightModels = CALIB_MODELS.filter(m => calibSelected.has(m));

  function drawLine(m, bright) {
    const pts = CALIB_DATA[m];
    if (!pts || pts.length < 2) {
      if (pts && pts.length === 1) {
        const px = toX(pts[0].x), py = toY(pts[0].y);
        ctx.beginPath(); ctx.arc(px, py, bright ? 5 : 3.5, 0, Math.PI * 2);
        ctx.fillStyle = bright ? CALIB_COLORS[m] : CALIB_COLORS[m] + '44'; ctx.fill();
      }
      return;
    }
    const col = CALIB_COLORS[m], lw = bright ? 2.2 : 1, r = bright ? 5 : 3;
    ctx.strokeStyle = bright ? col : col + '2e'; ctx.lineWidth = lw;
    ctx.beginPath();
    pts.forEach((p, i) => { i === 0 ? ctx.moveTo(toX(p.x), toY(p.y)) : ctx.lineTo(toX(p.x), toY(p.y)); });
    ctx.stroke();
    pts.forEach(p => {
      const x = toX(p.x), y = toY(p.y);
      if (bright) { ctx.beginPath(); ctx.arc(x, y, r + 2, 0, Math.PI * 2); ctx.fillStyle = '#fff'; ctx.fill(); }
      ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fillStyle = bright ? col : col + '44'; ctx.fill();
      if (bright) { ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.5; ctx.stroke(); }
    });
  }

  dimModels.forEach(m => drawLine(m, false));
  brightModels.forEach(m => drawLine(m, true));

  // Hover highlight
  if (calibHoverModel && calibHoverPt) {
    const m = calibHoverModel, p = calibHoverPt;
    const x = toX(p.x), y = toY(p.y);
    ctx.beginPath(); ctx.arc(x, y, 9, 0, Math.PI * 2);
    ctx.fillStyle = CALIB_COLORS[m] + '30'; ctx.fill();
    ctx.beginPath(); ctx.arc(x, y, 6, 0, Math.PI * 2);
    ctx.fillStyle = CALIB_COLORS[m]; ctx.fill();
    ctx.strokeStyle = '#fff'; ctx.lineWidth = 2; ctx.stroke();
  }
}

function initCalib() {
  buildCalibSelector();
  drawCalib();

  const canvas = document.getElementById('calibCanvas');
  if (!canvas) return;
  const tip = document.getElementById('calibTip');

  canvas.addEventListener('mousemove', e => {
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left, my = e.clientY - rect.top;
    const W = rect.width, H = rect.height;
    const ml = 48, mr = 20, mt = 20, mb = 42;
    const pw = W - ml - mr, ph = H - mt - mb;
    const toXpx = v => ml + v * pw;
    const toYpx = v => mt + (1 - v / 100) * ph;

    let best = null, bestDist = 22;
    CALIB_MODELS.forEach(m => {
      (CALIB_DATA[m] || []).forEach(p => {
        const dist = Math.sqrt((toXpx(p.x) - mx) ** 2 + (toYpx(p.y) - my) ** 2);
        if (dist < bestDist) { bestDist = dist; best = { m, p }; }
      });
    });

    if (best) {
      calibHoverModel = best.m; calibHoverPt = best.p;
      const col = CALIB_COLORS[best.m];
      tip.style.borderTopColor = col;
      tip.innerHTML = `
        <div style="font-weight:700;font-size:12px;margin-bottom:5px;color:${col};">${best.m}</div>
        <div style="display:grid;grid-template-columns:auto auto;gap:1px 12px;">
          <span style="color:rgba(255,255,255,0.55);">Confidence</span>
          <span style="font-family:'IBM Plex Mono',monospace;font-weight:600;">${best.p.x.toFixed(2)}</span>
          <span style="color:rgba(255,255,255,0.55);">Mean Score</span>
          <span style="font-family:'IBM Plex Mono',monospace;font-weight:600;">${best.p.y.toFixed(1)}%</span>
          <span style="color:rgba(255,255,255,0.55);">Sample n</span>
          <span style="font-family:'IBM Plex Mono',monospace;font-weight:600;">${best.p.n}</span>
        </div>`;
      let tx = e.clientX + 14, ty = e.clientY - 10;
      if (tx + 200 > window.innerWidth)  tx = e.clientX - 214;
      if (ty + 100 > window.innerHeight) ty = e.clientY - 110;
      tip.style.left = tx + 'px'; tip.style.top = ty + 'px';
      tip.style.display = 'block'; canvas.style.cursor = 'crosshair';
      drawCalib();
    } else {
      if (calibHoverModel) { calibHoverModel = null; calibHoverPt = null; drawCalib(); }
      tip.style.display = 'none'; canvas.style.cursor = 'default';
    }
  });

  canvas.addEventListener('mouseleave', () => {
    if (calibHoverModel) { calibHoverModel = null; calibHoverPt = null; drawCalib(); }
    tip.style.display = 'none'; canvas.style.cursor = 'default';
  });
}

// ===== SCORE BREAKDOWN CHARTS =====

function renderBreakdown() {
  const container = document.getElementById('breakdown-charts');
  if (!container) return;
  container.innerHTML = '';

  BREAKDOWN_CATS.forEach(cat => {
    const sorted = [...lbData].sort((a, b) => b[cat.key] - a[cat.key]);
    const card   = document.createElement('div');
    card.className = 'bd-card';
    card.innerHTML = `
      <div class="bd-card-head">
        <div class="bd-card-title">${cat.label}</div>
        <div class="bd-card-sub">${cat.subtitle}</div>
      </div>
      <div class="bd-rows"></div>`;
    const barsWrap = card.querySelector('.bd-rows');

    sorted.forEach((m, i) => {
      const score       = m[cat.key];
      const color       = BREAKDOWN_COLORS[m.name] || '#003c78';
      const displayName = m.name === 'grok-4-fast-reasoning' ? 'grok-4-fast' : m.name;
      const row         = document.createElement('div');
      row.className = 'bd-row' + (i === sorted.length - 1 ? ' bd-row-last' : '');
      row.innerHTML = `
        <div class="bd-label">${displayName}</div>
        <div class="bd-bar-wrap">
          <div class="bd-bar-fill" style="width:${score}%;background:linear-gradient(90deg,${color},${color}66);--delay:${i * 0.06}s;"></div>
        </div>
        <div class="bd-val" style="color:${color};">${score.toFixed(1)}%</div>`;
      barsWrap.appendChild(row);
    });
    container.appendChild(card);
  });

  // Animate bars on scroll-in
  document.querySelectorAll('.bd-bar-fill').forEach(el => {
    const targetW = el.style.width;
    el.style.width = '0%';
    const io = new IntersectionObserver(entries => {
      entries.forEach(e => { if (e.isIntersecting) { el.style.width = targetW; io.disconnect(); } });
    }, { threshold: 0.1 });
    io.observe(el);
  });
}

// ===== INIT =====

window.addEventListener('load', () => {
  // Detect which page we are on and init only what is needed
  const file = window.location.pathname.split('/').pop() || 'index.html';

  if (file === 'index.html' || file === '') {
    // Home page: radar chart + heatmap leaderboard preview
    drawChart();
    updateLegend();
    renderLeaderboard('overall');
  }

  if (file === 'leaderboard.html') {
    renderLeaderboard('overall');
    renderMobileLeaderboard('mLbCardsLeaderboard');
    renderBreakdown();
    drawChart();
    updateLegend();
  }

  if (file === 'dashboard.html') {
    renderCostTable();
    renderTokenBars();
    renderQuestionDistribution();
    renderDatasetTables();
    drawCostScatter();
    initScatterTooltip();
    drawSpeedScatter();
    initSpeedTooltip();
    initCalib();
  }

  // Methodology and About pages have no canvas charts — nothing to init.
});

window.addEventListener('resize', () => {
  const file = window.location.pathname.split('/').pop() || 'index.html';
  if (file === 'dashboard.html') {
    drawCostScatter();
    drawSpeedScatter();
    drawCalib();
  }
  if (file === 'index.html' || file === 'leaderboard.html' || file === '') {
    drawChart();
    updateLegend();
  }
});
