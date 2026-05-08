// ============================================================
//  AccountingBench — Derived chart/table data + DOM renderers
//
//  DO NOT edit numbers here.
//  All values are derived from BENCHMARK_RESULTS in results.js.
//  To add or update a model, edit results.js only.
//
//  Load order in HTML: results.js → data.js → main.js
// ============================================================

// ── Radar / bar chart axes ────────────────────────────────────
const AXES      = ['Overall', 'Financial', 'Management', 'Tax', 'IFRS', 'National GAAP'];
const AXIS_KEYS = ['overall', 'financial', 'management', 'tax', 'ifrs', 'ugb'];

// ── Score breakdown categories ────────────────────────────────
const BREAKDOWN_CATS = [
  { key:'financial',  label:'Financial Accounting', subtitle:'122 questions' },
  { key:'management', label:'Management Accounting', subtitle:'49 questions'  },
  { key:'tax',        label:'Tax',                   subtitle:'349 questions' },
];

// ── Holistic matrix column definitions ───────────────────────
// To add/remove columns from the matrix table, edit here only.
const HM_COLS = [
  { key:'overall',      label:'Overall'           },
  { key:'tax',          label:'Tax'               },
  { key:'financial',    label:'Fin. Acc.'          },
  { key:'management',   label:'Mgmt. Acc.'         },
  { key:'interpLaw',    label:'Interp. of Law'     },
  { key:'calculation',  label:'Calculation'        },
  { key:'journal',      label:'Journal Entry'      },
  { key:'multiChoice',  label:'Multi Choice'       },
  { key:'openText',     label:'Open Text'          },
  { key:'singleChoice', label:'Single Choice'      },
  { key:'journalEntry', label:'Journal Entry (AT)' },
  { key:'austrianTax',  label:'Austrian Tax'       },
  { key:'mixedAcc',     label:'Mixed Acc.'         },
  { key:'ugb',          label:'National GAAP'      },
  { key:'ifrs',         label:'IFRS'               },
];

// ── Helpers ───────────────────────────────────────────────────
function _rankClass(rank) {
  if (rank === 1) return 'rank-1';
  if (rank === 2) return 'rank-2';
  if (rank === 3) return 'rank-3';
  return '';
}
function _rankColor(rank) {
  if (rank === 1) return 'var(--gold)';
  if (rank === 2) return 'var(--silver)';
  if (rank === 3) return 'var(--bronze)';
  return 'var(--text-muted)';
}
function _scorePillClass(v) {
  if (v >= 90) return 's-90plus';
  if (v >= 75) return 's-75plus';
  if (v >= 60) return 's-60plus';
  if (v >= 50) return 's-50plus';
  return 's-below50';
}
function _nColor(n) {
  return n.includes('/') ? 'var(--amber)' : 'var(--text-dim)';
}

// ── MODELS (radar + bar charts) ───────────────────────────────
const MODELS = BENCHMARK_RESULTS.map(m => ({
  name:       m.name,
  org:        m.org,
  color:      m.color,
  overall:    m.overall,
  financial:  m.financial,
  management: m.management,
  tax:        m.tax,
  ifrs:       m.ifrs,
  ugb:        m.ugb,
}));

// ── Leaderboard table data ────────────────────────────────────
const lbData = BENCHMARK_RESULTS.map((m, i) => {
  const rank = i + 1;
  return {
    rank, cls: _rankClass(rank),
    name: m.name, org: m.org,
    overall: m.overall, financial: m.financial,
    management: m.management, tax: m.tax,
    best: `IFRS ${m.ifrs}%`,
    n: m.n, oc: _rankColor(rank),
  };
});

// ── Cost-efficiency scatter ───────────────────────────────────
const SCATTER_MODELS = BENCHMARK_RESULTS.map(m => ({
  name: m.name, color: m.color, score: m.overall, cost: m.cost,
}));
const SCATTER_META = Object.fromEntries(
  BENCHMARK_RESULTS.map((m, i) => [m.name, { org: m.org, rank: i + 1, tokTask: m.tokTask }])
);

// ── Speed vs Score scatter ────────────────────────────────────
const SPEED_MODELS_CLEAN = BENCHMARK_RESULTS.map(m => ({
  name: m.name, color: m.color, score: m.overall, speed: m.speed,
}));
const SPEED_META = Object.fromEntries(
  BENCHMARK_RESULTS.map((m, i) => [m.name, { org: m.org, rank: i + 1 }])
);

// ── Confidence calibration ────────────────────────────────────
const CALIB_DATA   = Object.fromEntries(BENCHMARK_RESULTS.map(m => [m.name, m.calib]));
const CALIB_COLORS = Object.fromEntries(BENCHMARK_RESULTS.map(m => [m.name, m.color]));

// ── Breakdown colour map ──────────────────────────────────────
const BREAKDOWN_COLORS = Object.fromEntries(BENCHMARK_RESULTS.map(m => [m.name, m.color]));

// ============================================================
//  DOM RENDER FUNCTIONS
//  Called once on page load (at bottom of main.js init block).
//  Each function finds its container by ID and injects HTML.
// ============================================================

// ── Ticker bar ───────────────────────────────────────────────
function renderTicker() {
  const inner = document.getElementById('ticker-inner');
  if (!inner) return;
  // Build items once, then duplicate for seamless CSS loop
  const sorted = [...BENCHMARK_RESULTS].sort((a, b) => b.overall - a.overall);
  const items = sorted.map(m =>
    `<div class="ticker-item"><span class="ticker-dot" style="background:${m.color};"></span>` +
    `<span class="ticker-model">${m.name}</span> ` +
    `<span class="ticker-score">${m.overall}%</span> ` +
    `<span class="ticker-cat">Overall</span></div>`
  ).join('');
  inner.innerHTML = items + items; // duplicate for infinite scroll
}

// ── Overview mini-leaderboard (desktop table) ─────────────────
function renderOverviewLeaderboard() {
  const el = document.getElementById('overview-leaderboard');
  if (!el) return;
  const sorted = [...BENCHMARK_RESULTS].sort((a, b) => b.overall - a.overall);
  const rows = sorted.map((m, i) => {
    const rank = i + 1;
    const rc   = _rankColor(rank);
    const cls  = _rankClass(rank);
    const winner = rank === 1 ? ' <span class="winner-chip">🏆 #1</span>' : '';
    return `<div class="leaderboard-row ${cls}">` +
      `<div class="rank-badge" style="color:${rc};">${rank}</div>` +
      `<div class="model-info"><div class="model-name">${m.name}${winner}</div><div class="model-org">${m.org}</div></div>` +
      `<div class="score-cell"><div class="score-main" style="color:${rc};">${m.overall}%</div>` +
      `<div class="score-bar-wrapper"><div class="score-bar-fill" style="width:${m.overall}%;background:${m.color};"></div></div></div>` +
      `<div class="score-cat">${m.financial}%</div>` +
      `<div class="score-cat">${m.management}%</div>` +
      `<div class="score-cat">${m.tax}%</div>` +
      `<div class="score-cat" style="color:${_nColor(m.n)};">${m.n}</div>` +
      `</div>`;
  }).join('');

  const notes = BENCHMARK_RESULTS
    .filter(m => m.note)
    .map(m => m.name + ': ' + m.note)
    .join('; ');
  const noteHtml = notes
    ? `<div style="padding:11px 20px;border-top:1px solid var(--border);font-size:11px;color:var(--text-muted);line-height:1.7;background:var(--wu-light);">Note: ${notes} Excluded tasks are transparently reported.</div>`
    : '';

  el.innerHTML = rows + noteHtml;
}

// ── Overview mobile leaderboard cards ────────────────────────
function renderMobileLeaderboard() {
  const el = document.getElementById('mobile-leaderboard');
  if (!el) return;
  const sorted = [...BENCHMARK_RESULTS].sort((a, b) => b.overall - a.overall);
  el.innerHTML = sorted.map((m, i) => {
    const rank = i + 1;
    const rc   = _rankColor(rank);
    const rankCls = rank === 1 ? 'gold' : rank === 2 ? 'silver' : rank === 3 ? 'bronze' : '';
    const winner = rank === 1 ? ` <span style="font-size:10px;background:rgba(180,83,9,0.12);color:var(--gold);padding:1px 6px;font-weight:700;">🏆 #1</span>` : '';
    const noteHtml = m.note ? `<div class="m-lb-note">⚠️ ${m.note}</div>` : '';
    return `<div class="m-lb-card">` +
      `<div class="m-lb-card-summary">` +
      `<div class="m-lb-rank ${rankCls}">${rank}</div>` +
      `<div class="m-lb-info"><div class="m-lb-name">${m.name}${winner}</div><div class="m-lb-org">${m.org}</div></div>` +
      `<div class="m-lb-score-wrap"><div class="m-lb-score" style="color:${rc};">${m.overall}%</div>` +
      `<div class="m-lb-score-bar"><div class="m-lb-score-bar-fill" style="width:${m.overall}%;background:${m.color};"></div></div></div>` +
      `<svg class="m-lb-chevron" fill="none" stroke="currentColor" stroke-linecap="round" stroke-width="2.5" viewBox="0 0 24 24"><polyline points="6 9 12 15 18 9"></polyline></svg>` +
      `</div>` +
      `<div class="m-lb-detail"><div class="m-lb-detail-grid">` +
      `<div class="m-lb-detail-item"><div class="m-lb-detail-label">Fin. Acc.</div><div class="m-lb-detail-val">${m.financial}%</div></div>` +
      `<div class="m-lb-detail-item"><div class="m-lb-detail-label">Mgmt. Acc.</div><div class="m-lb-detail-val">${m.management}%</div></div>` +
      `<div class="m-lb-detail-item"><div class="m-lb-detail-label">Tax</div><div class="m-lb-detail-val">${m.tax}%</div></div>` +
      `<div class="m-lb-detail-item"><div class="m-lb-detail-label">IFRS</div><div class="m-lb-detail-val">${m.ifrs}%</div></div>` +
      `<div class="m-lb-detail-item"><div class="m-lb-detail-label">National GAAP</div><div class="m-lb-detail-val">${m.ugb}%</div></div>` +
      `<div class="m-lb-detail-item"><div class="m-lb-detail-label">Tasks</div><div class="m-lb-detail-val">${m.n}</div></div>` +
      `</div>${noteHtml}</div></div>`;
  }).join('');
}

// ── Holistic matrix table (overview page) ────────────────────
function renderHolisticMatrix(eduKey) {
  const tbody  = document.getElementById('hm-tbody');
  const thead  = document.getElementById('hm-thead');
  if (!tbody) return;

  eduKey = eduKey || 'all';

  // ── 2-row grouped header ──────────────────────────────────
  if (thead) {
    thead.innerHTML =
      `<tr style="border-bottom:none;">
        <th rowspan="2" style="width:140px;vertical-align:bottom;">Model</th>
        <th style="text-align:center;">Overall</th>
        <th colspan="3" style="text-align:center;background:#1a4f8a;">Category</th>
        <th colspan="3" style="text-align:center;background:#1a4f8a;">Task Type</th>
        <th colspan="4" style="text-align:center;background:#1a4f8a;">Answer Type</th>
        <th colspan="4" style="text-align:center;background:#1a4f8a;">Reg. Framework</th>
        <th colspan="3" style="text-align:center;background:#1a4f8a;">Education</th>
      </tr>
      <tr>
        <th style="font-size:9px;"></th>
        <th style="background:#1a4f8a;font-size:9px;font-weight:400;">Tax</th>
        <th style="background:#1a4f8a;font-size:9px;font-weight:400;">Fin. Acc.</th>
        <th style="background:#1a4f8a;font-size:9px;font-weight:400;">Mgmt. Acc.</th>
        <th style="background:#1a4f8a;font-size:9px;font-weight:400;">Interp. of Law</th>
        <th style="background:#1a4f8a;font-size:9px;font-weight:400;position:relative;cursor:help;" class="hm-calc-tip">Calculation
          <div class="hm-calc-popup">The low calculation score is driven by task composition: 45 of 54 calculation items are open_text, which models struggle with. Performance is strong on multi_choice (~95%) and moderate on open_numeric (~59%).</div>
        </th>
        <th style="background:#1a4f8a;font-size:9px;font-weight:400;">Journal Entry</th>
        <th style="background:#1a4f8a;font-size:9px;font-weight:400;">Multi Choice</th>
        <th style="background:#1a4f8a;font-size:9px;font-weight:400;">Open Text</th>
        <th style="background:#1a4f8a;font-size:9px;font-weight:400;">Single Choice</th>
        <th style="background:#1a4f8a;font-size:9px;font-weight:400;">Journal Entry</th>
        <th style="background:#1a4f8a;font-size:9px;font-weight:400;">Austrian Tax</th>
        <th style="background:#1a4f8a;font-size:9px;font-weight:400;">Mixed Acc.</th>
        <th style="background:#1a4f8a;font-size:9px;font-weight:400;">National GAAP</th>
        <th style="background:#1a4f8a;font-size:9px;font-weight:400;position:relative;cursor:help;" class="hm-calc-tip">IFRS
          <div class="hm-calc-popup">The IFRS subset of the dataset is comparatively small (n = 25 tasks) and was drawn primarily from university-level teaching material. The near-ceiling performance reported should therefore not be read as evidence that LLMs handle IFRS reasoning reliably in general; the result is consistent with the high standardization and broad international documentation of IFRS, but the present item pool does not capture the full complexity of IFRS application in practice and has limited discriminative power for cross-model comparison. Expanding the IFRS subset with practice-grade items is a priority for the next iteration.</div>
        </th>
        <th style="background:#1a4f8a;font-size:9px;font-weight:400;">Prof. Exams</th>
        <th style="background:#1a4f8a;font-size:9px;font-weight:400;">University Exams</th>
        <th style="background:#1a4f8a;font-size:9px;font-weight:400;">Sec. Voc. School</th>
      </tr>`;
  }

  // ── Column order ─────────────────────────────────────────
  const COL_KEYS = [
    'overall',
    'tax', 'financial', 'management',
    'interpLaw', 'calculation', 'journal',
    'multiChoice', 'openText', 'singleChoice', 'journalEntry',
    'austrianTax', 'mixedAcc', 'ugb', 'ifrs',
    'eduProf', 'eduMaster', 'eduVoc',
  ];

  // ── Rows ──────────────────────────────────────────────────
  const sorted = [...BENCHMARK_RESULTS].sort((a, b) => b.overall - a.overall);
  tbody.innerHTML = sorted.map(m => {
    // Get source data — byEdu subset or full model
    const src = (eduKey !== 'all' && m.byEdu && m.byEdu[eduKey]) ? m.byEdu[eduKey] : null;

    const cells = COL_KEYS.map(k => {
      let v;
      if (eduKey === 'all') {
        // Use top-level fields
        v = m[k];
      } else {
        // For edu columns always use top-level
        if (k === 'eduProf')   v = m.eduProf;
        else if (k === 'eduMaster') v = m.eduMaster;
        else if (k === 'eduVoc')    v = m.eduVoc;
        else v = src ? src[k] : null;
      }

      if (v === null || v === undefined) {
        return `<td class="hm-cell"><span class="score-pill hm-null">—</span></td>`;
      }
      return `<td class="hm-cell"><span class="score-pill ${_scorePillClass(v)}">${v}%</span></td>`;
    }).join('');
    return `<tr><td class="hm-model">${m.name}</td>${cells}</tr>`;
  }).join('');

  // ── Caption ───────────────────────────────────────────────
  const caption = document.getElementById('hm-caption');
  if (caption) {
    const label = eduKey === 'all' ? 'All tasks' :
                  eduKey === 'prof' ? 'Professional Exams only' :
                  eduKey === 'master' ? "University Exams only" :
                  'Secondary Vocational only';
    const nullNote = eduKey !== 'all' ? ' · — indicates no tasks in this combination' : '';
    caption.textContent = `Holistic results matrix · ${BENCHMARK_META.totalTasks} tasks · ${BENCHMARK_RESULTS.length} models · ${BENCHMARK_META.date} · ${label}${nullNote}`;
  }
}

// ── API Cost table (dashboard) ────────────────────────────────
function renderCostTable() {
  const tbody = document.getElementById('cost-table-tbody');
  if (!tbody) return;
  // Sort by cost descending (most expensive first)
  const sorted = [...BENCHMARK_RESULTS].filter(m => m.cost > 0).sort((a, b) => b.cost - a.cost);
  const maxCost = sorted[0]?.cost || 1;
  tbody.innerHTML = sorted.map(m => {
    const costColor = m.cost > 0.01 ? 'var(--red)' : m.cost > 0.003 ? 'var(--amber)' : 'var(--green)';
    const costFmt = m.cost < 0.001 ? '$' + m.cost.toFixed(5) : '$' + m.cost.toFixed(4);
    const priceIn  = m.priceIn  != null ? '$' + m.priceIn.toFixed(2)  : '—';
    const priceOut = m.priceOut != null ? '$' + m.priceOut.toFixed(2) : '—';
    return `<tr>
      <td style="font-weight:600;font-size:13px;">${m.name}</td>
      <td style="font-family:'IBM Plex Mono',monospace;text-align:right;font-size:12px;">${priceIn}</td>
      <td style="font-family:'IBM Plex Mono',monospace;text-align:right;font-size:12px;">${priceOut}</td>
      <td style="font-family:'IBM Plex Mono',monospace;text-align:right;font-size:12px;font-weight:700;color:${costColor};">${costFmt}</td>
    </tr>`;
  }).join('');
}

// ── Token usage bars (dashboard) ─────────────────────────────
function renderTokenBars() {
  const el = document.getElementById('token-bars');
  if (!el) return;
  const sorted = [...BENCHMARK_RESULTS].filter(m => m.tokTask > 0).sort((a, b) => b.tokTask - a.tokTask);
  const maxTok = sorted[0]?.tokTask || 1;
  el.innerHTML = sorted.map((m, i) => {
    const pct = ((m.tokTask / maxTok) * 100).toFixed(1);
    const hex  = m.color;
    const hexA = hex + '80'; // 50% alpha approximation
    return `<div style="display:flex;align-items:center;gap:12px;">
      <div style="width:clamp(80px,28%,160px);flex-shrink:0;font-family:'IBM Plex Mono',monospace;font-size:11px;color:var(--text-muted);text-align:right;">${m.name}</div>
      <div style="flex:1;height:26px;background:var(--surface2);border-radius:2px;overflow:hidden;position:relative;">
        <div class="tok-bar-fill" style="width:${pct}%;height:100%;background:linear-gradient(90deg,${hex},${hexA})"></div>
      </div>
      <div style="width:44px;flex-shrink:0;font-family:'IBM Plex Mono',monospace;font-size:12px;font-weight:700;color:${hex};text-align:right;">${m.tokTask.toLocaleString()}</div>
    </div>`;
  }).join('');
}

// ── Question Distribution donut + legend (dashboard) ─────────
function renderQuestionDistribution() {
  const donut  = document.getElementById('distDonut');
  const legend = document.getElementById('dist-legend');
  const center = document.getElementById('dist-center');
  if (!donut || !legend) return;

  const cats  = BENCHMARK_META.categories;
  const total = cats.reduce((s, c) => s + c.tasks, 0);
  const CIRC  = 352; // circumference of r=56 circle (2π×56 ≈ 352)
  const GAP   = 2;   // gap between segments

  // Update center label
  if (center) center.textContent = total;

  // Build donut segments
  let offset = 0;
  donut.querySelectorAll('.donut-seg').forEach(el => el.remove()); // clear old
  cats.forEach((c, i) => {
    const pct  = c.tasks / total;
    const arc  = Math.round(pct * CIRC) - GAP;
    const rest = CIRC - arc;
    const seg  = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    seg.setAttribute('class', 'donut-seg');
    seg.setAttribute('cx', '80');
    seg.setAttribute('cy', '80');
    seg.setAttribute('r', '56');
    seg.setAttribute('fill', 'none');
    seg.setAttribute('stroke', c.color);
    seg.setAttribute('stroke-width', '28');
    seg.setAttribute('stroke-dasharray', `${arc} ${rest + GAP}`);
    seg.setAttribute('stroke-dashoffset', String(-offset));
    seg.setAttribute('data-full', arc);
    seg.setAttribute('data-offset', -offset);
    seg.style.transition = `stroke-dasharray 1.1s cubic-bezier(0.4,0,0.2,1) ${i * 0.15}s`;
    donut.insertBefore(seg, donut.lastElementChild); // insert before gap ring
    offset += arc + GAP;
  });

  // Build legend
  legend.innerHTML = cats.map(c => {
    const pct = ((c.tasks / total) * 100).toFixed(1);
    const nameHtml = c.labelShort
      ? `<span class="dist-name-full">${c.label}</span><span class="dist-name-abbr">${c.labelShort}</span>`
      : c.label;
    return `<div class="dist-legend-item" style="--c:${c.color};">
      <div class="dist-legend-bar" data-final-width="${pct}%" style="background:${c.color};width:${pct}%;"></div>
      <div class="dist-legend-row">
        <div class="dist-legend-dot" style="background:${c.color};"></div>
        <span class="dist-legend-name">${nameHtml}</span>
        <span class="dist-legend-count">${c.tasks}</span>
      </div>
      <div class="dist-legend-pct" style="color:${c.color};">${pct}%</div>
    </div>`;
  }).join('');
}

// ── Dataset Composition tables (dashboard) ───────────────────
function renderDatasetTables() {
  const NOTE_MARKER = `<sup style="color:var(--wu-blue);font-weight:700;">*</sup>`;

  function buildRows(items, total) {
    return items.map(r => {
      const pct = ((r.tasks / total) * 100).toFixed(1) + '%';
      const lbl = r.note ? `${r.label} ${NOTE_MARKER}` : r.label;
      return `<tr><td>${lbl}</td><td>${r.tasks}</td><td>${pct}</td></tr>`;
    }).join('');
  }

  const T = BENCHMARK_META.totalTasks;

  // Category table
  const catTbody = document.getElementById('ds-category-tbody');
  if (catTbody) catTbody.innerHTML = buildRows(BENCHMARK_META.categories, T);

  // Task type table
  const ttTbody = document.getElementById('ds-tasktype-tbody');
  if (ttTbody) ttTbody.innerHTML = buildRows(BENCHMARK_META.taskTypes, T);

  // Journal entry note
  const noteEl = document.getElementById('ds-journal-note');
  if (noteEl) noteEl.textContent = BENCHMARK_META.journalEntryNote;

  // Question format table
  const qfTbody = document.getElementById('ds-questionformat-tbody');
  if (qfTbody) qfTbody.innerHTML = buildRows(BENCHMARK_META.questionFormats, T);

  // Education level table
  const eduTbody = document.getElementById('ds-education-tbody');
  if (eduTbody) eduTbody.innerHTML = buildRows(BENCHMARK_META.educationLevels, T);

  // Regulatory framework table
  const regTbody = document.getElementById('ds-regulatory-tbody');
  if (regTbody) regTbody.innerHTML = buildRows(BENCHMARK_META.regulatoryFrameworks_data, T);

  // Dataset description text
  const descEl = document.getElementById('ds-description');
  if (descEl) descEl.textContent = `The dataset contains ${T} tasks curated from professional examination materials and university coursework. Each task is tagged by category, regulatory framework, education level, and answer type.`;
}
