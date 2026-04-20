// ============================================================
//  AccountingBench — Derived chart/table data
//
//  DO NOT edit numbers here directly.
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

// ── Leaderboard table ─────────────────────────────────────────
const lbData = BENCHMARK_RESULTS.map((m, i) => {
  const rank = i + 1;
  return {
    rank,
    cls:        _rankClass(rank),
    name:       m.name,
    org:        m.org,
    overall:    m.overall,
    financial:  m.financial,
    management: m.management,
    tax:        m.tax,
    best:       `IFRS ${m.ifrs}%`,
    n:          m.n,
    oc:         _rankColor(rank),
  };
});

// ── Cost-efficiency scatter ───────────────────────────────────
const SCATTER_MODELS = BENCHMARK_RESULTS.map(m => ({
  name:  m.name,
  color: m.color,
  score: m.overall,
  cost:  m.cost,
}));

const SCATTER_META = Object.fromEntries(
  BENCHMARK_RESULTS.map((m, i) => [
    m.name,
    { org: m.org, rank: i + 1, tokTask: m.tokTask },
  ])
);

// ── Speed vs Score scatter ────────────────────────────────────
const SPEED_MODELS_CLEAN = BENCHMARK_RESULTS.map(m => ({
  name:  m.name,
  color: m.color,
  score: m.overall,
  speed: m.speed,
}));

const SPEED_META = Object.fromEntries(
  BENCHMARK_RESULTS.map((m, i) => [
    m.name,
    { org: m.org, rank: i + 1 },
  ])
);

// ── Confidence calibration ────────────────────────────────────
const CALIB_DATA = Object.fromEntries(
  BENCHMARK_RESULTS.map(m => [m.name, m.calib])
);

const CALIB_COLORS = Object.fromEntries(
  BENCHMARK_RESULTS.map(m => [m.name, m.color])
);

// ── Breakdown colour map ──────────────────────────────────────
const BREAKDOWN_COLORS = Object.fromEntries(
  BENCHMARK_RESULTS.map(m => [m.name, m.color])
);
