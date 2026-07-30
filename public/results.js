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
//  -- Education level breakdowns --
//  byEdu         object   Full score breakdown by education level.
//                         Keys: prof, master, voc
//                         Each contains all score fields (overall, tax, financial, etc.)
//                         null = no tasks exist for that education/category combination
//                         Key insight: IFRS is null for prof and voc — all 25 IFRS tasks
//                         are Master-level only, explaining the near-ceiling IFRS scores.
//
//  -- Optional --
//  note          string   Short warning shown in leaderboard if tasks were excluded
// ============================================================

// Cost methodology: (input_tokens × price_in + output_tokens × price_out) / n_tasks / 1e6

const BENCHMARK_META = {
  date:                 'May 2026',
  totalTasks:           564,
  regulatoryFrameworks: 5,

  // ── Dataset composition ───────────────────────────────────
  // Edit tasks counts only — percentages are computed automatically.

  categories: [
    { label: 'Tax',                   labelShort: null,         color: '#003c78', tasks: 349 },
    { label: 'Financial Accounting',  labelShort: 'Fin. Acc.',  color: '#0d7a4e', tasks: 166 },
    { label: 'Management Accounting', labelShort: 'Mgmt. Acc.', color: '#166534', tasks: 49  },
  ],

  taskTypes: [
    { label: 'Interpretation of Law', tasks: 462 },
    { label: 'Calculation',           tasks: 70  },
    { label: 'Journal Entry',         tasks: 32, note: true },
  ],

  questionFormats: [
    { label: 'Open Text',     tasks: 333 },
    { label: 'Multi-Choice',  tasks: 164 },
    { label: 'Single-Choice', tasks: 44  },
    { label: 'Journal Entry', tasks: 15, note: true },
    { label: 'Open Numeric',  tasks: 8   },
  ],

  educationLevels: [
    { label: 'Professional Examinations', tasks: 392 },
    { label: 'University Exams',       tasks: 116 },
    { label: 'Secondary Vocational',      tasks: 56  },
  ],

  regulatoryFrameworks_data: [
    { label: 'Tax (Austrian Tax Law)',      tasks: 388 },
    { label: 'Mixed Accounting Framework', tasks: 62  },
    { label: 'National GAAP',              tasks: 34  },
    { label: 'IFRS',                       tasks: 69  },
    { label: 'Mixed: Accounting + Tax',    tasks: 11  },
  ],

  journalEntryNote: 'Of the 32 journal-entry tasks, 15 use a structured journal-entry question format; the remaining 17 are presented as open-text questions - hence the lower count (15) in the Question Format table.',
};



// ── Models — keep sorted by overall score descending ─────────
const BENCHMARK_RESULTS = [

  // ── 1. gpt-5.5 ───────────────────────────────────
  {
    name: 'gpt-5.5', org: 'OpenAI', color: '#14532d',
    overall: 79.2, tax: 76.3, financial: 82.8, management: 86.6,
    interpLaw: 83.3, calculation: 50.7, journal: 79.5,
    multiChoice: 91.4, openText: 73.2, singleChoice: 80.6, journalEntry: 79.6,
    austrianTax: 75.3, mixedAcc: 89.4, ugb: 82.0, ifrs: 89.1,
    eduProf: 76.7, eduMaster: 92.2, eduVoc: 69.0,
    byEdu: {
      prof:   { overall: 76.7, tax: 76.1, financial: 82.8, management: 71.0, interpLaw: 80.8, calculation: 44.0, journal: 95.0, multiChoice: 90.4, openText: 73.6, singleChoice: 84.6, journalEntry: 91.2, austrianTax: 76.1, mixedAcc: 71.0, ugb: null, ifrs: 82.8 },
      master: { overall: 92.2, tax: 84.7, financial: 93.2, management: 92.9, interpLaw: 92.2, calculation: null, journal: null, multiChoice: 91.9, openText: 50.0, singleChoice: 100.0, journalEntry: null, austrianTax: 83.3, mixedAcc: 94.8, ugb: 86.1, ifrs: 100.0 },
      voc:    { overall: 69.0, tax: 65.0, financial: 69.3, management: null, interpLaw: 60.0, calculation: 66.0, journal: 75.1, multiChoice: 100.0, openText: 70.5, singleChoice: 50.0, journalEntry: 75.3, austrianTax: 67.1, mixedAcc: null, ugb: 75.3, ifrs: null },
    },
    n: '550/564', priceIn: 5.0, priceOut: 30.0, cost: 0.035077, tokTask: 1573, speed: 57,
    note: '14 tasks not completed for this model. Scored on 550/564 tasks.',
    calib: [{x:0.25,y:75.0,n:1}, {x:0.35,y:0.0,n:1}, {x:0.45,y:23.3,n:3}, {x:0.55,y:35.0,n:14}, {x:0.65,y:39.9,n:16}, {x:0.75,y:65.7,n:111}, {x:0.85,y:80.7,n:236}, {x:0.95,y:94.9,n:168}],
  },

  // ── 2. claude-opus-4-7 ───────────────────────────────────
  {
    name: 'claude-opus-4-7', org: 'Anthropic', color: '#1d4ed8',
    overall: 74.4, tax: 69.8, financial: 78.2, management: 91.6,
    interpLaw: 79.3, calculation: 41.9, journal: 73.4,
    multiChoice: 90.2, openText: 65.3, singleChoice: 84.4, journalEntry: 74.0,
    austrianTax: 68.5, mixedAcc: 91.8, ugb: 81.9, ifrs: 86.0,
    eduProf: 71.1, eduMaster: 91.6, eduVoc: 60.2,
    byEdu: {
      prof:   { overall: 71.1, tax: 69.6, financial: 78.7, management: 80.2, interpLaw: 74.7, calculation: 43.4, journal: 80.0, multiChoice: 87.8, openText: 66.9, singleChoice: 85.7, journalEntry: 72.5, austrianTax: 69.6, mixedAcc: 80.2, ugb: null, ifrs: 78.7 },
      master: { overall: 91.6, tax: 82.6, financial: 90.8, management: 96.2, interpLaw: 91.6, calculation: null, journal: null, multiChoice: 91.7, openText: 100.0, singleChoice: 90.0, journalEntry: null, austrianTax: 81.1, mixedAcc: 95.1, ugb: 88.5, ifrs: 99.0 },
      voc:    { overall: 60.2, tax: 38.3, financial: 61.4, management: null, interpLaw: 77.5, calculation: 38.4, journal: 71.5, multiChoice: 75.0, openText: 52.1, singleChoice: 75.0, journalEntry: 74.5, austrianTax: 56.9, mixedAcc: null, ugb: 71.2, ifrs: null },
    },
    n: '540/564', priceIn: 5, priceOut: 25, cost: 0.02997, tokTask: 1919, speed: 37,
    note: '24 tasks not completed for this model. Scored on 540/564 tasks.',
    calib: [{x:0.25,y:0.0,n:2}, {x:0.35,y:15.7,n:14}, {x:0.45,y:31.8,n:11}, {x:0.55,y:26.7,n:29}, {x:0.65,y:58.1,n:44}, {x:0.75,y:68.5,n:129}, {x:0.85,y:83.8,n:212}, {x:0.95,y:97.6,n:99}],
  },

  // ── 3. gpt-5.4 ───────────────────────────────────
  {
    name: 'gpt-5.4', org: 'OpenAI', color: '#0d4a2a',
    overall: 72.7, tax: 68.0, financial: 78.0, management: 88.1,
    interpLaw: 77.9, calculation: 36.2, journal: 73.3,
    multiChoice: 90.3, openText: 62.3, singleChoice: 86.4, journalEntry: 71.3,
    austrianTax: 66.7, mixedAcc: 88.2, ugb: 82.4, ifrs: 85.1,
    eduProf: 69.4, eduMaster: 90.6, eduVoc: 58.3,
    byEdu: {
      prof:   { overall: 69.4, tax: 68.0, financial: 77.8, management: 76.3, interpLaw: 73.4, calculation: 38.2, journal: 76.4, multiChoice: 89.7, openText: 63.8, singleChoice: 88.5, journalEntry: 63.8, austrianTax: 68.0, mixedAcc: 76.3, ugb: null, ifrs: 77.8 },
      master: { overall: 90.6, tax: 77.8, financial: 91.7, management: 92.9, interpLaw: 90.6, calculation: null, journal: null, multiChoice: 90.6, openText: 100.0, singleChoice: 90.0, journalEntry: null, austrianTax: 75.8, mixedAcc: 91.7, ugb: 88.3, ifrs: 98.0 },
      voc:    { overall: 58.3, tax: 23.3, financial: 60.3, management: null, interpLaw: 79.5, calculation: 31.5, journal: 72.4, multiChoice: 100.0, openText: 48.7, singleChoice: 75.0, journalEntry: 74.1, austrianTax: 54.0, mixedAcc: null, ugb: 72.7, ifrs: null },
    },
    n: '564', priceIn: 2.5, priceOut: 15.0, cost: 0.023853, tokTask: 1997, speed: 83.3,
    calib: [
      {x:0.45,y:17.9,n:7},{x:0.55,y:17.7,n:25},{x:0.65,y:44.8,n:23},
      {x:0.75,y:58.2,n:86},{x:0.85,y:69.1,n:142},{x:0.95,y:90.8,n:231},
    ],
  },

  // ── 4. gpt-5.2 ───────────────────────────────────
  {
    name: 'gpt-5.2', org: 'OpenAI', color: '#166534',
    overall: 69.6, tax: 62.9, financial: 78.3, management: 87.8,
    interpLaw: 73.8, calculation: 36.6, journal: 76.7,
    multiChoice: 90.1, openText: 57.6, singleChoice: 81.8, journalEntry: 74.7,
    austrianTax: 62.0, mixedAcc: 87.1, ugb: 83.1, ifrs: 87.3,
    eduProf: 65.3, eduMaster: 90.0, eduVoc: 57.2,
    byEdu: {
      prof:   { overall: 65.3, tax: 62.8, financial: 81.2, management: 75.1, interpLaw: 68.2, calculation: 39.9, journal: 79.3, multiChoice: 88.4, openText: 58.5, singleChoice: 88.5, journalEntry: 70.0, austrianTax: 62.8, mixedAcc: 75.1, ugb: null, ifrs: 81.2 },
      master: { overall: 90.0, tax: 77.8, financial: 90.7, management: 92.9, interpLaw: 90.0, calculation: null, journal: null, multiChoice: 91.0, openText: 95.0, singleChoice: 80.0, journalEntry: null, austrianTax: 75.8, mixedAcc: 90.6, ugb: 88.7, ifrs: 98.0 },
      voc:    { overall: 57.2, tax: 13.3, financial: 59.7, management: null, interpLaw: 70.0, calculation: 28.8, journal: 76.0, multiChoice: 100.0, openText: 49.0, singleChoice: 62.5, journalEntry: 76.4, austrianTax: 52.1, mixedAcc: null, ugb: 74.2, ifrs: null },
    },
    n: '564', priceIn: 1.75, priceOut: 14.0, cost: 0.017876, tokTask: 1699, speed: 79.8,
    calib: [
      {x:0.15,y:21.2,n:4},{x:0.25,y:7.5,n:4},{x:0.35,y:10.9,n:16},
      {x:0.45,y:21.9,n:18},{x:0.55,y:42.8,n:35},{x:0.65,y:59.0,n:138},
      {x:0.75,y:71.4,n:162},{x:0.85,y:94.8,n:99},{x:0.95,y:100.0,n:44},
    ],
  },

  // ── 5. claude-opus-4-6 ───────────────────────────────────
  {
    name: 'claude-opus-4-6', org: 'Anthropic', color: '#1e40af',
    overall: 66.9, tax: 59.1, financial: 76.6, management: 90.2,
    interpLaw: 69.9, calculation: 41.9, journal: 76.7,
    multiChoice: 88.5, openText: 55.2, singleChoice: 70.5, journalEntry: 76.9,
    austrianTax: 58.3, mixedAcc: 90.6, ugb: 76.0, ifrs: 88.0,
    eduProf: 61.7, eduMaster: 89.6, eduVoc: 57.0,
    byEdu: {
      prof:   { overall: 61.7, tax: 58.5, financial: 81.2, management: 75.5, interpLaw: 63.3, calculation: 44.8, journal: 85.0, multiChoice: 86.6, openText: 55.6, singleChoice: 69.2, journalEntry: 75.0, austrianTax: 58.5, mixedAcc: 75.5, ugb: null, ifrs: 81.2 },
      master: { overall: 89.6, tax: 82.6, financial: 87.4, management: 96.1, interpLaw: 89.6, calculation: null, journal: null, multiChoice: 89.4, openText: 100.0, singleChoice: 90.0, journalEntry: null, austrianTax: 81.1, mixedAcc: 95.1, ugb: 75.8, ifrs: 100.0 },
      voc:    { overall: 57.0, tax: 26.7, financial: 58.7, management: null, interpLaw: 59.5, calculation: 35.1, journal: 74.3, multiChoice: 100.0, openText: 51.0, singleChoice: 50.0, journalEntry: 77.5, austrianTax: 51.1, mixedAcc: null, ugb: 76.4, ifrs: null },
    },
    n: '564', priceIn: 5.0, priceOut: 25.0, cost: 0.028614, tokTask: 1684, speed: 40.2,
    calib: [{x:0.25,y:22.4,n:14}, {x:0.35,y:12.3,n:20}, {x:0.45,y:32.8,n:12}, {x:0.55,y:47.1,n:38}, {x:0.65,y:52.3,n:63}, {x:0.75,y:61.3,n:130}, {x:0.85,y:76.5,n:197}, {x:0.95,y:97.5,n:89}],
  },

  // ── 6. claude-sonnet-4-6 ───────────────────────────────────
  {
    name: 'claude-sonnet-4-6', org: 'Anthropic', color: '#3b82f6',
    overall: 64.0, tax: 54.4, financial: 77.0, management: 88.3,
    interpLaw: 67.2, calculation: 37.1, journal: 74.4,
    multiChoice: 87.7, openText: 50.0, singleChoice: 75.0, journalEntry: 79.6,
    austrianTax: 54.6, mixedAcc: 89.1, ugb: 80.5, ifrs: 84.0,
    eduProf: 56.8, eduMaster: 90.7, eduVoc: 59.2,
    byEdu: {
      prof:   { overall: 56.8, tax: 53.5, financial: 75.5, management: 78.1, interpLaw: 58.3, calculation: 39.7, journal: 83.6, multiChoice: 82.5, openText: 50.2, singleChoice: 65.4, journalEntry: 87.5, austrianTax: 53.5, mixedAcc: 78.1, ugb: null, ifrs: 75.5 },
      master: { overall: 90.7, tax: 86.8, financial: 90.6, management: 92.4, interpLaw: 90.7, calculation: null, journal: null, multiChoice: 90.7, openText: 100.0, singleChoice: 90.0, journalEntry: null, austrianTax: 85.6, mixedAcc: 92.4, ugb: 86.1, ifrs: 99.0 },
      voc:    { overall: 59.2, tax: 33.3, financial: 60.6, management: null, interpLaw: 87.0, calculation: 30.9, journal: 71.8, multiChoice: 75.0, openText: 47.1, singleChoice: 87.5, journalEntry: 76.8, austrianTax: 55.4, mixedAcc: null, ugb: 71.5, ifrs: null },
    },
    n: '564', priceIn: 3.0, priceOut: 15.0, cost: 0.015551, tokTask: 1578, speed: 44.5,
    calib: [
      {x:0.25,y:9.1,n:16},{x:0.35,y:20.4,n:14},{x:0.45,y:30.9,n:23},
      {x:0.55,y:42.3,n:37},{x:0.65,y:53.2,n:63},{x:0.75,y:65.7,n:117},
      {x:0.85,y:82.5,n:123},{x:0.95,y:97.1,n:69},
    ],
  },

  // ── 7. gpt-5-mini ───────────────────────────────────
  {
    name: 'gpt-5-mini', org: 'OpenAI', color: '#15803d',
    overall: 58.5, tax: 50.4, financial: 68.7, management: 82.7,
    interpLaw: 62.8, calculation: 27.0, journal: 63.2,
    multiChoice: 83.7, openText: 45.0, singleChoice: 65.9, journalEntry: 65.7,
    austrianTax: 50.2, mixedAcc: 80.6, ugb: 75.5, ifrs: 76.2,
    eduProf: 51.7, eduMaster: 85.7, eduVoc: 50.0,
    byEdu: {
      prof:   { overall: 51.7, tax: 49.9, financial: 63.3, management: 57.4, interpLaw: 54.2, calculation: 28.5, journal: 68.6, multiChoice: 77.6, openText: 45.4, singleChoice: 61.5, journalEntry: 76.2, austrianTax: 49.9, mixedAcc: 57.4, ugb: null, ifrs: 63.3 },
      master: { overall: 85.7, tax: 70.1, financial: 84.9, management: 92.8, interpLaw: 85.7, calculation: null, journal: null, multiChoice: 87.1, openText: 100.0, singleChoice: 70.0, journalEntry: null, austrianTax: 67.4, mixedAcc: 87.4, ugb: 85.3, ifrs: 99.0 },
      voc:    { overall: 50.0, tax: 21.0, financial: 51.7, management: null, interpLaw: 77.5, calculation: 23.5, journal: 61.7, multiChoice: 75.0, openText: 40.5, singleChoice: 75.0, journalEntry: 61.5, austrianTax: 47.7, mixedAcc: null, ugb: 58.3, ifrs: null },
    },
    n: '563/564', priceIn: 0.25, priceOut: 2.0, cost: 0.003254, tokTask: 2048, speed: 79.3,
    note: '1 task not completed for this model. Scored on 563/564 tasks.',
    calib: [{x:0.05,y:11.7,n:3}, {x:0.15,y:11.6,n:17}, {x:0.25,y:29.1,n:29}, {x:0.35,y:31.3,n:28}, {x:0.45,y:42.2,n:26}, {x:0.55,y:43.6,n:42}, {x:0.65,y:51.4,n:74}, {x:0.75,y:47.9,n:85}, {x:0.85,y:69.6,n:128}, {x:0.95,y:86.1,n:131}],
  },

  // ── 8. Kimi-K2.6 ───────────────────────────────────
  {
    name: 'Kimi-K2.6', org: 'Moonshot AI', color: '#7e22ce',
    overall: 57.3, tax: 45.6, financial: 72.6, management: 85.3,
    interpLaw: 59.8, calculation: 35.6, journal: 63.1,
    multiChoice: 86.0, openText: 39.0, singleChoice: 78.6, journalEntry: 66.3,
    austrianTax: 45.8, mixedAcc: 85.2, ugb: 72.9, ifrs: 83.4,
    eduProf: 49.0, eduMaster: 87.4, eduVoc: 50.6,
    byEdu: {
      prof:   { overall: 49.0, tax: 44.4, financial: 75.8, management: 71.4, interpLaw: 49.0, calculation: 38.4, journal: 85.0, multiChoice: 82.2, openText: 38.6, singleChoice: 79.2, journalEntry: 81.2, austrianTax: 44.4, mixedAcc: 71.4, ugb: null, ifrs: 75.8 },
      master: { overall: 87.4, tax: 81.9, financial: 86.5, management: 90.9, interpLaw: 87.4, calculation: null, journal: null, multiChoice: 88.0, openText: 95.0, singleChoice: 80.0, journalEntry: null, austrianTax: 80.3, mixedAcc: 89.2, ugb: 79.5, ifrs: 96.3 },
      voc:    { overall: 50.6, tax: 28.3, financial: 51.9, management: null, interpLaw: 80.0, calculation: 29.1, journal: 57.0, multiChoice: 100.0, openText: 40.7, singleChoice: 75.0, journalEntry: 60.9, austrianTax: 47.1, mixedAcc: null, ugb: 62.3, ifrs: null },
    },
    n: '549/564', priceIn: 0.95, priceOut: 4, cost: 0.052311, tokTask: 13524, speed: 41.7,
    note: '15 tasks not completed for this model. Scored on 549/564 tasks.',
    calib: [{x:0.05,y:35.0,n:2}, {x:0.15,y:0.0,n:1}, {x:0.45,y:0.0,n:2}, {x:0.55,y:17.0,n:5}, {x:0.65,y:26.0,n:7}, {x:0.75,y:18.4,n:19}, {x:0.85,y:37.6,n:225}, {x:0.95,y:77.4,n:288}],
  },

  // ── 9. Mistral-Large-3 ───────────────────────────────────
  {
    name: 'Mistral-Large-3', org: 'Mistral AI', color: '#c2410c',
    overall: 51.5, tax: 41.5, financial: 62.4, management: 85.5,
    interpLaw: 56.6, calculation: 22.7, journal: 39.4,
    multiChoice: 86.2, openText: 32.4, singleChoice: 70.5, journalEntry: 36.1,
    austrianTax: 41.6, mixedAcc: 86.4, ugb: 70.4, ifrs: 62.6,
    eduProf: 41.6, eduMaster: 89.2, eduVoc: 42.9,
    byEdu: {
      prof:   { overall: 41.6, tax: 40.5, financial: 41.9, management: 66.9, interpLaw: 44.4, calculation: 21.6, journal: 27.1, multiChoice: 80.6, openText: 31.9, singleChoice: 61.5, journalEntry: 25.0, austrianTax: 40.5, mixedAcc: 66.9, ugb: null, ifrs: 41.9 },
      master: { overall: 89.2, tax: 79.2, financial: 89.0, management: 93.0, interpLaw: 89.2, calculation: null, journal: null, multiChoice: 89.1, openText: 90.0, singleChoice: 90.0, journalEntry: null, austrianTax: 77.3, mixedAcc: 92.1, ugb: 84.8, ifrs: 99.0 },
      voc:    { overall: 42.9, tax: 6.7, financial: 44.9, management: null, interpLaw: 80.0, calculation: 25.2, journal: 42.9, multiChoice: 100.0, openText: 35.0, singleChoice: 75.0, journalEntry: 40.2, austrianTax: 41.6, mixedAcc: null, ugb: 47.1, ifrs: null },
    },
    n: '564', priceIn: 0.5, priceOut: 1.5, cost: 0.001419, tokTask: 1307, speed: 48.2,
    calib: [{x:0.05,y:70.0,n:1}, {x:0.35,y:10.0,n:1}, {x:0.65,y:85.0,n:1}, {x:0.75,y:40.7,n:3}, {x:0.85,y:35.6,n:52}, {x:0.95,y:53.2,n:506}],
  },

  // ── 10. grok-4-fast-reasoning ───────────────────────────────────
  {
    name: 'grok-4-fast-reasoning', org: 'xAI', color: '#0f766e',
    overall: 50.3, tax: 38.8, financial: 64.3, management: 84.5,
    interpLaw: 52.5, calculation: 31.3, journal: 57.1,
    multiChoice: 83.0, openText: 31.0, singleChoice: 68.2, journalEntry: 62.2,
    austrianTax: 39.2, mixedAcc: 79.7, ugb: 62.9, ifrs: 76.3,
    eduProf: 41.9, eduMaster: 80.0, eduVoc: 47.5,
    byEdu: {
      prof:   { overall: 41.9, tax: 37.9, financial: 64.4, management: 67.7, interpLaw: 42.1, calculation: 35.0, journal: 55.7, multiChoice: 83.5, openText: 30.2, singleChoice: 73.1, journalEntry: 57.5, austrianTax: 37.9, mixedAcc: 67.7, ugb: null, ifrs: 64.4 },
      master: { overall: 80.0, tax: 68.7, financial: 76.3, management: 91.2, interpLaw: 80.0, calculation: null, journal: null, multiChoice: 82.8, openText: 90.0, singleChoice: 50.0, journalEntry: null, austrianTax: 65.9, mixedAcc: 83.2, ugb: 63.4, ifrs: 97.3 },
      voc:    { overall: 47.5, tax: 27.7, financial: 48.6, management: null, interpLaw: 74.5, calculation: 22.7, journal: 57.5, multiChoice: 75.0, openText: 35.6, singleChoice: 75.0, journalEntry: 63.9, austrianTax: 43.0, mixedAcc: null, ugb: 62.2, ifrs: null },
    },
    n: '564', priceIn: 0.2, priceOut: 0.5, cost: 0.00124, tokTask: 2797, speed: 171.7,
    calib: [
      {x:0.55,y:5.0,n:4},{x:0.65,y:2.5,n:8},{x:0.75,y:8.4,n:20},
      {x:0.85,y:30.8,n:212},{x:0.95,y:68.4,n:274},
    ],
  },

  // ── 11. gpt-4o ───────────────────────────────────
  {
    name: 'gpt-4o', org: 'OpenAI', color: '#16a34a',
    overall: 47.1, tax: 38.2, financial: 56.2, management: 79.8,
    interpLaw: 53.3, calculation: 13.3, journal: 34.4,
    multiChoice: 82.2, openText: 28.3, singleChoice: 63.6, journalEntry: 32.8,
    austrianTax: 37.8, mixedAcc: 80.8, ugb: 71.9, ifrs: 52.8,
    eduProf: 36.2, eduMaster: 89.3, eduVoc: 36.1,
    byEdu: {
      prof:   { overall: 36.2, tax: 36.9, financial: 25.9, management: 49.7, interpLaw: 39.8, calculation: 13.7, journal: 20.0, multiChoice: 67.5, openText: 28.6, singleChoice: 53.8, journalEntry: 10.0, austrianTax: 36.9, mixedAcc: 49.7, ugb: null, ifrs: 25.9 },
      master: { overall: 89.3, tax: 79.9, financial: 89.7, management: 91.8, interpLaw: 89.3, calculation: null, journal: null, multiChoice: 90.1, openText: 100.0, singleChoice: 80.0, journalEntry: null, austrianTax: 78.0, mixedAcc: 89.9, ugb: 90.1, ifrs: 100.0 },
      voc:    { overall: 36.1, tax: 6.7, financial: 37.7, management: null, interpLaw: 80.0, calculation: 12.3, journal: 38.5, multiChoice: 100.0, openText: 24.1, singleChoice: 75.0, journalEntry: 41.1, austrianTax: 34.1, mixedAcc: null, ugb: 42.5, ifrs: null },
    },
    n: '564', priceIn: 2.5, priceOut: 10.0, cost: 0.003193, tokTask: 681, speed: 134.2,
    calib: [
      {x:0.05,y:0.0,n:4},{x:0.15,y:0.0,n:3},{x:0.25,y:8.0,n:5},
      {x:0.35,y:12.5,n:4},{x:0.45,y:8.8,n:4},{x:0.55,y:22.5,n:4},
      {x:0.85,y:59.1,n:238},{x:0.95,y:57.5,n:188},
    ],
  },

  // ── 12. DeepSeek-V3.2 ───────────────────────────────────
  {
    name: 'DeepSeek-V3.2', org: 'DeepSeek', color: '#4338ca',
    overall: 45.5, tax: 35.7, financial: 57.8, management: 74.1,
    interpLaw: 50.1, calculation: 20.3, journal: 32.3,
    multiChoice: 79.1, openText: 27.5, singleChoice: 65.9, journalEntry: 25.2,
    austrianTax: 35.3, mixedAcc: 76.6, ugb: 53.5, ifrs: 69.6,
    eduProf: 37.1, eduMaster: 81.2, eduVoc: 31.1,
    byEdu: {
      prof:   { overall: 37.1, tax: 34.7, financial: 54.8, management: 37.0, interpLaw: 38.6, calculation: 23.9, journal: 30.7, multiChoice: 77.0, openText: 27.6, singleChoice: 57.7, journalEntry: 25.0, austrianTax: 34.7, mixedAcc: 37.0, ugb: null, ifrs: 54.8 },
      master: { overall: 81.2, tax: 66.0, financial: 79.9, management: 89.0, interpLaw: 81.2, calculation: null, journal: null, multiChoice: 80.2, openText: 95.0, singleChoice: 90.0, journalEntry: null, austrianTax: 65.9, mixedAcc: 88.1, ugb: 69.3, ifrs: 95.7 },
      voc:    { overall: 31.1, tax: 21.0, financial: 31.6, management: null, interpLaw: 67.0, calculation: 12.0, journal: 32.7, multiChoice: 75.0, openText: 24.6, singleChoice: 62.5, journalEntry: 25.3, austrianTax: 32.0, mixedAcc: null, ugb: 27.9, ifrs: null },
    },
    n: '564', priceIn: 0.28, priceOut: 0.42, cost: 0.000313, tokTask: 925, speed: 35.7,
    calib: [{x:0.05,y:30.0,n:2}, {x:0.15,y:6.0,n:5}, {x:0.25,y:0.0,n:6}, {x:0.35,y:4.0,n:5}, {x:0.45,y:0.0,n:4}, {x:0.55,y:3.3,n:6}, {x:0.65,y:12.7,n:12}, {x:0.75,y:17.8,n:26}, {x:0.85,y:44.2,n:419}, {x:0.95,y:81.2,n:79}],
  },

  // ── 13. mercury-2 ───────────────────────────────────
  {
    name: 'mercury-2', org: 'Inception Labs', color: '#7c3aed',
    overall: 43.5, tax: 32.4, financial: 56.8, management: 77.2,
    interpLaw: 47.8, calculation: 18.7, journal: 34.3,
    multiChoice: 78.2, openText: 23.0, singleChoice: 70.5, journalEntry: 37.5,
    austrianTax: 32.6, mixedAcc: 77.9, ugb: 62.8, ifrs: 60.9,
    eduProf: 32.7, eduMaster: 82.4, eduVoc: 37.9,
    byEdu: {
      prof:   { overall: 32.7, tax: 31.3, financial: 39.2, management: 47.1, interpLaw: 34.8, calculation: 19.6, journal: 13.6, multiChoice: 70.5, openText: 22.4, singleChoice: 65.4, journalEntry: 13.8, austrianTax: 31.3, mixedAcc: 47.1, ugb: null, ifrs: 39.2 },
      master: { overall: 82.4, tax: 66.0, financial: 81.8, management: 89.2, interpLaw: 82.4, calculation: null, journal: null, multiChoice: 82.4, openText: 100.0, singleChoice: 80.0, journalEntry: null, austrianTax: 62.9, mixedAcc: 86.9, ugb: 73.0, ifrs: 99.0 },
      voc:    { overall: 37.9, tax: 21.0, financial: 38.9, management: null, interpLaw: 77.0, calculation: 16.7, journal: 40.1, multiChoice: 75.0, openText: 26.1, singleChoice: 75.0, journalEntry: 46.1, austrianTax: 35.4, mixedAcc: null, ugb: 46.3, ifrs: null },
    },
    n: '564', priceIn: 0.25, priceOut: 0.75, cost: 0.000885, tokTask: 1492, speed: 1023.0,
    calib: [
      {x:0.25,y:2.0,n:5},{x:0.35,y:0.0,n:5},{x:0.45,y:13.3,n:6},
      {x:0.55,y:7.5,n:4},{x:0.65,y:5.0,n:9},{x:0.75,y:13.8,n:6},
      {x:0.85,y:31.2,n:30},{x:0.95,y:47.6,n:453},
    ],
  },

];
