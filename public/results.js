// ============================================================
//  AccountingBench — Single source of truth for ALL benchmark data
//
//  HOW TO ADD A NEW MODEL:
//  1. Copy any model block below.
//  2. Fill in all fields (see field reference below).
//  3. Insert it at the correct position (sorted by overall %, descending).
//  4. Done — ticker, leaderboard, holistic matrix, and all charts update automatically.
//
//  FIELDS per model
//  ─────────────────────────────────────────────────────────────
//  name          string   Display name shown in charts & tables
//  org           string   Provider / organisation name
//  color         string   Hex colour used across all charts
//
//  -- Category scores (%) --
//  overall       number   Overall benchmark score
//  tax           number   Tax
//  financial     number   Financial Accounting
//  management    number   Management Accounting
//
//  -- Task type scores (%) --
//  interpLaw     number   Interpretation of Law
//  calculation   number   Calculation
//  journal       number   Journal Entry (task type)
//
//  -- Answer type scores (%) --
//  multiChoice   number   Multiple Choice
//  openText      number   Open Text
//  singleChoice  number   Single Choice
//  journalEntry  number   Journal Entry (answer type)
//
//  -- Regulatory framework scores (%) --
//  austrianTax   number   Austrian Tax
//  mixedAcc      number   Mixed Accounting
//  ugb           number   National GAAP (UGB)
//  ifrs          number   IFRS
//
//  -- Efficiency --
//  n             string   Tasks completed, e.g. '520' or '465/520'
//  cost          number   Cost per task in USD
//  tokTask       number   Average tokens per task
//  speed         number   Output tokens/sec
//
//  -- Calibration --
//  calib         array    [{x, y, n}] — x=confidence midpoint, y=accuracy(%), n=count
//
//  -- Optional --
//  note          string   Short warning shown in leaderboard if tasks were excluded
// ============================================================

// Cost methodology: (input_tokens × price_in + output_tokens × price_out) / n_tasks / 1e6

const BENCHMARK_META = {
  date:                 'March 2026',
  totalTasks:           520,
  regulatoryFrameworks: 5,

  // ── Dataset composition ───────────────────────────────────
  // Edit tasks counts only — percentages are computed automatically.

  categories: [
    { label: 'Tax',                   labelShort: null,         color: '#003c78', tasks: 349 },
    { label: 'Financial Accounting',  labelShort: 'Fin. Acc.',  color: '#0d7a4e', tasks: 122 },
    { label: 'Management Accounting', labelShort: 'Mgmt. Acc.', color: '#166534', tasks: 49  },
  ],

  taskTypes: [
    { label: 'Interpretation of Law', tasks: 441 },
    { label: 'Calculation',           tasks: 54  },
    { label: 'Journal Entry',         tasks: 25, note: true },
  ],

  questionFormats: [
    { label: 'Open Text',     tasks: 300 },
    { label: 'Multi-Choice',  tasks: 155 },
    { label: 'Single-Choice', tasks: 41  },
    { label: 'Journal Entry', tasks: 16, note: true },
    { label: 'Open Numeric',  tasks: 8   },
  ],

  educationLevels: [
    { label: 'Professional Examinations', tasks: 348 },
    { label: "University Master's",       tasks: 116 },
    { label: 'Secondary Vocational',      tasks: 56  },
  ],

  regulatoryFrameworks_data: [
    { label: 'Tax (Austrian Tax Law)',      tasks: 388 },
    { label: 'Mixed Accounting Framework', tasks: 62  },
    { label: 'National GAAP',              tasks: 34  },
    { label: 'IFRS',                       tasks: 25  },
    { label: 'Mixed: Accounting + Tax',    tasks: 11  },
  ],

  journalEntryNote: 'Of the 25 journal-entry tasks, 16 use a structured journal-entry question format; the remaining 9 are presented as open-text questions — hence the lower count (16) in the Question Format table.',
};



// ── Models — keep sorted by overall score descending ─────────
const BENCHMARK_RESULTS = [

  // ── 1. gpt-5.4 ───────────────────────────────────────────────
  {
    name: 'gpt-5.4', org: 'OpenAI', color: '#0d4a2a',
    overall: 72.2, tax: 68.0, financial: 78.1, management: 88.1,
    interpLaw: 77.8, calculation: 26.4, journal: 72.4,
    multiChoice: 91.4, openText: 60.7, singleChoice: 85.4, journalEntry: 74.1,
    austrianTax: 66.7, mixedAcc: 88.2, ugb: 82.4, ifrs: 98.0,
    eduProf: 68.3, eduMaster: 90.6, eduVoc: 58.3,
    n: '520', priceIn: 2.5, priceOut: 15.0, cost: 0.023853, tokTask: 1997, speed: 83.3,
    calib: [
      {x:0.45,y:17.9,n:7},{x:0.55,y:17.7,n:25},{x:0.65,y:44.8,n:23},
      {x:0.75,y:58.2,n:86},{x:0.85,y:69.1,n:142},{x:0.95,y:90.8,n:231},
    ],
  },

  // ── 2. gpt-5.2 ───────────────────────────────────────────────
  {
    name: 'gpt-5.2', org: 'OpenAI', color: '#166534',
    overall: 68.6, tax: 62.9, financial: 77.3, management: 87.8,
    interpLaw: 73.6, calculation: 24.9, journal: 76.0,
    multiChoice: 91.1, openText: 55.2, singleChoice: 80.5, journalEntry: 76.4,
    austrianTax: 62.0, mixedAcc: 87.1, ugb: 83.1, ifrs: 98.0,
    eduProf: 63.3, eduMaster: 90.0, eduVoc: 57.2,
    n: '520', priceIn: 1.75, priceOut: 14.0, cost: 0.017876, tokTask: 1699, speed: 79.8,
    calib: [
      {x:0.15,y:21.2,n:4},{x:0.25,y:7.5,n:4},{x:0.35,y:10.9,n:16},
      {x:0.45,y:21.9,n:18},{x:0.55,y:42.8,n:35},{x:0.65,y:59.0,n:138},
      {x:0.75,y:71.4,n:162},{x:0.85,y:94.8,n:99},{x:0.95,y:100.0,n:44},
    ],
  },

  // ── 3. gpt-5.5 — 
  {
    name: 'gpt-5.5', org: 'OpenAI', color: '#14532d',
    overall: 78.8, tax: 76.3, financial: 82.8, management: 86.2,
    interpLaw: 83.7, calculation: 41.9, journal: 75.1,
    multiChoice: 93.2, openText: 71.9, singleChoice: 78.5, journalEntry: 75.3,
    austrianTax: 75.2, mixedAcc: 89.4, ugb: 81.9, ifrs: 100,
    eduProf: 75.9, eduMaster: 92.2, eduVoc: 69.0,
    n: '520', priceIn: null, priceOut: null, cost: 0, tokTask: 2128, speed: 82,
    calib: [
        {x:0.45,y:23.3,n:3},{x:0.55,y:35.0,n:14},{x:0.65,y:39.0,n:16},
        {x:0.75,y:66.7,n:107},{x:0.85,y:79.9,n:213},{x:0.95,y:95.1,n:152},

    ],
  },

  // ── 4. claude-opus-4-6 ───────────────────────────────────────
  {
    name: 'claude-opus-4-6', org: 'Anthropic', color: '#1e40af',
    overall: 63.3, tax: 57.1, financial: 74.4, management: 88.5,
    interpLaw: 67.2, calculation: 30.5, journal: 74.3,
    multiChoice: 91.3, openText: 52.7, singleChoice: 68.3, journalEntry: 77.5,
    austrianTax: 56.7, mixedAcc: 89.3, ugb: 72.1, ifrs: 100.0,
    eduProf: 57.8, eduMaster: 90.4, eduVoc: 56.5,
    n: '465/520', priceIn: 5.0, priceOut: 25.0, cost: 0.028186, tokTask: 1668, speed: 40.2,
    note: '55 tasks excluded (no final_answer). Scored on 465/520 tasks.',
    calib: [
      {x:0.25,y:22.4,n:14},{x:0.35,y:12.4,n:20},{x:0.45,y:33.0,n:11},
      {x:0.55,y:58.3,n:12},{x:0.65,y:46.3,n:28},{x:0.75,y:48.9,n:77},
      {x:0.85,y:62.0,n:177},{x:0.95,y:85.4,n:91},
    ],
  },

  // ── 5. claude-sonnet-4-6 ─────────────────────────────────────
  {
    name: 'claude-sonnet-4-6', org: 'Anthropic', color: '#3b82f6',
    overall: 63.1, tax: 54.4, financial: 77.6, management: 88.3,
    interpLaw: 67.1, calculation: 26.1, journal: 71.8,
    multiChoice: 89.6, openText: 47.4, singleChoice: 73.2, journalEntry: 76.8,
    austrianTax: 54.6, mixedAcc: 89.1, ugb: 80.5, ifrs: 99.0,
    eduProf: 54.5, eduMaster: 90.7, eduVoc: 59.2,
    n: '520', priceIn: 3.0, priceOut: 15.0, cost: 0.015551, tokTask: 1578, speed: 44.5,
    calib: [
      {x:0.25,y:9.1,n:16},{x:0.35,y:20.4,n:14},{x:0.45,y:30.9,n:23},
      {x:0.55,y:42.3,n:37},{x:0.65,y:53.2,n:63},{x:0.75,y:65.7,n:117},
      {x:0.85,y:82.5,n:123},{x:0.95,y:97.1,n:69},
    ],
  },

  // ── 6. claude-opus-4-7 — ─
  {
    name: 'claude-opus-4-7', org: 'Anthropic', color: '#1d4ed8',
    overall: 73.5, tax: 69.7, financial: 77.6, management: 91.6,
    interpLaw: 79.3, calculation: 31.3, journal: 71.5,
    multiChoice: 91.5, openText: 63.7, singleChoice: 82.1, journalEntry: 74.5,
    austrianTax: 68.4, mixedAcc: 91.8, ugb: 80.4, ifrs: 99,
    eduProf: 70.0, eduMaster: 91.2, eduVoc: 60.2,
    n: '520', priceIn: null, priceOut: null, cost: 0, tokTask: 1917, speed: 50,
    calib: [
      {x:0.35,y:15.7,n:14},{x:0.45,y:31.8,n:11},{x:0.55,y:27.3,n:28},
      {x:0.65,y:59.1,n:42},{x:0.75,y:67.5,n:116},{x:0.85,y:83.0,n:186},
      {x:0.95,y:97.8,n:97},

    ],
  },

  // ── 7. gpt-5-mini ────────────────────────────────────────────
  {
    name: 'gpt-5-mini', org: 'OpenAI', color: '#15803d',
    overall: 58.3, tax: 50.6, financial: 70.5, management: 82.7,
    interpLaw: 62.9, calculation: 19.5, journal: 61.6,
    multiChoice: 85.6, openText: 43.5, singleChoice: 65.9, journalEntry: 61.4,
    austrianTax: 50.4, mixedAcc: 80.6, ugb: 75.0, ifrs: 99.0,
    eduProf: 50.5, eduMaster: 85.7, eduVoc: 50.2,
    n: '520', priceIn: 0.25, priceOut: 2.0, cost: 0.003107, tokTask: 1975, speed: 79.3,
    calib: [
      {x:0.05,y:11.7,n:3},{x:0.15,y:11.6,n:17},{x:0.25,y:29.1,n:29},
      {x:0.35,y:31.3,n:28},{x:0.45,y:42.2,n:26},{x:0.55,y:43.5,n:41},
      {x:0.65,y:51.5,n:69},{x:0.75,y:48.8,n:74},{x:0.85,y:70.6,n:107},
      {x:0.95,y:87.6,n:121},
    ],
  },

  // ── 8. Mistral-Large-3 ───────────────────────────────────────
  {
    name: 'Mistral-Large-3', org: 'Mistral AI', color: '#c2410c',
    overall: 52.7, tax: 42.0, financial: 69.8, management: 85.5,
    interpLaw: 57.2, calculation: 20.7, journal: 42.9,
    multiChoice: 88.3, openText: 32.2, singleChoice: 70.7, journalEntry: 40.2,
    austrianTax: 42.1, mixedAcc: 86.4, ugb: 70.4, ifrs: 99.0,
    eduProf: 42.0, eduMaster: 89.2, eduVoc: 42.9,
    n: '516/520', priceIn: 0.5, priceOut: 1.5, cost: 0.001365, tokTask: 1272, speed: 48.2,
    note: '4 tasks excluded (no final_answer). Scored on 516/520 tasks.',
    calib: [
      {x:0.85,y:38.4,n:46},{x:0.95,y:54.1,n:466},
    ],
  },

  // ── 9. grok-4-fast-reasoning ─────────────────────────────────
  {
    name: 'grok-4-fast-reasoning', org: 'xAI', color: '#0f766e',
    overall: 49.1, tax: 38.8, financial: 64.3, management: 84.5,
    interpLaw: 51.9, calculation: 22.8, journal: 57.5,
    multiChoice: 84.2, openText: 28.1, singleChoice: 65.9, journalEntry: 63.9,
    austrianTax: 39.2, mixedAcc: 79.7, ugb: 62.9, ifrs: 97.3,
    eduProf: 39.1, eduMaster: 80.0, eduVoc: 47.5,
    n: '520', priceIn: 0.2, priceOut: 0.5, cost: 0.00124, tokTask: 2797, speed: 171.7,
    calib: [
      {x:0.55,y:5.0,n:4},{x:0.65,y:2.5,n:8},{x:0.75,y:8.4,n:20},
      {x:0.85,y:30.8,n:212},{x:0.95,y:68.4,n:274},
    ],
  },

  // ── 10. gpt-4o ───────────────────────────────────────────────
  {
    name: 'gpt-4o', org: 'OpenAI', color: '#16a34a',
    overall: 48.9, tax: 38.2, financial: 67.1, management: 79.8,
    interpLaw: 53.9, calculation: 13.0, journal: 38.5,
    multiChoice: 84.7, openText: 28.8, singleChoice: 65.9, journalEntry: 41.1,
    austrianTax: 37.8, mixedAcc: 80.8, ugb: 71.9, ifrs: 100.0,
    eduProf: 37.5, eduMaster: 89.3, eduVoc: 36.1,
    n: '520', priceIn: 2.5, priceOut: 10.0, cost: 0.003193, tokTask: 681, speed: 134.2,
    calib: [
      {x:0.05,y:0.0,n:4},{x:0.15,y:0.0,n:3},{x:0.25,y:8.0,n:5},
      {x:0.35,y:12.5,n:4},{x:0.45,y:8.8,n:4},{x:0.55,y:22.5,n:4},
      {x:0.85,y:59.1,n:238},{x:0.95,y:57.5,n:188},
    ],
  },

  // ── 11. DeepSeek-V3.2-2 ──────────────────────────────────────
  {
    name: 'DeepSeek-V3.2-2', org: 'DeepSeek', color: '#4338ca',
    overall: 44.8, tax: 35.8, financial: 58.9, management: 74.1,
    interpLaw: 49.5, calculation: 12.4, journal: 32.7,
    multiChoice: 80.1, openText: 25.2, singleChoice: 65.0, journalEntry: 25.3,
    austrianTax: 35.4, mixedAcc: 76.6, ugb: 53.5, ifrs: 95.7,
    eduProf: 34.9, eduMaster: 81.2, eduVoc: 31.1,
    n: '519/520', priceIn: 0.28, priceOut: 0.42, cost: 0.000304, tokTask: 904, speed: 35.7,
    note: '1 task excluded (no final_answer). Scored on 519/520 tasks.',
    calib: [
      {x:0.15,y:15.0,n:4},{x:0.25,y:4.3,n:7},{x:0.35,y:2.9,n:7},
      {x:0.45,y:0.0,n:4},{x:0.55,y:3.3,n:6},{x:0.65,y:12.7,n:12},
      {x:0.75,y:14.9,n:23},{x:0.85,y:43.2,n:380},{x:0.95,y:80.8,n:77},
    ],
  },

  // ── 12. Kimi-K2.6 — 
  {
    name: 'Kimi-K2.6', org: 'Moonshot AI', color: '#7e22ce',
    overall: 55.6, tax: 45.6, financial: 71.5, management: 85.3,
    interpLaw: 59.2, calculation: 27.1, journal: 56.9,
    multiChoice: 87.2, openText: 35.4, singleChoice: 76.9, journalEntry: 60.8,
    austrianTax: 45.6, mixedAcc: 85.2, ugb: 72.9, ifrs: 96.3,
    eduProf: 45.5, eduMaster: 87.4, eduVoc: 50.6,
    n: '520', priceIn: null, priceOut: null, cost: 0, tokTask: 13583, speed: 34,
    calib: [
      {x:0.55,y:17.0,n:5},{x:0.65,y:26,n:7},{x:0.75,y:18.4,n:19},
      {x:0.85,y:37.2,n:218},{x:0.95,y:77.5,n:250},
    ],
  },

  // ── 13. mercury-2 ────────────────────────────────────────────
  {
    name: 'mercury-2', org: 'Inception Labs', color: '#7c3aed',
    overall: 43.8, tax: 32.4, financial: 63.1, management: 77.2,
    interpLaw: 47.3, calculation: 16.7, journal: 40.1,
    multiChoice: 79.2, openText: 22.4, singleChoice: 68.3, journalEntry: 46.1,
    austrianTax: 32.6, mixedAcc: 77.9, ugb: 62.8, ifrs: 99.0,
    eduProf: 31.9, eduMaster: 82.4, eduVoc: 37.9,
    n: '520', priceIn: 0.25, priceOut: 0.75, cost: 0.000885, tokTask: 1492, speed: 1023.0,
    calib: [
      {x:0.25,y:2.0,n:5},{x:0.35,y:0.0,n:5},{x:0.45,y:13.3,n:6},
      {x:0.55,y:7.5,n:4},{x:0.65,y:5.0,n:9},{x:0.75,y:13.8,n:6},
      {x:0.85,y:31.2,n:30},{x:0.95,y:47.6,n:453},
    ],
  },

];
