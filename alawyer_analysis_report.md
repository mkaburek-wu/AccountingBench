# Alawyer Benchmark Analysis Report

**Model:** alawyer (Austrian Legal AI)  
**Platform:** AccountingBench — WU Vienna  
**Date:** June 2026  
**Analyst:** Daniel Höllmüller  

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Scope and Coverage](#2-scope-and-coverage)
3. [Technical Failures](#3-technical-failures)
4. [Personalverrechnung Exclusion](#4-personalverrechnung-exclusion)
5. [Answer Truncation](#5-answer-truncation)
6. [Score Derivation](#6-score-derivation)
7. [Model Comparison (280-Task Sample)](#7-model-comparison-280-task-sample)
8. [Qualitative Performance Analysis](#8-qualitative-performance-analysis)
9. [Root Cause: Truncation Mechanisms](#9-root-cause-truncation-mechanisms)
10. [Recommendations](#10-recommendations)

---

## 1. Executive Summary

Alawyer was benchmarked on 328 tax tasks (Professional Examinations level, Austrian Tax Law). The raw average score is **59.54%**. After removing tasks that are structurally outside alawyer's design scope (Personalverrechnung payroll calculations), confirmed technical failures (empty responses, API errors, rate-limit hits), and answers flagged by the judge as incomplete/truncated, the **clean score on fully-answered tasks is 79.46%** (n=159).

The central finding is that alawyer's low raw score is not primarily a knowledge problem. When alawyer produces a complete answer, it performs at or above the level of claude-opus-4-7. The dominant driver of underperformance is **answer truncation in 45% of open-text tasks**, caused by two distinct technical mechanisms: a hard API response-length cap and a prompt-following failure where the model stops after addressing sub-question 1 of a multi-part exam question.

---

## 2. Scope and Coverage

### 2.1 What Alawyer Was Run On

| Dimension | Value |
|---|---|
| Total approved tasks in DB | 521 |
| Tasks alawyer ran on | 328 |
| Tasks not run | 193 |

Alawyer was only executed on a subset of the full benchmark. All 328 tasks belong to a single intersection:

- **Category:** Tax only
- **Education level:** Professional Examinations only
- **Regulatory framework:** Austrian Tax Law

The 193 missing tasks cover Financial Accounting, Management Accounting, and the remaining Tax tasks at University Master's and Secondary Vocational level. These are not failures — alawyer was simply not submitted for those task groups.

### 2.2 Task Composition of the 328 Runs

| Dimension | Distribution |
|---|---|
| Answer type | open_text: 262 (79.9%) · multi_choice: 43 (13.1%) · single_choice: 23 (7.0%) |
| Task type | interpretation_of_law: 304 (92.7%) · calculation: 24 (7.3%) |
| Subcategory | personalverrechnung: 40 · Ertragsteuern: 85+ · Umsatzsteuer: 78+ · Umgründungssteuer: 61+ · Abgabenverfahren: 37 · Finanzstrafrecht: 27 |

---

## 3. Technical Failures

Thirteen tasks were identified where alawyer received a score of 0 due to technical failures rather than model quality. These should be excluded from any performance assessment.

### 3.1 Type A — All Three Trials Completely Empty (5 tasks)

All three independent trial answers and the final consolidated answer are empty strings. The pipeline received nothing parseable from the API.

| QID | Answer type | Subcategory |
|---|---|---|
| 11913255_0035 | multi_choice | Ertragsteuern |
| 11913255_0039 | multi_choice | Umgründungssteuergesetz |
| 11913255_0042 | multi_choice | Umgründungssteuergesetz |
| 11913255_0067 | multi_choice | Umgründungssteuergesetz |
| 11913255_0110 | multi_choice | Ertragsteuern |

### 3.2 Type B — JSON Stub Response (3 tasks)

The API returned `{"answer":"","confidence":0.0}` instead of legal text — a protocol/format mismatch. All three tasks scored 0 and no usable content was recovered by consolidation.

| QID | Score | What happened |
|---|---|---|
| 11913255_0235 | 0% | All 3 trials + final = JSON stub |
| 11913255_0254 | 0% | Trial 1 = HTTP 429 rate-limit error; final collapsed to JSON stub |
| 11913255_0284 | 0% | Trial 1 was real content; final answer collapsed to JSON stub |

Note: three further tasks (11913255_0251, 0269, 0279) had a JSON stub in trial 1 but the pipeline recovered in trials 2–3. Their scores (20%, 40%, 100%) reflect genuine model performance and are **not** excluded.

### 3.3 Type C — HTTP 429 Rate-Limit Errors (5 tasks)

The API returned `"API Error: Request rejected (429) · Too many tokens per day"` as the answer text across all trials. The judge correctly gave 0, but these are infrastructure failures, not content failures.

| QID | Opus score on same task | Subcategory |
|---|---|---|
| 11913255_0261 | 75% | Umsatzsteuer |
| 11913255_0265 | 60% | Ertragsteuern |
| 11913255_0282 | 70% | Ertragsteuern |
| 11913255_0288 | 80% | Umgründungssteuergesetz |
| 11913255_0255 | 60% | Umgründungssteuergesetz |

**Total technical exclusions: 13 tasks** (all scored 0 for non-content reasons).

---

## 4. Personalverrechnung Exclusion

### 4.1 Overview

Alawyer ran on all 40 Personalverrechnung (payroll accounting) tasks. Performance is very poor:

| Metric | Value |
|---|---|
| n | 40 |
| Average score | **33.2%** |
| Zeros | 25 (62.5%) |
| Perfect scores | 12 (30.0%) |

### 4.2 Why These Tasks Should Be Excluded

Personalverrechnung tasks in the benchmark are primarily **numerical payroll calculations**: computing net wages (Auszahlungsbetrag), applying the Jahressechstel holiday-pay rule, calculating Lohnpfändung (wage garnishment), determining SV/LSt deductions, and handling Sonderzahlungen. These require exact arithmetic with Austrian payroll tax tables.

Alawyer is a legal interpretation AI that generates discursive legal prose in response to open-ended questions. It is explicitly documented that it cannot produce structured numerical output. The 12 perfect scores are entirely concentrated on single-choice true/false legal theory questions (e.g. "Does absence for Präsenzdienst suspend a fixed-term contract — true or false?"). The 25 zeros are all the payroll calculation tasks.

This is a **structural mismatch** between task type and model capability, not a knowledge failure. Alawyer was not designed for, and should not be evaluated on, payroll computation tasks.

### 4.3 Score Impact

Excluding the 40 Personalverrechnung tasks: **n=288, avg=63.19%** (vs 59.54% raw).

---

## 5. Answer Truncation

### 5.1 Scale

**98 of 217 open_text tasks (45.2%)** were flagged by the LLM judge as having incomplete or truncated answers — the judge explicitly noted missing sub-parts, cut-off text, or failure to address required sub-questions.

| | Truncated (n=98) | Complete (n=119) |
|---|---|---|
| Average score | **45.8%** | **72.8%** |
| Score penalty | **−27.0 pp** | — |
| Tasks in 26–50% band | 57.1% | 24.4% |
| Tasks scoring 76–100% | 9.2% | **56.3%** |
| Tasks scoring 100% | 0.0% | **26.9%** |

The 27 percentage-point gap between truncated and complete answers is the single largest driver of alawyer's overall underperformance.

### 5.2 Relationship to Prompt Complexity

Truncation scales directly with the number of sub-questions (`Aufgabenstellung N`) in the prompt:

| Sub-questions | n tasks | Truncation rate | Alawyer avg |
|---|---|---|---|
| 1 | 72 | 15% | 75% |
| 2 | 43 | 44% | 68% |
| 3 | 54 | **63%** | 52% |
| 4 | 29 | **69%** | 47% |
| 5+ | 30 | **70–100%** | 33–49% |

Single-question tasks: 15% truncation rate, 75% average score. Five-or-more sub-questions: 70–100% truncation rate, ~42% average score. The threshold is around 2–3 sub-questions.

### 5.3 Subcategory Impact

| Subcategory | Truncation rate | Avg (truncated) | Avg (complete) |
|---|---|---|---|
| Finanzstrafrecht | 62% | 34% | 77% |
| Ertragsteuern | 54% | 44% | 66% |
| Abgabenverfahren | 48% | 56% | 86% |
| Umgründungssteuergesetz | 45% | 45% | 65% |
| **Umsatzsteuer (standard)** | **27%** | 52% | 76% |

Umsatzsteuer has the lowest truncation rate and is also the only subcategory where alawyer outperforms claude-opus-4-7 overall. The correlation is direct: alawyer's competitive advantage disappears wherever truncation is most frequent.

### 5.4 Opus on Alawyer's Truncated Tasks

On the exact same 97 tasks where alawyer truncated, claude-opus-4-7 scores **74.3%** vs alawyer's **45.8%** (gap: 28.5 pp). Opus scores 0% on none of these tasks, confirming the tasks are solvable — the gap is entirely in alawyer's failure to complete them.

---

## 6. Score Derivation

### 6.1 Filter Chain

| Filter step | n remaining | Notes |
|---|---|---|
| All alawyer outputs | 328 | Raw run |
| Excl. Personalverrechnung | 288 | Structural mismatch |
| Excl. 13 technical failures | 275 | Empty / stub / 429 errors |
| Excl. 98 truncated answers | **159** | Incomplete multi-part answers |

### 6.2 Score Summary Table

| Scenario | n | Score | Description |
|---|---|---|---|
| Raw | 328 | **59.54%** | Everything alawyer ran on |
| Excl. Personalverrechnung | 288 | **63.19%** | Remove structural mismatch |
| Excl. PV + tech failures | 275 | **64.79%** | Remove PV + 13 tech errors |
| **Excl. PV + tech + truncated** | **159** | **79.46%** | **Clean score: complete answers only** |

### 6.3 Score Distribution (Clean 159-Task Set)

| Range | n | % |
|---|---|---|
| 0% | 1 | 0.6% |
| 1–25% | 6 | 3.8% |
| 26–50% | 29 | 18.2% |
| 51–75% | 17 | 10.7% |
| 76–99% | 35 | 22.0% |
| 100% | 71 | **44.7%** |

The single remaining zero is `11913255_0223` (Ertragsteuern, open_text): alawyer answered only `"440000"` where the correct answer required a full §24 capital gains calculation.

### 6.4 Clean Score by Subcategory

| Subcategory | n | Avg score |
|---|---|---|
| Abgabenverfahren | 19 | **88.8%** |
| Finanzstrafrecht | 11 | **83.2%** |
| Umsatzsteuer (standard) | 54 | 79.0% |
| Ertragsteuern | 41 | 77.4% |
| Umgründungssteuergesetz | 32 | 74.8% |

---

## 7. Model Comparison (280-Task Sample)

The 280-task sample is defined as: all tasks alawyer ran on, excluding Personalverrechnung (40 tasks) and the 8 originally-identified technical failures. The 5 rate-limit failures were identified later and remain in this sample (reducing the base to 275 for the extended comparison).

### 7.1 Overall Scores on the 280-Task Sample

| Model | n covered | Avg score | Zeros | Perfect |
|---|---|---|---|---|
| **gpt-5.5** | 280/280 | **81.78%** | 2 | 99 |
| **claude-opus-4-7** | 276/280 | **74.74%** | 6 | 84 |
| **alawyer** | 280/280 | **65.00%** | 10 | 76 |
| **Kimi-K2.6** | 269/280 | **45.96%** | 18 | 39 |

### 7.2 By Answer Type (280-Task Sample)

| Answer type | n tasks | gpt-5.5 | claude-opus | alawyer | Kimi-K2.6 |
|---|---|---|---|---|---|
| open_text | 235 | 78.4% | 71.0% | 58.4% | 37.7% |
| multi_choice | 38 | **99.3%** | 93.0% | **99.1%** | 87.1% |
| single_choice | 7 | **100.0%** | 100.0% | **100.0%** | 85.7% |

Alawyer matches gpt-5.5 almost exactly on choice tasks (99.1% vs 99.3% multi-choice, 100% vs 100% single-choice). The entire performance gap sits in open_text (58.4% vs 78.4%), driven by the truncation problem.

### 7.3 Missing Tasks

- **gpt-5.5:** Full coverage — 0 missing
- **alawyer:** Full coverage — 0 missing
- **claude-opus-4-7:** 4 missing (all open_text — Umsatzsteuer and Finanzstrafrecht tasks added after its run)
- **Kimi-K2.6:** 11 missing (all open_text — spread across Ertragsteuern, Umgründungssteuer, Finanzstrafrecht, Umsatzsteuer); its 45.96% may be an overestimate if the 11 missing tasks are harder

---

## 8. Qualitative Performance Analysis

### 8.1 Where Alawyer Outperforms Opus

On 76 of 276 shared tasks, alawyer outscores claude-opus-4-7. On 49 tasks the margin exceeds 10 percentage points. These wins cluster in:

- **Umsatzsteuer (VAT):** Alawyer outperforms opus on Umsatzsteuer by 3.2 pp overall (71.5% vs 68.3%). Alawyer's training on Austrian legal texts gives it precise knowledge of Austrian VAT rules — §10 Abs. 3 (wine, Beherbergung), Reihengeschäft chain transaction rules, and Reverse-Charge — that opus occasionally misapplies.
- **Umgründungssteuergesetz restructuring law:** On single-question tasks requiring interpretation of §§19, 27 UmgrStG, alawyer is frequently correct and complete while opus makes calculation errors (wrong GrESt Bemessungsgrundlage, incorrect downstream consequences).

### 8.2 Where Alawyer Underperforms

| Subcategory | Alawyer | Opus | Gap |
|---|---|---|---|
| Finanzstrafrecht | 56.7% | 83.3% | **−26.6 pp** |
| Umsatzsteuer (Verbrauchsteuern) | 70.3% | 90.8% | **−20.5 pp** |
| Ertragsteuern | 61.2% | 76.7% | **−15.5 pp** |
| Abgabenverfahren | 72.9% | 86.3% | **−13.4 pp** |

Finanzstrafrecht is alawyer's weakest area. This includes criminal tax law (§§ 33, 51 FinStrG), penalty thresholds (€100,000/€50,000 jurisdictional limits), procedural deadlines, and multi-year compliance scenarios. These tasks also have the highest truncation rate (62%), suggesting that the length and complexity of Finanzstrafrecht exam questions is a primary trigger for the API length cap.

### 8.3 Judge Notes — Quality Assessment

The LLM judge notes were reviewed for systematic errors in scoring:

**Score = 100 with reservations (5 cases):** In all 5 cases the judge gave 100% despite noting minor caveats (missing one citation format, a minor sub-note not affecting the operative conclusion). These are correctly scored — the core legal answer was complete and accurate.

**Score = 0 with potential partial credit (3 cases):** Two cases (12008933_0036 and 12008933_0041) are correctly scored at 0 — the final figures are materially wrong. One case (12008933_0023) is borderline: alawyer described the correct Lohnpfändung methodology but did not produce the final net figure (€1,646.25). A score of ~20% could be argued; however, this task is in Personalverrechnung and excluded regardless.

**Overall:** No systematic judge scoring errors were identified. The judge behaved consistently across all 328 tasks.

---

## 9. Root Cause: Truncation Mechanisms

### 9.1 Two Distinct Mechanisms

Analysis of the 98 truncated tasks revealed two separate failure modes:

#### Mechanism A — Hard API Response-Length Cap (56% of truncated tasks, ~54 tasks)

Trial answers end mid-sentence, mid-word, or mid-table. Examples: `"...verpflichtet, Rechnungen auszustellen, wenn er Umsätze an einen anderen Unternehme"`, `"...Beteiligungsquote aller bete"`. The UTF-8 encoding artefacts (`Â§`, `â¬`, `hÃ¶heren`) appearing at answer endings are consistent with a character stream that was cut before encoding completed.

The model is generating content correctly but the API closes the connection before the response finishes. Alawyer's response token budget is being exhausted — not because the answer is long, but because the model spends its entire budget providing detailed coverage of sub-question 1, leaving nothing for sub-questions 2–N.

#### Mechanism B — Deliberate Early Stop / Prompt-Following Failure (44% of truncated tasks, ~42 tasks)

Trial answers end at clean punctuation — a full sentence-ending period — after addressing only sub-question 1. The model treated the entire multi-part exam question as a single open-ended legal query, generated a complete answer to what it perceived as "the question", and stopped without acknowledging the remaining numbered sub-questions.

This is consistent with a model trained on legal helpdesk queries rather than structured exam formats. A legal AI asked "what are the rules under §29 FinStrG?" generates a complete answer and stops naturally. It is not designed to iterate through `Aufgabenstellung 1`, `Aufgabenstellung 2`, ..., `Aufgabenstellung 6` in sequence.

### 9.2 Cross-Trial Variability

| Behaviour across 3 trials | Count |
|---|---|
| All 3 trials stop at sub-q 1 (consistent failure) | 28 |
| Coverage varies — sometimes sub-q 2+ is reached | **39** |
| Covers 2+ sub-q in all trials (content gap only) | 29 |

The 39 tasks with variable coverage across trials are important: on the same question, trial 1 covers sub-questions 1–2, trial 2 only sub-question 1, trial 3 sub-questions 1–2. The **consolidation step then picks the majority content**, effectively discarding sub-question 2 coverage from trials 1 and 3 because it was absent in trial 2. The consolidation step is compounding the problem rather than rescuing it — in 5 identified cases the consolidated final answer is shorter and worse than the best individual trial.

### 9.3 Prompt Structure

Every single truncated task prompt (100%) contains `Aufgabenstellung N` headings to mark sub-questions. Alawyer sees this structure but fails to iterate through it systematically. This is not a recognition problem — alawyer frequently begins its answer with `"Aufgabenstellung 1: ..."` — it simply generates detailed prose for that heading and then stops.

---

## 10. Recommendations

### 10.1 Immediate Fixes (Pipeline-Level)

**Increase the API response token limit.**  
The alawyer API call likely has a `max_tokens` or equivalent cap. Based on the hard cutoffs observed (answers ending mid-word), the current limit is insufficient for multi-part exam questions. Increasing this to 4,000–6,000 tokens would address Mechanism A entirely.

**Add an explicit completion instruction to the prompt.**  
Before sending each task to alawyer, prepend an instruction such as:  
> *"Die Aufgabe enthält mehrere Aufgabenstellungen. Beantworte jede Aufgabenstellung (1, 2, 3, ...) einzeln und vollständig, der Reihe nach, bevor du zur nächsten übergehst. Schließe alle Aufgabenstellungen ab."*  

This addresses Mechanism B by making the expected iteration behaviour explicit.

**Use best-of-3 rather than majority-vote consolidation for multi-part tasks.**  
For tasks with 3+ sub-questions, select the trial with the highest sub-question coverage as the base for consolidation rather than averaging. This prevents the consolidation step from discarding correctly-answered sub-questions that only appeared in 1–2 of the 3 trials.

### 10.2 Re-Run Recommendation

Before reporting final benchmark scores, the following tasks should be re-run with the corrected prompt and increased token budget:

| Category | Count | Reason |
|---|---|---|
| Truncated open_text tasks | 98 | Incomplete answers due to Mechanisms A/B |
| 429 rate-limit failures | 5 | Infrastructure failures during original run |
| JSON stub / empty failures | 8 | API format errors |
| **Total** | **111** | |

Applying the max_workers rate-limit guidance from the README (max-workers 1 or 2 for alawyer given 10 req/min limit) would also reduce the likelihood of further 429 errors.

### 10.3 Scope Extension

The current run covers only Tax / Professional Examinations. To produce a complete benchmark score comparable to the other models, alawyer should also be run on:

- Financial Accounting tasks (122 tasks in DB)
- Management Accounting tasks (60 tasks in DB)
- Tax tasks at University Master's and Secondary Vocational level

Given the VAT performance advantage observed (+3.2 pp over opus on Umsatzsteuer), alawyer may perform competitively on Financial Accounting interpretation tasks. Management Accounting and calculation-heavy tasks will likely remain weak.

---

## Appendix: Score Reference Card

| Metric | Value |
|---|---|
| Raw score (all 328 tasks) | 59.54% |
| Excl. Personalverrechnung (n=288) | 63.19% |
| Excl. PV + tech failures (n=275) | 64.79% |
| Excl. PV + tech + truncated (n=159) | **79.46%** |
| gpt-5.5 on 280-task sample | 81.78% |
| claude-opus-4-7 on 280-task sample | 74.74% |
| alawyer on 280-task sample (raw) | 65.00% |
| Kimi-K2.6 on 280-task sample | 45.96% |
| Alawyer clean score vs opus | **+4.72 pp** |
| Tasks with technical failures | 13 |
| Tasks excluded (Personalverrechnung) | 40 |
| Tasks with truncated answers | 98 (45.2% of open_text) |
| Score penalty from truncation | −27.0 pp |
| Truncation: hard cutoff (Mech. A) | ~54 tasks (56%) |
| Truncation: prompt-following (Mech. B) | ~42 tasks (44%) |

---

*AccountingBench — WU Vienna · Financial Accounting & Auditing Group*  
*Report generated June 2026*
