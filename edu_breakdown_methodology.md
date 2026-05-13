# AccountingBench — Education-Level Breakdown Calculation

This document explains how the `byEdu` scores in `results.js` were computed from the raw benchmark output Excel files.

---

## Input Files

### `output_old_models.xlsx` — 10 models
Contains: gpt-5.4, gpt-5.2, claude-opus-4-6, claude-sonnet-4-6, gpt-5-mini, Mistral-Large-3, grok-4-fast-reasoning, gpt-4o, DeepSeek-V3.2-2, mercury-2

Two sheets:
- **`Runs`** — one row per model run: `run_id`, `model_name`
- **`Outputs`** — one row per task per model: `question_id`, `final_score_percent`, `education_level`, `category`, `task_type`, `answer_type`, `regulatory_framework`

### `output.xlsx` — 3 new models
Contains: claude-opus-4-7, gpt-5.5, Kimi-K2.6

Sheet `benchmark_outputs`: `task_id` (integer), `final_score_percent` — **no metadata columns**.

---

## Joining New File to Metadata

The old file has `question_id` like `12008933_0001` to `12008933_0521`.
The new file has integer `task_id` from 1 to 521.

We matched by sequential position — `task_id 1` = first unique `question_id` in old file, `task_id 2` = second, etc. This works because both datasets cover the exact same 521 tasks in the same order.

```python
import pandas as pd

# Load old file
df_old = pd.read_excel('output_old_models.xlsx', sheet_name='Outputs')
df_runs = pd.read_excel('output_old_models.xlsx', sheet_name='Runs')
df_old = df_old.merge(df_runs[['run_id','model_name']], on='run_id', how='left')

# Load new file
df_new = pd.read_excel('output.xlsx', sheet_name='benchmark_outputs')

# Build task metadata lookup from old file (sequential task_id)
task_meta = df_old[['question_id','task_type','answer_type','regulatory_framework',
                     'category','education_level']].drop_duplicates('question_id').reset_index(drop=True)
task_meta['task_id'] = task_meta.index + 1

# Join metadata onto new file
df_new = df_new.merge(
    task_meta[['task_id','task_type','answer_type','regulatory_framework','category','education_level']],
    on='task_id', how='left'
)

# Combine both into one dataframe
df_all = pd.concat([df_old, df_new], ignore_index=True)
df_all = df_all.dropna(subset=['education_level'])
```

---

## Score Computation

For each model + education level combination, filter rows and compute `mean(final_score_percent)` per subcategory. `None` is returned when no tasks exist for that combination.

```python
def scores(df, model, edu=None):
    sub = df[df['model_name'] == model]
    if edu:
        sub = sub[sub['education_level'] == edu]
    if len(sub) == 0:
        return None

    def avg(mask):
        s = sub[mask]['final_score_percent']
        return round(s.mean(), 1) if len(s) > 0 else None

    return {
        'overall':      round(sub['final_score_percent'].mean(), 1),
        # Category
        'tax':          avg(sub['category'] == 'tax'),
        'financial':    avg(sub['category'] == 'financial_accounting'),
        'management':   avg(sub['category'] == 'management_accounting'),
        # Task type
        'interpLaw':    avg(sub['task_type'] == 'interpretation_of_law'),
        'calculation':  avg(sub['task_type'] == 'calculation'),
        'journal':      avg(sub['task_type'] == 'journal_entry'),
        # Answer type
        'multiChoice':  avg(sub['answer_type'] == 'multi_choice'),
        'openText':     avg(sub['answer_type'] == 'open_text'),
        'singleChoice': avg(sub['answer_type'] == 'single_choice'),
        'journalEntry': avg(sub['answer_type'] == 'journal_entry'),
        # Regulatory framework
        'austrianTax':  avg(sub['regulatory_framework'] == 'austrian_tax_law'),
        'mixedAcc':     avg(sub['regulatory_framework'] == 'mixed_accounting_framework'),
        'ugb':          avg(sub['regulatory_framework'] == 'UGB'),
        'ifrs':         avg(sub['regulatory_framework'] == 'IFRS'),
    }

# Education level key mapping
EDU_KEYS = {
    'professional_examinations':   'prof',
    'master':                      'master',
    'secondary_vocational_school': 'voc',
}

# Example: compute for all models
models = [
    'gpt-5.4', 'gpt-5.2', 'gpt-5.5', 'claude-opus-4-6', 'claude-sonnet-4-6',
    'claude-opus-4-7', 'gpt-5-mini', 'Mistral-Large-3', 'grok-4-fast-reasoning',
    'gpt-4o', 'DeepSeek-V3.2-2', 'Kimi-K2.6', 'mercury-2'
]

for model in models:
    for edu_label, edu_key in EDU_KEYS.items():
        s = scores(df_all, model, edu_label)
        print(f"{model} / {edu_key}: {s}")
```

---

## Education Level Values in Data

| Raw value in Excel | Key in `results.js` | Label shown on site |
|---|---|---|
| `professional_examinations` | `prof` | Professional Exams |
| `master` | `master` | University Exams |
| `secondary_vocational_school` | `voc` | Secondary Vocational |

---

## Key Finding: IFRS is Exclusively Master-Level

All 25 IFRS tasks are university teaching material (Master level only).
- `ifrs` is `null` for both `prof` and `voc` — no IFRS tasks exist at those levels
- This explains the near-ceiling IFRS scores (~97–100%) across all models
- The holistic matrix filter makes this immediately visible: switching to "Professional Exams" shows `—` for IFRS across all 13 models

---

## Note on claude-opus-4-6 Scoring

The overall score of **63.3%** in `results.js` is computed only over the **465 tasks** that produced a `final_answer` (55 tasks had no parseable answer, scored as 0 but excluded from the average).

The raw average over all 520 rows is 56.6%.

For consistency, the education-level breakdowns should ideally also exclude null-answer rows. This was not applied in the current computation — the `byEdu` values for claude-opus-4-6 include the zero-scored excluded tasks and may be slightly understated.

---

## Dataset Composition by Education Level

| Regulatory Framework | Prof | Master | Vocational |
|---|---|---|---|
| Austrian Tax Law | 86% | 11% | 3% |
| Mixed Accounting | 0% | 85% | 15% |
| UGB (National GAAP) | 0% | 62% | 38% |
| IFRS | **0%** | **100%** | **0%** |
| Mixed Acc. + Tax | 0% | 100% | 0% |

| Category | Prof | Master | Vocational |
|---|---|---|---|
| Tax | 99% | 1% | 0% |
| Financial Accounting | 0% | 57% | 43% |
| Management Accounting | 57% | 43% | 0% |
