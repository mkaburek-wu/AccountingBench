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
  date:                 'August 2026',
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

  // ── 1. claude-opus-5 ───────────────────────────────────
  {
    name: 'claude-opus-5', org: 'Anthropic', color: '#3b82f6',
    overall: 83.3, tax: 81.7, financial: 84.8, management: 90.2,
    interpLaw: 88.8, calculation: 45.1, journal: 83.8,
    multiChoice: 94.0, openText: 76.8, singleChoice: 93.2, journalEntry: 87.5,
    austrianTax: 79.6, mixedAcc: 92.2, ugb: 87.8, ifrs: 93.8,
    eduProf: 82.9, eduMaster: 94.2, eduVoc: 63.9,
    byEdu: {
      prof:   { overall: 82.9, tax: 82.0, financial: 90.9, management: 78.6, interpLaw: 86.8, calculation: 52.5, journal: 86.4, multiChoice: 94.7, openText: 80.0, singleChoice: 92.3, journalEntry: 80.0, austrianTax: 82.0, mixedAcc: 78.6, ugb: null, ifrs: 90.9 },
      master: { overall: 94.2, tax: 93.1, financial: 94.1, management: 94.8, interpLaw: 94.2, calculation: null, journal: null, multiChoice: 93.6, openText: 100.0, singleChoice: 100.0, journalEntry: null, austrianTax: 92.4, mixedAcc: 96.2, ugb: 90.1, ifrs: 99.0 },
      voc:    { overall: 63.9, tax: 0.0, financial: 67.5, management: null, interpLaw: 90.0, calculation: 28.6, journal: 83.1, multiChoice: 100.0, openText: 49.6, singleChoice: 87.5, journalEntry: 90.3, austrianTax: 57.8, mixedAcc: null, ugb: 84.1, ifrs: null },
    },
    n: '564', priceIn: 5.0, priceOut: 25.0, cost: 0.104625, tokTask: 5006, speed: 51.0,
    calib: [{x:0.35,y:0.0,n:1}, {x:0.45,y:25.0,n:8}, {x:0.55,y:38.2,n:32}, {x:0.65,y:68.9,n:72}, {x:0.75,y:83.9,n:200}, {x:0.85,y:93.1,n:171}, {x:0.95,y:98.8,n:80}],
  },

  // ── 2. claude-fable-5 ───────────────────────────────────
  {
    name: 'claude-fable-5', org: 'Anthropic', color: '#3b82f6',
    overall: 80.6, tax: 81.1, financial: 78.1, management: 85.5,
    interpLaw: 86.6, calculation: 41.8, journal: 73.6,
    multiChoice: 91.4, openText: 75.7, singleChoice: 84.1, journalEntry: 71.6,
    austrianTax: 78.1, mixedAcc: 88.5, ugb: 79.3, ifrs: 90.6,
    eduProf: 81.2, eduMaster: 90.5, eduVoc: 55.8,
    byEdu: {
      prof:   { overall: 81.2, tax: 81.3, financial: 85.2, management: 64.6, interpLaw: 86.0, calculation: 45.7, journal: 74.3, multiChoice: 94.5, openText: 78.8, singleChoice: 88.5, journalEntry: 58.8, austrianTax: 81.3, mixedAcc: 64.6, ugb: null, ifrs: 85.2 },
      master: { overall: 90.5, tax: 86.1, financial: 89.6, management: 93.8, interpLaw: 90.5, calculation: null, journal: null, multiChoice: 89.5, openText: 100.0, singleChoice: 100.0, journalEntry: null, austrianTax: 84.8, mixedAcc: 95.5, ugb: 83.7, ifrs: 100.0 },
      voc:    { overall: 55.8, tax: 33.3, financial: 57.1, management: null, interpLaw: 60.0, calculation: 32.9, journal: 73.4, multiChoice: 100.0, openText: 49.6, singleChoice: 50.0, journalEntry: 76.3, austrianTax: 50.8, mixedAcc: null, ugb: 72.2, ifrs: null },
    },
    n: '564', priceIn: 10.0, priceOut: 50.0, cost: 0.121125, tokTask: 3244, speed: 66.0,
    calib: [{x:0.25,y:0.0,n:2}, {x:0.35,y:18.0,n:10}, {x:0.45,y:21.5,n:10}, {x:0.55,y:40.6,n:18}, {x:0.65,y:53.2,n:31}, {x:0.75,y:71.3,n:100}, {x:0.85,y:87.1,n:269}, {x:0.95,y:97.8,n:124}],
  },

  // ── 3. gpt-5.5 ───────────────────────────────────
  {
    name: 'gpt-5.5', org: 'OpenAI', color: '#14532d',
    overall: 80.1, tax: 77.7, financial: 83.1, management: 86.6,
    interpLaw: 83.8, calculation: 53.8, journal: 79.5,
    multiChoice: 91.7, openText: 74.0, singleChoice: 84.1, journalEntry: 79.6,
    austrianTax: 76.6, mixedAcc: 89.4, ugb: 82.0, ifrs: 89.8,
    eduProf: 78.1, eduMaster: 92.2, eduVoc: 69.0,
    byEdu: {
      prof:   { overall: 78.1, tax: 77.6, financial: 84.0, management: 71.0, interpLaw: 81.5, calculation: 48.4, journal: 95.0, multiChoice: 91.2, openText: 74.5, singleChoice: 88.5, journalEntry: 91.2, austrianTax: 77.6, mixedAcc: 71.0, ugb: null, ifrs: 84.0 },
      master: { overall: 92.2, tax: 84.7, financial: 93.2, management: 92.9, interpLaw: 92.2, calculation: null, journal: null, multiChoice: 91.9, openText: 50.0, singleChoice: 100.0, journalEntry: null, austrianTax: 83.3, mixedAcc: 94.8, ugb: 86.1, ifrs: 100.0 },
      voc:    { overall: 69.0, tax: 65.0, financial: 69.3, management: null, interpLaw: 60.0, calculation: 66.0, journal: 75.1, multiChoice: 100.0, openText: 70.5, singleChoice: 50.0, journalEntry: 75.3, austrianTax: 67.1, mixedAcc: null, ugb: 75.3, ifrs: null },
    },
    n: '564', priceIn: 5.0, priceOut: 30.0, cost: 0.034981, tokTask: 1608, speed: 57,
    calib: [{x:0.25,y:75.0,n:1}, {x:0.35,y:0.0,n:1}, {x:0.45,y:5.0,n:2}, {x:0.55,y:40.8,n:13}, {x:0.65,y:44.4,n:19}, {x:0.75,y:66.3,n:111}, {x:0.85,y:81.1,n:238}, {x:0.95,y:95.2,n:179}],
  },

  // ── 4. gpt-5.6-sol ───────────────────────────────────
  {
    name: 'gpt-5.6-sol', org: 'OpenAI', color: '#3b82f6',
    overall: 78.6, tax: 76.6, financial: 80.8, management: 85.0,
    interpLaw: 84.2, calculation: 39.5, journal: 78.0,
    multiChoice: 90.1, openText: 72.2, singleChoice: 90.9, journalEntry: 73.1,
    austrianTax: 75.7, mixedAcc: 88.1, ugb: 75.1, ifrs: 89.2,
    eduProf: 77.5, eduMaster: 89.6, eduVoc: 63.7,
    byEdu: {
      prof:   { overall: 77.5, tax: 77.2, financial: 83.1, management: 65.3, interpLaw: 82.2, calculation: 41.0, journal: 80.0, multiChoice: 93.2, openText: 74.2, singleChoice: 88.5, journalEntry: 72.5, austrianTax: 77.2, mixedAcc: 65.3, ugb: null, ifrs: 83.1 },
      master: { overall: 89.6, tax: 79.2, financial: 89.8, management: 92.9, interpLaw: 89.6, calculation: null, journal: null, multiChoice: 88.5, openText: 100.0, singleChoice: 100.0, journalEntry: null, austrianTax: 80.3, mixedAcc: 94.8, ugb: 79.6, ifrs: 100.0 },
      voc:    { overall: 63.7, tax: 0.0, financial: 67.3, management: null, interpLaw: 87.5, calculation: 36.0, journal: 77.5, multiChoice: 75.0, openText: 55.1, singleChoice: 87.5, journalEntry: 73.4, austrianTax: 62.4, mixedAcc: null, ugb: 67.8, ifrs: null },
    },
    n: '564', priceIn: 5.0, priceOut: 30.0, cost: 0.064875, tokTask: 2617, speed: 64.0,
    calib: [{x:0.45,y:20.0,n:2}, {x:0.55,y:24.7,n:3}, {x:0.65,y:16.4,n:11}, {x:0.75,y:50.6,n:34}, {x:0.85,y:66.7,n:141}, {x:0.95,y:88.3,n:373}],
  },

  // ── 5. claude-opus-4-7 ───────────────────────────────────
  {
    name: 'claude-opus-4-7', org: 'Anthropic', color: '#1d4ed8',
    overall: 74.6, tax: 70.4, financial: 78.5, management: 91.6,
    interpLaw: 79.2, calculation: 42.5, journal: 73.4,
    multiChoice: 90.5, openText: 65.9, singleChoice: 81.8, journalEntry: 74.0,
    austrianTax: 69.1, mixedAcc: 91.8, ugb: 81.9, ifrs: 86.8,
    eduProf: 71.7, eduMaster: 91.6, eduVoc: 60.2,
    byEdu: {
      prof:   { overall: 71.7, tax: 70.2, financial: 79.8, management: 80.2, interpLaw: 74.9, calculation: 44.3, journal: 80.0, multiChoice: 88.6, openText: 67.5, singleChoice: 80.8, journalEntry: 72.5, austrianTax: 70.2, mixedAcc: 80.2, ugb: null, ifrs: 79.8 },
      master: { overall: 91.6, tax: 82.6, financial: 90.8, management: 96.2, interpLaw: 91.6, calculation: null, journal: null, multiChoice: 91.7, openText: 100.0, singleChoice: 90.0, journalEntry: null, austrianTax: 81.1, mixedAcc: 95.1, ugb: 88.5, ifrs: 99.0 },
      voc:    { overall: 60.2, tax: 38.3, financial: 61.4, management: null, interpLaw: 77.5, calculation: 38.4, journal: 71.5, multiChoice: 75.0, openText: 52.1, singleChoice: 75.0, journalEntry: 74.5, austrianTax: 56.9, mixedAcc: null, ugb: 71.2, ifrs: null },
    },
    n: '564', priceIn: 5, priceOut: 25, cost: 0.03107, tokTask: 2050, speed: 37,
    calib: [{x:0.35,y:15.5,n:11}, {x:0.45,y:27.5,n:16}, {x:0.55,y:29.7,n:31}, {x:0.65,y:57.4,n:49}, {x:0.75,y:69.1,n:134}, {x:0.85,y:83.6,n:219}, {x:0.95,y:97.7,n:104}],
  },

  // ── 6. gpt-5.4 ───────────────────────────────────
  {
    name: 'gpt-5.4', org: 'OpenAI', color: '#0d4a2a',
    overall: 73.1, tax: 68.6, financial: 78.0, management: 88.1,
    interpLaw: 78.0, calculation: 37.6, journal: 73.3,
    multiChoice: 90.3, openText: 62.9, singleChoice: 86.4, journalEntry: 71.3,
    austrianTax: 67.2, mixedAcc: 88.2, ugb: 82.4, ifrs: 85.1,
    eduProf: 70.0, eduMaster: 90.6, eduVoc: 58.3,
    byEdu: {
      prof:   { overall: 70.0, tax: 68.7, financial: 77.8, management: 76.3, interpLaw: 73.5, calculation: 40.4, journal: 76.4, multiChoice: 89.7, openText: 64.5, singleChoice: 88.5, journalEntry: 63.8, austrianTax: 68.7, mixedAcc: 76.3, ugb: null, ifrs: 77.8 },
      master: { overall: 90.6, tax: 77.8, financial: 91.7, management: 92.9, interpLaw: 90.6, calculation: null, journal: null, multiChoice: 90.6, openText: 100.0, singleChoice: 90.0, journalEntry: null, austrianTax: 75.8, mixedAcc: 91.7, ugb: 88.3, ifrs: 98.0 },
      voc:    { overall: 58.3, tax: 23.3, financial: 60.3, management: null, interpLaw: 79.5, calculation: 31.5, journal: 72.4, multiChoice: 100.0, openText: 48.7, singleChoice: 75.0, journalEntry: 74.1, austrianTax: 54.0, mixedAcc: null, ugb: 72.7, ifrs: null },
    },
    n: '564', priceIn: 2.5, priceOut: 15.0, cost: 0.024983, tokTask: 2112, speed: 83.3,
    calib: [{x:0.25,y:85.0,n:2}, {x:0.35,y:0.0,n:1}, {x:0.45,y:18.6,n:11}, {x:0.55,y:17.5,n:22}, {x:0.65,y:44.6,n:25}, {x:0.75,y:57.1,n:87}, {x:0.85,y:68.5,n:152}, {x:0.95,y:90.7,n:264}],
  },

  // ── 7. claude-opus-4-8 ───────────────────────────────────
  {
    name: 'claude-opus-4-8', org: 'Anthropic', color: '#3b82f6',
    overall: 72.2, tax: 67.6, financial: 76.6, management: 89.9,
    interpLaw: 76.4, calculation: 39.5, journal: 76.3,
    multiChoice: 88.5, openText: 63.2, singleChoice: 77.3, journalEntry: 79.9,
    austrianTax: 65.9, mixedAcc: 90.4, ugb: 80.4, ifrs: 86.4,
    eduProf: 69.4, eduMaster: 90.3, eduVoc: 54.2,
    byEdu: {
      prof:   { overall: 69.4, tax: 67.8, financial: 79.3, management: 77.2, interpLaw: 71.5, calculation: 48.6, journal: 83.6, multiChoice: 85.6, openText: 65.8, singleChoice: 73.1, journalEntry: 78.8, austrianTax: 67.8, mixedAcc: 77.2, ugb: null, ifrs: 79.3 },
      master: { overall: 90.3, tax: 79.9, financial: 89.7, management: 95.0, interpLaw: 90.3, calculation: null, journal: null, multiChoice: 90.2, openText: 100.0, singleChoice: 90.0, journalEntry: null, austrianTax: 78.0, mixedAcc: 94.3, ugb: 84.5, ifrs: 99.0 },
      voc:    { overall: 54.2, tax: 0.0, financial: 57.3, management: null, interpLaw: 77.5, calculation: 19.3, journal: 74.3, multiChoice: 75.0, openText: 41.1, singleChoice: 75.0, journalEntry: 80.3, austrianTax: 48.4, mixedAcc: null, ugb: 73.7, ifrs: null },
    },
    n: '564', priceIn: 5.0, priceOut: 25.0, cost: 0.032051, tokTask: 2103, speed: 59.0,
    calib: [{x:0.35,y:7.1,n:7}, {x:0.45,y:18.4,n:25}, {x:0.55,y:44.7,n:44}, {x:0.65,y:58.6,n:83}, {x:0.75,y:72.3,n:143}, {x:0.85,y:84.9,n:200}, {x:0.95,y:97.8,n:62}],
  },

  // ── 8. gpt-5.6-terra ───────────────────────────────────
  {
    name: 'gpt-5.6-terra', org: 'OpenAI', color: '#3b82f6',
    overall: 70.3, tax: 63.6, financial: 80.2, management: 84.7,
    interpLaw: 74.6, calculation: 34.9, journal: 79.3,
    multiChoice: 89.0, openText: 58.8, singleChoice: 86.4, journalEntry: 81.7,
    austrianTax: 63.1, mixedAcc: 87.9, ugb: 81.6, ifrs: 87.8,
    eduProf: 65.6, eduMaster: 92.2, eduVoc: 58.3,
    byEdu: {
      prof:   { overall: 65.6, tax: 63.7, financial: 81.5, management: 59.7, interpLaw: 67.9, calculation: 39.9, journal: 95.7, multiChoice: 84.6, openText: 60.3, singleChoice: 80.8, journalEntry: 100.0, austrianTax: 63.7, mixedAcc: 59.7, ugb: null, ifrs: 81.5 },
      master: { overall: 92.2, tax: 76.4, financial: 93.6, management: 94.8, interpLaw: 92.2, calculation: null, journal: null, multiChoice: 91.3, openText: 100.0, singleChoice: 100.0, journalEntry: null, austrianTax: 77.3, mixedAcc: 96.2, ugb: 88.1, ifrs: 99.0 },
      voc:    { overall: 58.3, tax: 0.0, financial: 61.6, management: null, interpLaw: 90.0, calculation: 23.6, journal: 74.8, multiChoice: 100.0, openText: 45.5, singleChoice: 87.5, journalEntry: 75.1, austrianTax: 54.4, mixedAcc: null, ugb: 71.2, ifrs: null },
    },
    n: '564', priceIn: 2.0, priceOut: 12.0, cost: 0.024684, tokTask: 2511, speed: 126.0,
    calib: [{x:0.55,y:33.4,n:9}, {x:0.65,y:15.4,n:22}, {x:0.75,y:44.5,n:80}, {x:0.85,y:62.4,n:197}, {x:0.95,y:90.5,n:256}],
  },

  // ── 9. gpt-5.2 ───────────────────────────────────
  {
    name: 'gpt-5.2', org: 'OpenAI', color: '#166534',
    overall: 70.2, tax: 63.9, financial: 78.3, management: 87.8,
    interpLaw: 73.9, calculation: 39.8, journal: 76.7,
    multiChoice: 90.1, openText: 58.6, singleChoice: 81.8, journalEntry: 74.7,
    austrianTax: 62.9, mixedAcc: 87.1, ugb: 83.1, ifrs: 87.3,
    eduProf: 66.2, eduMaster: 90.0, eduVoc: 57.2,
    byEdu: {
      prof:   { overall: 66.2, tax: 63.9, financial: 81.2, management: 75.1, interpLaw: 68.4, calculation: 44.7, journal: 79.3, multiChoice: 88.4, openText: 59.7, singleChoice: 88.5, journalEntry: 70.0, austrianTax: 63.9, mixedAcc: 75.1, ugb: null, ifrs: 81.2 },
      master: { overall: 90.0, tax: 77.8, financial: 90.7, management: 92.9, interpLaw: 90.0, calculation: null, journal: null, multiChoice: 91.0, openText: 95.0, singleChoice: 80.0, journalEntry: null, austrianTax: 75.8, mixedAcc: 90.6, ugb: 88.7, ifrs: 98.0 },
      voc:    { overall: 57.2, tax: 13.3, financial: 59.7, management: null, interpLaw: 70.0, calculation: 28.8, journal: 76.0, multiChoice: 100.0, openText: 49.0, singleChoice: 62.5, journalEntry: 76.4, austrianTax: 52.1, mixedAcc: null, ugb: 74.2, ifrs: null },
    },
    n: '564', priceIn: 1.75, priceOut: 14.0, cost: 0.018687, tokTask: 1799, speed: 79.8,
    calib: [{x:0.15,y:42.5,n:2}, {x:0.25,y:11.8,n:6}, {x:0.35,y:16.7,n:15}, {x:0.45,y:25.0,n:17}, {x:0.55,y:42.1,n:36}, {x:0.65,y:60.5,n:156}, {x:0.75,y:73.8,n:183}, {x:0.85,y:94.2,n:102}, {x:0.95,y:100.0,n:47}],
  },

  // ── 10. claude-sonnet-5 ───────────────────────────────────
  {
    name: 'claude-sonnet-5', org: 'Anthropic', color: '#3b82f6',
    overall: 69.1, tax: 63.2, financial: 76.5, management: 85.5,
    interpLaw: 73.4, calculation: 32.4, journal: 79.8,
    multiChoice: 89.5, openText: 57.9, singleChoice: 72.7, journalEntry: 87.8,
    austrianTax: 61.2, mixedAcc: 85.3, ugb: 82.3, ifrs: 89.7,
    eduProf: 65.6, eduMaster: 90.1, eduVoc: 50.0,
    byEdu: {
      prof:   { overall: 65.6, tax: 63.2, financial: 84.4, management: 62.7, interpLaw: 67.8, calculation: 42.3, journal: 91.4, multiChoice: 87.2, openText: 60.5, singleChoice: 73.1, journalEntry: 92.5, austrianTax: 63.2, mixedAcc: 62.7, ugb: null, ifrs: 84.4 },
      master: { overall: 90.1, tax: 79.2, financial: 89.6, management: 94.7, interpLaw: 90.1, calculation: null, journal: null, multiChoice: 90.9, openText: 100.0, singleChoice: 80.0, journalEntry: null, austrianTax: 77.3, mixedAcc: 91.9, ugb: 84.5, ifrs: 99.0 },
      voc:    { overall: 50.0, tax: 0.0, financial: 52.9, management: null, interpLaw: 67.5, calculation: 10.2, journal: 76.5, multiChoice: 75.0, openText: 35.6, singleChoice: 62.5, journalEntry: 86.2, austrianTax: 41.4, mixedAcc: null, ugb: 78.7, ifrs: null },
    },
    n: '564', priceIn: 2.0, priceOut: 10.0, cost: 0.052268, tokTask: 6047, speed: 59.0,
    calib: [{x:0.15,y:12.0,n:5}, {x:0.25,y:6.2,n:12}, {x:0.35,y:15.0,n:11}, {x:0.45,y:26.5,n:17}, {x:0.55,y:55.6,n:116}, {x:0.65,y:66.4,n:133}, {x:0.75,y:69.4,n:85}, {x:0.85,y:90.3,n:137}, {x:0.95,y:96.9,n:48}],
  },

  // ── 11. gpt-5.6-luna ───────────────────────────────────
  {
    name: 'gpt-5.6-luna', org: 'OpenAI', color: '#3b82f6',
    overall: 68.5, tax: 61.1, financial: 78.8, management: 86.2,
    interpLaw: 72.1, calculation: 36.8, journal: 80.4,
    multiChoice: 89.9, openText: 55.2, singleChoice: 86.4, journalEntry: 81.1,
    austrianTax: 60.8, mixedAcc: 87.5, ugb: 84.5, ifrs: 86.4,
    eduProf: 63.4, eduMaster: 90.0, eduVoc: 59.7,
    byEdu: {
      prof:   { overall: 63.4, tax: 61.2, financial: 79.5, management: 66.1, interpLaw: 65.7, calculation: 41.1, journal: 81.4, multiChoice: 90.1, openText: 55.9, singleChoice: 88.5, journalEntry: 67.5, austrianTax: 61.2, mixedAcc: 66.1, ugb: null, ifrs: 79.5 },
      master: { overall: 90.0, tax: 75.0, financial: 90.5, management: 94.2, interpLaw: 90.0, calculation: null, journal: null, multiChoice: 89.9, openText: 100.0, singleChoice: 90.0, journalEntry: null, austrianTax: 75.8, mixedAcc: 93.7, ugb: 88.1, ifrs: 98.7 },
      voc:    { overall: 59.7, tax: 0.0, financial: 63.1, management: null, interpLaw: 77.5, calculation: 27.0, journal: 80.1, multiChoice: 75.0, openText: 47.8, singleChoice: 75.0, journalEntry: 86.1, austrianTax: 54.0, mixedAcc: null, ugb: 78.6, ifrs: null },
    },
    n: '564', priceIn: 0.2, priceOut: 1.2, cost: 0.002321, tokTask: 2389, speed: 187.0,
    calib: [{x:0.45,y:17.3,n:3}, {x:0.55,y:35.0,n:4}, {x:0.65,y:11.3,n:13}, {x:0.75,y:29.5,n:32}, {x:0.85,y:51.6,n:155}, {x:0.95,y:82.3,n:357}],
  },

  // ── 12. claude-opus-4-6 ───────────────────────────────────
  {
    name: 'claude-opus-4-6', org: 'Anthropic', color: '#1e40af',
    overall: 67.3, tax: 59.6, financial: 76.6, management: 90.2,
    interpLaw: 70.1, calculation: 42.9, journal: 76.7,
    multiChoice: 88.5, openText: 55.8, singleChoice: 70.5, journalEntry: 76.9,
    austrianTax: 58.8, mixedAcc: 90.6, ugb: 76.0, ifrs: 88.0,
    eduProf: 62.1, eduMaster: 89.6, eduVoc: 57.0,
    byEdu: {
      prof:   { overall: 62.1, tax: 59.1, financial: 81.2, management: 75.5, interpLaw: 63.6, calculation: 46.4, journal: 85.0, multiChoice: 86.6, openText: 56.2, singleChoice: 69.2, journalEntry: 75.0, austrianTax: 59.1, mixedAcc: 75.5, ugb: null, ifrs: 81.2 },
      master: { overall: 89.6, tax: 82.6, financial: 87.4, management: 96.1, interpLaw: 89.6, calculation: null, journal: null, multiChoice: 89.4, openText: 100.0, singleChoice: 90.0, journalEntry: null, austrianTax: 81.1, mixedAcc: 95.1, ugb: 75.8, ifrs: 100.0 },
      voc:    { overall: 57.0, tax: 26.7, financial: 58.7, management: null, interpLaw: 59.5, calculation: 35.1, journal: 74.3, multiChoice: 100.0, openText: 51.0, singleChoice: 50.0, journalEntry: 77.5, austrianTax: 51.1, mixedAcc: null, ugb: 76.4, ifrs: null },
    },
    n: '564', priceIn: 5.0, priceOut: 25.0, cost: 0.030985, tokTask: 1841, speed: 40.2,
    calib: [{x:0.25,y:18.1,n:8}, {x:0.35,y:17.2,n:21}, {x:0.45,y:28.9,n:15}, {x:0.55,y:47.1,n:38}, {x:0.65,y:52.3,n:63}, {x:0.75,y:61.3,n:130}, {x:0.85,y:76.6,n:198}, {x:0.95,y:97.5,n:90}],
  },

  // ── 13. claude-sonnet-4-6 ───────────────────────────────────
  {
    name: 'claude-sonnet-4-6', org: 'Anthropic', color: '#3b82f6',
    overall: 64.7, tax: 55.4, financial: 77.0, management: 88.3,
    interpLaw: 67.3, calculation: 40.3, journal: 74.4,
    multiChoice: 87.7, openText: 51.0, singleChoice: 75.0, journalEntry: 79.6,
    austrianTax: 55.5, mixedAcc: 89.1, ugb: 80.5, ifrs: 84.0,
    eduProf: 57.7, eduMaster: 90.7, eduVoc: 59.2,
    byEdu: {
      prof:   { overall: 57.7, tax: 54.5, financial: 75.5, management: 78.1, interpLaw: 58.6, calculation: 44.5, journal: 83.6, multiChoice: 82.5, openText: 51.3, singleChoice: 65.4, journalEntry: 87.5, austrianTax: 54.5, mixedAcc: 78.1, ugb: null, ifrs: 75.5 },
      master: { overall: 90.7, tax: 86.8, financial: 90.6, management: 92.4, interpLaw: 90.7, calculation: null, journal: null, multiChoice: 90.7, openText: 100.0, singleChoice: 90.0, journalEntry: null, austrianTax: 85.6, mixedAcc: 92.4, ugb: 86.1, ifrs: 99.0 },
      voc:    { overall: 59.2, tax: 33.3, financial: 60.6, management: null, interpLaw: 87.0, calculation: 30.9, journal: 71.8, multiChoice: 75.0, openText: 47.1, singleChoice: 87.5, journalEntry: 76.8, austrianTax: 55.4, mixedAcc: null, ugb: 71.5, ifrs: null },
    },
    n: '564', priceIn: 3.0, priceOut: 15.0, cost: 0.017257, tokTask: 1752, speed: 44.5,
    calib: [{x:0.05,y:70.0,n:1}, {x:0.15,y:20.0,n:2}, {x:0.25,y:10.5,n:10}, {x:0.35,y:20.4,n:14}, {x:0.45,y:32.8,n:28}, {x:0.55,y:47.7,n:63}, {x:0.65,y:53.6,n:86}, {x:0.75,y:63.0,n:150}, {x:0.85,y:80.1,n:137}, {x:0.95,y:95.9,n:73}],
  },

  // ── 14. gpt-5-mini ───────────────────────────────────
  {
    name: 'gpt-5-mini', org: 'OpenAI', color: '#15803d',
    overall: 59.0, tax: 51.0, financial: 68.9, management: 82.7,
    interpLaw: 62.7, calculation: 29.7, journal: 64.4,
    multiChoice: 83.7, openText: 45.7, singleChoice: 65.9, journalEntry: 68.0,
    austrianTax: 50.7, mixedAcc: 80.6, ugb: 76.2, ifrs: 76.2,
    eduProf: 52.3, eduMaster: 85.7, eduVoc: 50.9,
    byEdu: {
      prof:   { overall: 52.3, tax: 50.6, financial: 63.3, management: 57.4, interpLaw: 54.2, calculation: 32.4, journal: 68.6, multiChoice: 77.6, openText: 46.1, singleChoice: 61.5, journalEntry: 76.2, austrianTax: 50.6, mixedAcc: 57.4, ugb: null, ifrs: 63.3 },
      master: { overall: 85.7, tax: 70.1, financial: 84.9, management: 92.8, interpLaw: 85.7, calculation: null, journal: null, multiChoice: 87.1, openText: 100.0, singleChoice: 70.0, journalEntry: null, austrianTax: 67.4, mixedAcc: 87.4, ugb: 85.3, ifrs: 99.0 },
      voc:    { overall: 50.9, tax: 21.0, financial: 52.6, management: null, interpLaw: 77.5, calculation: 23.5, journal: 63.2, multiChoice: 75.0, openText: 40.5, singleChoice: 75.0, journalEntry: 65.0, austrianTax: 47.7, mixedAcc: null, ugb: 61.5, ifrs: null },
    },
    n: '564', priceIn: 0.25, priceOut: 2.0, cost: 0.003275, tokTask: 2103, speed: 79.3,
    calib: [{x:0.05,y:11.2,n:4}, {x:0.15,y:13.2,n:15}, {x:0.25,y:32.0,n:27}, {x:0.35,y:33.7,n:26}, {x:0.45,y:43.9,n:25}, {x:0.55,y:41.7,n:46}, {x:0.65,y:49.8,n:78}, {x:0.75,y:49.6,n:81}, {x:0.85,y:69.0,n:129}, {x:0.95,y:86.3,n:133}],
  },

  // ── 15. Kimi-K2.6 ───────────────────────────────────
  {
    name: 'Kimi-K2.6', org: 'Moonshot AI', color: '#7e22ce',
    overall: 56.6, tax: 44.8, financial: 72.8, management: 85.3,
    interpLaw: 58.6, calculation: 36.6, journal: 63.1,
    multiChoice: 86.1, openText: 38.7, singleChoice: 75.0, journalEntry: 66.3,
    austrianTax: 45.1, mixedAcc: 85.2, ugb: 72.9, ifrs: 83.6,
    eduProf: 48.3, eduMaster: 87.4, eduVoc: 50.6,
    byEdu: {
      prof:   { overall: 48.3, tax: 43.6, financial: 76.4, management: 71.4, interpLaw: 47.9, calculation: 39.9, journal: 85.0, multiChoice: 82.5, openText: 38.3, singleChoice: 73.1, journalEntry: 81.2, austrianTax: 43.6, mixedAcc: 71.4, ugb: null, ifrs: 76.4 },
      master: { overall: 87.4, tax: 81.9, financial: 86.5, management: 90.9, interpLaw: 87.4, calculation: null, journal: null, multiChoice: 88.0, openText: 95.0, singleChoice: 80.0, journalEntry: null, austrianTax: 80.3, mixedAcc: 89.2, ugb: 79.5, ifrs: 96.3 },
      voc:    { overall: 50.6, tax: 28.3, financial: 51.9, management: null, interpLaw: 80.0, calculation: 29.1, journal: 57.0, multiChoice: 100.0, openText: 40.7, singleChoice: 75.0, journalEntry: 60.9, austrianTax: 47.1, mixedAcc: null, ugb: 62.3, ifrs: null },
    },
    n: '564', priceIn: 0.95, priceOut: 4, cost: 0.054203, tokTask: 14052, speed: 41.7,
    calib: [{x:0.05,y:70.0,n:1}, {x:0.45,y:0.0,n:1}, {x:0.55,y:23.3,n:3}, {x:0.65,y:13.9,n:7}, {x:0.75,y:20.2,n:20}, {x:0.85,y:36.6,n:241}, {x:0.95,y:77.1,n:291}],
  },

  // ── 16. Mistral-Large-3 ───────────────────────────────────
  {
    name: 'Mistral-Large-3', org: 'Mistral AI', color: '#c2410c',
    overall: 52.0, tax: 42.3, financial: 62.4, management: 85.5,
    interpLaw: 56.8, calculation: 24.7, journal: 39.4,
    multiChoice: 86.2, openText: 33.3, singleChoice: 70.5, journalEntry: 36.1,
    austrianTax: 42.4, mixedAcc: 86.4, ugb: 70.4, ifrs: 62.6,
    eduProf: 42.3, eduMaster: 89.2, eduVoc: 42.9,
    byEdu: {
      prof:   { overall: 42.3, tax: 41.3, financial: 41.9, management: 66.9, interpLaw: 44.8, calculation: 24.5, journal: 27.1, multiChoice: 80.6, openText: 32.9, singleChoice: 61.5, journalEntry: 25.0, austrianTax: 41.3, mixedAcc: 66.9, ugb: null, ifrs: 41.9 },
      master: { overall: 89.2, tax: 79.2, financial: 89.0, management: 93.0, interpLaw: 89.2, calculation: null, journal: null, multiChoice: 89.1, openText: 90.0, singleChoice: 90.0, journalEntry: null, austrianTax: 77.3, mixedAcc: 92.1, ugb: 84.8, ifrs: 99.0 },
      voc:    { overall: 42.9, tax: 6.7, financial: 44.9, management: null, interpLaw: 80.0, calculation: 25.2, journal: 42.9, multiChoice: 100.0, openText: 35.0, singleChoice: 75.0, journalEntry: 40.2, austrianTax: 41.6, mixedAcc: null, ugb: 47.1, ifrs: null },
    },
    n: '564', priceIn: 0.5, priceOut: 1.5, cost: 0.001485, tokTask: 1391, speed: 48.2,
    calib: [{x:0.05,y:70.0,n:1}, {x:0.15,y:25.0,n:1}, {x:0.35,y:10.0,n:1}, {x:0.65,y:85.0,n:1}, {x:0.75,y:31.8,n:4}, {x:0.85,y:36.5,n:51}, {x:0.95,y:53.8,n:505}],
  },

  // ── 17. grok-4-fast-reasoning ───────────────────────────────────
  {
    name: 'grok-4-fast-reasoning', org: 'xAI', color: '#0f766e',
    overall: 51.3, tax: 40.1, financial: 64.3, management: 84.5,
    interpLaw: 52.5, calculation: 37.3, journal: 57.1,
    multiChoice: 83.0, openText: 32.0, singleChoice: 68.2, journalEntry: 62.2,
    austrianTax: 40.4, mixedAcc: 79.7, ugb: 62.9, ifrs: 76.3,
    eduProf: 43.2, eduMaster: 80.0, eduVoc: 47.5,
    byEdu: {
      prof:   { overall: 43.2, tax: 39.2, financial: 64.4, management: 67.7, interpLaw: 42.1, calculation: 45.5, journal: 55.7, multiChoice: 83.5, openText: 31.4, singleChoice: 73.1, journalEntry: 57.5, austrianTax: 39.2, mixedAcc: 67.7, ugb: null, ifrs: 64.4 },
      master: { overall: 80.0, tax: 68.7, financial: 76.3, management: 91.2, interpLaw: 80.0, calculation: null, journal: null, multiChoice: 82.8, openText: 90.0, singleChoice: 50.0, journalEntry: null, austrianTax: 65.9, mixedAcc: 83.2, ugb: 63.4, ifrs: 97.3 },
      voc:    { overall: 47.5, tax: 27.7, financial: 48.6, management: null, interpLaw: 74.5, calculation: 22.7, journal: 57.5, multiChoice: 75.0, openText: 35.6, singleChoice: 75.0, journalEntry: 63.9, austrianTax: 43.0, mixedAcc: null, ugb: 62.2, ifrs: null },
    },
    n: '552/564', priceIn: 0.2, priceOut: 0.5, cost: 0.001259, tokTask: 2809, speed: 171.7,
    note: '12 tasks not completed for this model. Scored on 552/564 tasks.',
    calib: [{x:0.25,y:35.0,n:2}, {x:0.55,y:10.0,n:2}, {x:0.65,y:3.3,n:6}, {x:0.75,y:17.7,n:18}, {x:0.85,y:32.0,n:218}, {x:0.95,y:68.4,n:306}],
  },

  // ── 18. gpt-4o ───────────────────────────────────
  {
    name: 'gpt-4o', org: 'OpenAI', color: '#16a34a',
    overall: 47.3, tax: 38.4, financial: 56.2, management: 79.8,
    interpLaw: 53.3, calculation: 13.7, journal: 34.4,
    multiChoice: 82.2, openText: 28.6, singleChoice: 63.6, journalEntry: 32.8,
    austrianTax: 38.1, mixedAcc: 80.8, ugb: 71.9, ifrs: 52.8,
    eduProf: 36.4, eduMaster: 89.3, eduVoc: 36.1,
    byEdu: {
      prof:   { overall: 36.4, tax: 37.2, financial: 25.9, management: 49.7, interpLaw: 39.9, calculation: 14.3, journal: 20.0, multiChoice: 67.5, openText: 29.0, singleChoice: 53.8, journalEntry: 10.0, austrianTax: 37.2, mixedAcc: 49.7, ugb: null, ifrs: 25.9 },
      master: { overall: 89.3, tax: 79.9, financial: 89.7, management: 91.8, interpLaw: 89.3, calculation: null, journal: null, multiChoice: 90.1, openText: 100.0, singleChoice: 80.0, journalEntry: null, austrianTax: 78.0, mixedAcc: 89.9, ugb: 90.1, ifrs: 100.0 },
      voc:    { overall: 36.1, tax: 6.7, financial: 37.7, management: null, interpLaw: 80.0, calculation: 12.3, journal: 38.5, multiChoice: 100.0, openText: 24.1, singleChoice: 75.0, journalEntry: 41.1, austrianTax: 34.1, mixedAcc: null, ugb: 42.5, ifrs: null },
    },
    n: '564', priceIn: 2.5, priceOut: 10.0, cost: 0.003352, tokTask: 734, speed: 134.2,
    calib: [{x:0.05,y:2.6,n:79}, {x:0.15,y:0.0,n:4}, {x:0.25,y:8.0,n:5}, {x:0.35,y:10.0,n:5}, {x:0.45,y:8.8,n:4}, {x:0.55,y:26.0,n:5}, {x:0.65,y:20.0,n:1}, {x:0.75,y:52.0,n:2}, {x:0.85,y:57.4,n:260}, {x:0.95,y:56.0,n:199}],
  },

  // ── 19. DeepSeek-V3.2 ───────────────────────────────────
  {
    name: 'DeepSeek-V3.2', org: 'DeepSeek', color: '#4338ca',
    overall: 45.9, tax: 36.2, financial: 57.8, management: 74.1,
    interpLaw: 50.1, calculation: 22.2, journal: 32.3,
    multiChoice: 79.1, openText: 28.1, singleChoice: 65.9, journalEntry: 25.2,
    austrianTax: 35.8, mixedAcc: 76.6, ugb: 53.5, ifrs: 69.6,
    eduProf: 37.5, eduMaster: 81.2, eduVoc: 31.1,
    byEdu: {
      prof:   { overall: 37.5, tax: 35.3, financial: 54.8, management: 37.0, interpLaw: 38.7, calculation: 26.8, journal: 30.7, multiChoice: 77.0, openText: 28.3, singleChoice: 57.7, journalEntry: 25.0, austrianTax: 35.3, mixedAcc: 37.0, ugb: null, ifrs: 54.8 },
      master: { overall: 81.2, tax: 66.0, financial: 79.9, management: 89.0, interpLaw: 81.2, calculation: null, journal: null, multiChoice: 80.2, openText: 95.0, singleChoice: 90.0, journalEntry: null, austrianTax: 65.9, mixedAcc: 88.1, ugb: 69.3, ifrs: 95.7 },
      voc:    { overall: 31.1, tax: 21.0, financial: 31.6, management: null, interpLaw: 67.0, calculation: 12.0, journal: 32.7, multiChoice: 75.0, openText: 24.6, singleChoice: 62.5, journalEntry: 25.3, austrianTax: 32.0, mixedAcc: null, ugb: 27.9, ifrs: null },
    },
    n: '564', priceIn: 0.28, priceOut: 0.42, cost: 0.000329, tokTask: 981, speed: 35.7,
    calib: [{x:0.05,y:30.0,n:2}, {x:0.15,y:6.0,n:5}, {x:0.25,y:0.0,n:1}, {x:0.35,y:5.0,n:4}, {x:0.45,y:5.0,n:4}, {x:0.55,y:3.3,n:6}, {x:0.65,y:12.5,n:13}, {x:0.75,y:24.6,n:55}, {x:0.85,y:45.1,n:395}, {x:0.95,y:81.2,n:79}],
  },

  // ── 20. mercury-2 ───────────────────────────────────
  {
    name: 'mercury-2', org: 'Inception Labs', color: '#7c3aed',
    overall: 43.8, tax: 32.9, financial: 56.8, management: 77.2,
    interpLaw: 47.8, calculation: 20.3, journal: 34.3,
    multiChoice: 78.2, openText: 23.5, singleChoice: 70.5, journalEntry: 37.5,
    austrianTax: 33.1, mixedAcc: 77.9, ugb: 62.8, ifrs: 60.9,
    eduProf: 33.2, eduMaster: 82.4, eduVoc: 37.9,
    byEdu: {
      prof:   { overall: 33.2, tax: 31.8, financial: 39.2, management: 47.1, interpLaw: 34.9, calculation: 21.9, journal: 13.6, multiChoice: 70.5, openText: 22.9, singleChoice: 65.4, journalEntry: 13.8, austrianTax: 31.8, mixedAcc: 47.1, ugb: null, ifrs: 39.2 },
      master: { overall: 82.4, tax: 66.0, financial: 81.8, management: 89.2, interpLaw: 82.4, calculation: null, journal: null, multiChoice: 82.4, openText: 100.0, singleChoice: 80.0, journalEntry: null, austrianTax: 62.9, mixedAcc: 86.9, ugb: 73.0, ifrs: 99.0 },
      voc:    { overall: 37.9, tax: 21.0, financial: 38.9, management: null, interpLaw: 77.0, calculation: 16.7, journal: 40.1, multiChoice: 75.0, openText: 26.1, singleChoice: 75.0, journalEntry: 46.1, austrianTax: 35.4, mixedAcc: null, ugb: 46.3, ifrs: null },
    },
    n: '564', priceIn: 0.25, priceOut: 0.75, cost: 0.000942, tokTask: 1599, speed: 1023.0,
    calib: [{x:0.15,y:20.0,n:2}, {x:0.25,y:10.0,n:2}, {x:0.35,y:0.0,n:4}, {x:0.45,y:12.9,n:7}, {x:0.55,y:3.3,n:3}, {x:0.65,y:5.8,n:12}, {x:0.75,y:13.8,n:6}, {x:0.85,y:33.0,n:33}, {x:0.95,y:47.0,n:495}],
  },

];
