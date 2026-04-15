// ============================================================
//  AccountingBench — Single source of truth for benchmark data
//
//  HOW TO UPDATE:
//  1. Add a new model object to BENCHMARK_RESULTS (or edit existing).
//  2. Keep the array sorted by overall score (descending) — rank is
//     derived automatically from array position.
//  3. All charts and tables in data.js are derived from this file.
//     Nothing else needs to change.
//
//  FIELDS per model
//  ─────────────────────────────────────────────────────────────
//  name       string   Model identifier used in charts & tables
//  org        string   Organisation / provider name
//  color      string   Hex colour used across all charts
//  overall    number   Overall benchmark score (%)
//  financial  number   Financial Accounting score (%)
//  management number   Management Accounting score (%)
//  tax        number   Tax score (%)
//  ifrs       number   IFRS score (%)
//  ugb        number   National GAAP (UGB) score (%)
//  n          string   Tasks completed, e.g. '520' or '465/520'
//  cost       number   Cost per task in USD (see methodology below)
//  tokTask    number   Average tokens per task
//  speed      number   Output tokens/sec (Artificial Analysis, March 2026)
//  calib      array    Confidence-calibration points: [{x, y, n}, ...]
//                        x = confidence midpoint, y = accuracy (%), n = count
// ============================================================

// Cost methodology: (input_tokens × price_in + output_tokens × price_out) / n_tasks / 1e6

const BENCHMARK_META = {
  date:                 'March 2026',
  totalTasks:           520,
  regulatoryFrameworks: 5,   // Financial, Management, Tax, IFRS, National GAAP
};

// ── Models — sorted by overall score descending ──────────────
const BENCHMARK_RESULTS = [
  {
    name: 'gpt-5.4', org: 'OpenAI', color: '#0d4a2a',
    overall: 72.2, financial: 78.1, management: 88.1, tax: 68.0, ifrs: 98.0,  ugb: 82.4,
    n: '520',
    cost: 0.023853, tokTask: 1997, speed: 83.3,
    calib: [
      {x:0.45,y:17.9,n:7},{x:0.55,y:17.7,n:25},{x:0.65,y:44.8,n:23},
      {x:0.75,y:58.2,n:86},{x:0.85,y:69.1,n:142},{x:0.95,y:90.8,n:231},
    ],
  },
  {
    name: 'gpt-5.2', org: 'OpenAI', color: '#166534',
    overall: 68.6, financial: 77.3, management: 87.8, tax: 62.9, ifrs: 98.0,  ugb: 83.1,
    n: '520',
    cost: 0.017876, tokTask: 1699, speed: 79.8,
    calib: [
      {x:0.15,y:21.2,n:4},{x:0.25,y:7.5,n:4},{x:0.35,y:10.9,n:16},
      {x:0.45,y:21.9,n:18},{x:0.55,y:42.8,n:35},{x:0.65,y:59.0,n:138},
      {x:0.75,y:71.4,n:162},{x:0.85,y:94.8,n:99},{x:0.95,y:100.0,n:44},
    ],
  },
  {
    name: 'claude-opus-4-6', org: 'Anthropic', color: '#1e40af',
    overall: 63.3, financial: 74.4, management: 88.5, tax: 57.1, ifrs: 100.0, ugb: 72.1,
    n: '465/520',
    cost: 0.028186, tokTask: 1668, speed: 40.2,
    calib: [
      {x:0.25,y:22.4,n:14},{x:0.35,y:12.4,n:20},{x:0.45,y:33.0,n:11},
      {x:0.55,y:58.3,n:12},{x:0.65,y:46.3,n:28},{x:0.75,y:48.9,n:77},
      {x:0.85,y:62.0,n:177},{x:0.95,y:85.4,n:91},
    ],
  },
  {
    name: 'claude-sonnet-4-6', org: 'Anthropic', color: '#3b82f6',
    overall: 63.1, financial: 77.6, management: 88.3, tax: 54.4, ifrs: 99.0,  ugb: 80.5,
    n: '520',
    cost: 0.015551, tokTask: 1578, speed: 44.5,
    calib: [
      {x:0.25,y:9.1,n:16},{x:0.35,y:20.4,n:14},{x:0.45,y:30.9,n:23},
      {x:0.55,y:42.3,n:37},{x:0.65,y:53.2,n:63},{x:0.75,y:65.7,n:117},
      {x:0.85,y:82.5,n:123},{x:0.95,y:97.1,n:69},
    ],
  },
  {
    name: 'gpt-5-mini', org: 'OpenAI', color: '#15803d',
    overall: 58.3, financial: 70.5, management: 82.7, tax: 50.6, ifrs: 99.0,  ugb: 75.0,
    n: '520',
    cost: 0.003107, tokTask: 1975, speed: 79.3,
    calib: [
      {x:0.05,y:11.7,n:3},{x:0.15,y:11.6,n:17},{x:0.25,y:29.1,n:29},
      {x:0.35,y:31.3,n:28},{x:0.45,y:42.2,n:26},{x:0.55,y:43.5,n:41},
      {x:0.65,y:51.5,n:69},{x:0.75,y:48.8,n:74},{x:0.85,y:70.6,n:107},
      {x:0.95,y:87.6,n:121},
    ],
  },
  {
    name: 'Mistral-Large-3', org: 'Mistral AI', color: '#c2410c',
    overall: 52.7, financial: 69.8, management: 85.5, tax: 42.0, ifrs: 99.0,  ugb: 70.4,
    n: '516/520',
    cost: 0.001365, tokTask: 1272, speed: 48.2,
    calib: [
      {x:0.85,y:38.4,n:46},{x:0.95,y:54.1,n:466},
    ],
  },
  {
    name: 'grok-4-fast-reasoning', org: 'xAI', color: '#0f766e',
    overall: 49.1, financial: 64.3, management: 84.5, tax: 38.8, ifrs: 97.3,  ugb: 62.9,
    n: '520',
    cost: 0.00124,  tokTask: 2797, speed: 171.7,
    calib: [
      {x:0.55,y:5.0,n:4},{x:0.65,y:2.5,n:8},{x:0.75,y:8.4,n:20},
      {x:0.85,y:30.8,n:212},{x:0.95,y:68.4,n:274},
    ],
  },
  {
    name: 'gpt-4o', org: 'OpenAI', color: '#16a34a',
    overall: 48.9, financial: 67.1, management: 79.8, tax: 38.2, ifrs: 100.0, ugb: 71.9,
    n: '520',
    cost: 0.003193, tokTask: 681,  speed: 134.2,
    calib: [
      {x:0.05,y:0.0,n:4},{x:0.15,y:0.0,n:3},{x:0.25,y:8.0,n:5},
      {x:0.35,y:12.5,n:4},{x:0.45,y:8.8,n:4},{x:0.55,y:22.5,n:4},
      {x:0.85,y:59.1,n:238},{x:0.95,y:57.5,n:188},
    ],
  },
  {
    name: 'DeepSeek-V3.2-2', org: 'DeepSeek', color: '#4338ca',
    overall: 44.8, financial: 58.9, management: 74.1, tax: 35.8, ifrs: 95.7,  ugb: 53.5,
    n: '519/520',
    cost: 0.000304, tokTask: 904,  speed: 35.7,
    calib: [
      {x:0.15,y:15.0,n:4},{x:0.25,y:4.3,n:7},{x:0.35,y:2.9,n:7},
      {x:0.45,y:0.0,n:4},{x:0.55,y:3.3,n:6},{x:0.65,y:12.7,n:12},
      {x:0.75,y:14.9,n:23},{x:0.85,y:43.2,n:380},{x:0.95,y:80.8,n:77},
    ],
  },
  {
    name: 'mercury-2', org: 'Inception Labs', color: '#7c3aed',
    overall: 43.8, financial: 63.1, management: 77.2, tax: 32.4, ifrs: 99.0,  ugb: 62.8,
    n: '520',
    cost: 0.000885, tokTask: 1492, speed: 1023.0,
    calib: [
      {x:0.25,y:2.0,n:5},{x:0.35,y:0.0,n:5},{x:0.45,y:13.3,n:6},
      {x:0.55,y:7.5,n:4},{x:0.65,y:5.0,n:9},{x:0.75,y:13.8,n:6},
      {x:0.85,y:31.2,n:30},{x:0.95,y:47.6,n:453},
    ],
  },
];
