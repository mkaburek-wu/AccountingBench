# Palazzo Albicocca — Case-Study Error Analysis

**Case:** Palazzo Albicocca (2026) — hotel CVP / relevant-costing / capital-budgeting teaching case
**Platform:** AccountingBench — WU Vienna
**Task group:** `20260907_0001`–`20260907_0006` (Management Accounting, Master level, `mixed_accounting_framework`)
**Models evaluated:** claude-opus-5, claude-sonnet-5, claude-fable-5, gpt-5.6-luna, gpt-5.6-sol, gpt-5.6-terra
**Run:** `run_20260907_113747` · N_TRIALS = 3 · JUDGE_MODEL = gpt-5-mini · `v3_types` / `v3`
**Date:** 2026-09-08
**Analyst:** Daniel Höllmüller

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Scope and Setup](#2-scope-and-setup)
3. [Score Overview](#3-score-overview)
4. [The Recurring Mistakes](#4-the-recurring-mistakes)
   - [4.1 Electricity — the cost-behaviour trap](#41-electricity--the-cost-behaviour-trap)
   - [4.2 Blended vs. per-category contribution margin (Q3)](#42-blended-vs-per-category-contribution-margin-q3)
   - [4.3 The €3.72 vs €3.80 linen rate (every quantitative part)](#43-the-372-vs-380-linen-rate-every-quantitative-part)
   - [4.4 Literal 153-day season vs. the 147-day / 45-weekday model solution](#44-literal-153-day-season-vs-the-147-day--45-weekday-model-solution)
   - [4.5 Off-season cleaning staff (Q4) — omitted or tripled](#45-off-season-cleaning-staff-q4--omitted-or-tripled)
   - [4.6 Missed pool cross-reference costs (Q4/Q5)](#46-missed-pool-cross-reference-costs-q4q5)
   - [4.7 Recommendation divergence and framing sensitivity (Q5/Q6)](#47-recommendation-divergence-and-framing-sensitivity-q5q6)
5. [Gold-Key Quality Issues](#5-gold-key-quality-issues)
6. [Judge Scoring Inconsistency](#6-judge-scoring-inconsistency)
7. [Per-Model Notes](#7-per-model-notes)
8. [Recommendations](#8-recommendations)
9. [Appendix: Reference Card](#9-appendix-reference-card)

---

## 1. Executive Summary

Six frontier models were run on the Palazzo Albicocca case, both as five separate sub-questions (`_0001`–`_0005`) and as one combined five-part task (`_0006`). Mean final scores by sub-question:

| Q1 (break-even) | Q2 (price cut) | Q3 (off-season CM) | Q4 (step-fixed costs) | Q5 (recommendation) | Q6 (all-in-one) |
|---|---|---|---|---|---|
| **95.8** | **80.3** | **45.8** | **29.2** | **80.5** | **85.0** |

The case is not a knowledge problem. Every model set up the CVP framework correctly, identified linen as the variable cost, reconstructed the tariff grid, and reconciled its model to Exhibit 1 within 0.5 %. The score collapse on **Q3 and Q4** comes from a small number of shared reasoning failures plus two genuine defects in the model solution (`Lösungsskizze`) against which the answers are graded.

**The five findings that explain almost all of the lost points:**

1. **Electricity cost-behaviour.** The case says electricity "is a function of the number of rooms *available* to the public." On Q3, `gpt-5.6-terra` and `gpt-5.6-luna` allocated it over *occupied* room-days and subtracted it from the unit contribution margin (answer €19.63 instead of €46.62). On Q4/Q5, **all six models** costed the April/October electricity at ≈ €29,600 (= €74,320 × 61/153) — the economically defensible reading — while the model solution reports **€346**. This single gap flips the Q5 recommendation.
2. **Blended vs. split contribution margin (Q3).** `claude-fable-5` and `gpt-5.6-sol` reported one blended CM (€46.6) instead of the two figures the key wants (€54.50 / €49.50 ocean vs. partial-ocean). The question is phrased in the singular, so this is partly a key-wording issue — but it cost `fable` 85 points on Q3.
3. **The €3.72 linen rate.** Every model divided €19,562 by a *recomputed* ≈ 5,265 occupied room-nights and got €3.7155. The key divides by *guests* first (€19,562.40 / 9,781.2 = exactly €2.00/guest → €3.80/room). A ~2 % difference, individually tolerated, but it appears in every quantitative answer.
4. **Off-season cleaning staff (Q4).** The Claude models excluded cleaning labour as "occupancy-variable" (omitting ≈ €16,800); the GPT models kept the full 8-person crew plus 40 % fringe (≈ €47,040, ~3× the key's €16,800). The case gives no explicit off-season staffing rule.
5. **Judge noise.** On Q2, `gpt-5.6-luna` and `gpt-5.6-sol` submit the *identical* final number (€75,223.11) by the *identical* method and score **40 vs. 90**. On Q5, `claude-opus-5` and `gpt-5.6-terra` reach the *same* conclusion by the *same* reasoning and score **98 vs. 20**. Between-model differences on Q2/Q3/Q5 are inflated by single-pass judge variance.

Findings 1, 3 and 4 are as much about the case and its key as about the models. Findings 2 and 5 are fixable at the rubric / judging layer.

---

## 2. Scope and Setup

### 2.1 The six tasks

| QID | Sub-question | Skill tested | Mean score |
|---|---|---|---|
| `20260907_0001` | Break-even rooms/night vs. actual 2025 | Multi-product CVP / break-even | 95.8 |
| `20260907_0002` | Revised PBT after a €15 weekday rate cut (Jul/Aug), 70 %→80 % | Contribution-margin, price–volume trade-off | 80.3 |
| `20260907_0003` | Incremental CM per occupied room/day, April & October | Relevant costing, variable vs. step-fixed | 45.8 |
| `20260907_0004` | Step-fixed (non-room) annual costs per decision alternative | Cost classification, alternative structuring | 29.2 |
| `20260907_0005` | Recommendation + pool as a multi-year investment | NPV / capital budgeting, decision synthesis | 80.5 |
| `20260907_0006` | All five parts in one prompt | Combined | 85.0 |

All six are `open_text` / `calculation`, `numeric_tolerance` empty (judge-scored against a prose + table gold answer and an explicit `grading_criteria` block). Each model ran 3 trials; a consolidation step produced the final answer; the judge scored once.

### 2.2 What the case is engineered to do

The case is a classic "separate the relevant from the irrelevant" exercise. It deliberately plants:

- **One variable cost** (linen) buried in an Exhibit-1 line called "Linen Service".
- **A capacity cost dressed as a volume cost** — electricity, described as "a function of the number of rooms *available* to the public" (not occupied).
- **Committed costs that Mr. Rossi wants to 'reduce'** — depreciation, mortgage interest, 12-month salaries — which are irrelevant to every incremental decision.
- **Cross-referenced cost items** — the pool "halves the private sunbathing area" (60 → 30 loungers) and, two sentences earlier, the hotel "has reserved 60 beach loungers … at €35 per month". The reader must connect them to get the €5,250 replacement cost.

Most of the model errors are the case working as designed; a few are the key over-reaching.

---

## 3. Score Overview

Final score (%) per model × question:

| Model | Q1 | Q2 | Q3 | Q4 | Q5 | Q6 | Mean |
|---|---|---|---|---|---|---|---|
| **claude-opus-5** | 95 | 95 | **80** | 40 | **98** | 92 | **83.3** |
| **claude-sonnet-5** | 95 | 92 | **95** | **20** | 85 | 88 | 79.2 |
| **gpt-5.6-sol** | 95 | 90 | **20** | 45 | 95 | 90 | 72.5 |
| **claude-fable-5** | 95 | 70 | **10** | 30 | 95 | 85 | 64.2 |
| **gpt-5.6-luna** | 100 | **40** | 40 | 20 | 90 | 80 | 61.7 |
| **gpt-5.6-terra** | 95 | 95 | 30 | 20 | **20** | 75 | 55.8 |
| **Mean** | 95.8 | 80.3 | 45.8 | 29.2 | 80.5 | 85.0 | |

Observations:

- **Q1 is solved** by everyone. All six converge on the same answer — break-even ≈ 32 rooms/night (≈ 4,907 room-nights, ≈ 53.5 %), actual 2025 ≈ 34.4 rooms/night (5,265 room-nights, 57.3 %) — and each reconciles to the reported €54,820 PBT exactly.
- **Q4 is the floor** (mean 29). No model scored above 45. The failure is shared and structural.
- **Q3 has the widest spread** (10–95) and it is driven by *which* mistake a model made, not by how wrong it was.
- **Q6 (combined) scores are compressed upward** (75–92) relative to the standalone spread — the combined-format judge is not applying the per-part criteria as harshly (see §6).

---

## 4. The Recurring Mistakes

### 4.1 Electricity — the cost-behaviour trap

**This is the single largest score driver in the whole task group.** It shows up in two different forms.

#### Form A — electricity pulled into the unit contribution margin (Q3)

`gpt-5.6-terra` and `gpt-5.6-luna` computed:

```
electricity per available room-day = €74,320 / (60 × 153) = €8.096
April/Oct electricity            = 60 × 61 × €8.096      = €29,631
÷ expected occupied room-days (1,098 at 30 %)            = €26.99 per occupied room-day
CM = €50.33 revenue − €3.72 linen − €26.99 electricity   = €19.63   ✗  (gold: €46.62)
```

`terra` even stated both interpretations, then led with the wrong one as its FINAL answer. `luna` did the same and also folded the €28,400 of period-fixed opening costs into a per-room number.

**Why they did it.** The case sentence "electricity expense is a function of the number of rooms available to the public" contains the word "function of … rooms". The models pattern-matched "function of rooms" → "per-room variable cost" and then divided the total by an *occupancy* base. The distinction the case is testing — **available** rooms (a capacity / step-fixed driver, fixed once you decide to open) vs. **occupied** rooms (a volume driver) — was collapsed. Once a capacity cost is divided by an occupancy count, it looks exactly like a variable unit cost, and it swamps the €46 margin.

`claude-opus-5`, `claude-sonnet-5`, `claude-fable-5` and `gpt-5.6-sol` classified it correctly on Q3 (step-fixed, excluded from the unit CM) and scored 80 / 95 / (10, for other reasons) / 20 respectively.

#### Form B — the magnitude of April/October electricity (Q4, Q5)

Here **all six models agree** and **all six disagree with the key**:

| | April/Oct electricity |
|---|---|
| All six models | **≈ €29,600** (= €74,320 × 61 ⁄ 153, i.e. 61 more days of a cost that buys 153 days of availability) |
| `Lösungsskizze` | **€346.48** |

The key's €346 comes from an idiosyncratic chain: `€74,320 / 5,148 rooms sold = €14.44` → `/ 5 months = €2.89` → `× 60 rooms = €173.24 / month` → `× 2 months`. This mixes "per room *sold* over the whole season" with "per month" and "× 60 available rooms" in a way that does not hold together dimensionally, and it produces an implausible €2.88 per room per month to heat / air-condition a 60-room seaside hotel. **The models' method is the one the case text prescribes.** They are nonetheless graded against €346, which is why Q4 scores 20–45 and why the Q5 recommendation flips (§4.7).

---

### 4.2 Blended vs. per-category contribution margin (Q3)

`claude-fable-5` and `gpt-5.6-sol` computed the off-season revenue as a single blended figure:

```
double avg = (50 × €50 + 10 × €55) / 60 = €50.833
single avg = €50.833 − €5              = €45.833
weighted (90/10)                       = €50.33  → CM ≈ €46.6
```

The key wants the two categories kept apart: **ocean view €54.50**, **partial-ocean view €49.50** (then linen €3.80). Numerically the blend is not *wrong* — `€50.33 = (50 × €49.50 + 10 × €54.50)/60` — and the prompt asks for "the incremental contribution margin per occupied room/day" in the singular. But `grading_criteria` item (2)/(4) rewards showing both category figures, and `fable` additionally (a) buried the answer in an over-elaborate linen sub-derivation and (b) had its consolidated final answer **truncated** mid-calculation → score **10**. `sol` gave a clean single blend → score **20**.

**Why.** Models optimise for "the number the question asks for" and discard the intermediate structure that the rubric grades. `claude-sonnet-5` also blended the two categories in Q3 but showed the per-category derivation on the way, and scored **95**.

---

### 4.3 The €3.72 vs €3.80 linen rate (every quantitative part)

Every model, on every quantitative sub-question, derived the variable linen cost as:

```
occupied room-nights 2025 ≈ 5,265        (recomputed from the occupancy grid)
linen units per room = 0.1×1 + 0.9×2 = 1.9
cost per unit = €19,562 / (5,265 × 1.9) = €1.9555
linen per occupied room-night = 1.9 × €1.9555 = €3.7155
```

The key instead divides by **guests**:

```
guests 2025 = 514.8 singles×1 + 4,633.2 doubles×2 = 9,781.2
linen per guest = €19,562.40 / 9,781.2 = exactly €2.00
linen per room  = €2.00 × (0.1×1 + 0.9×2) = exactly €3.80
```

The case is engineered so that linen is a clean **€2.00 per guest / €3.80 per room** *when you use the case designer's guest count and 5,148 rooms sold*. The models rebuilt the occupied-room-night count themselves from a literal 153-day season (§4.4), landed on ≈ 5,265, and so got €3.7155.

**Impact:** individually ~2 %, and the judge tolerated it everywhere. But it is the **most pervasive single deviation** — it is in Q1, Q2, Q3, and the Q4 cost base — and the judge repeatedly *names* it in the evaluation notes ("abweichender variabler Kostensatz 3,71 vs 3,80"), which drags borderline scores down.

---

### 4.4 Literal 153-day season vs. the 147-day / 45-weekday model solution

The models use the **literal calendar**: May 1 – Sep 30 = 153 nights, 60 × 153 = 9,180 available room-nights, and (for 2025) 18 / 13 / 13 weekend nights per period → 44 weekday nights in Jul/Aug.

The `Lösungsskizze` uses a **simplification it flags explicitly**: "9 weeks Jul/Aug + 6 + 6 = 21 weeks × 7 = 147 nights", 8,820 available room-nights, and 9 × 5 = **45** weekday nights in Jul/Aug.

Consequences:

| | Models | Gold |
|---|---|---|
| Q1 break-even occupancy | 53.4–53.5 % | 54.40 % |
| Q1 actual 2025 occupancy | 57.3 % | 58.37 % |
| Q2 Jul/Aug weekday nights | 44 | 45 |
| Q2 ΔContribution margin | ≈ €20,404 | €20,844 |

On Q1 the judge treated the models' version as within tolerance (95–100) — and it *is* internally consistent (it reconciles to €54,820 exactly). But it compounds §4.3 and feeds the Q2 gap. Note that **44 is the correct 2025 count**; the €440 Q2 difference is the models being more literal than the key, not less accurate.

---

### 4.5 Off-season cleaning staff (Q4) — omitted or tripled

The key assigns **€16,800** of incremental cleaning cost to every "open April/October" alternative, derived by a capacity-ratio scaling: `40 % × 60 = 24 rooms` at `7.5 rooms per cleaner` → `3.2 → round up to 4 cleaners` → `4 × €2,100/cleaner-month × 2 months = €16,800` (no fringe).

The models split into two camps, **neither matching**:

| Camp | Models | Treatment | Result |
|---|---|---|---|
| Exclude | `fable`, `opus` (headline), `sonnet`, `luna` | Cleaning is occupancy-variable → not a "non-room" cost → leave it out | Omit ≈ €16,800; judge: *"Reinigungspersonal fehlt"* |
| Retain full crew | `sol`, `terra` | All 8 cleaners are step-fixed for 2 extra months + 40 % payroll fringe | €33,600 + €13,440 = **€47,040** (~3× the key) |

**Why.** The case gives **no explicit rule** for off-season cleaning headcount. "Exclude as variable" and "keep the whole crew" are both defensible defaults. The key's answer — *scale the crew to expected off-season room demand via the existing rooms-per-cleaner ratio and round up* — is a modelling choice that is never signalled in the case text. This item is genuinely under-determined.

---

### 4.6 Missed pool cross-reference costs (Q4/Q5)

The full annual pool cost in the key is **€64,290**:

| Component | € | Missed by |
|---|---|---|
| Depreciation (120,000 / 10) | 12,000 | — |
| Lifeguard (2,800 × 7) | 19,600 | — |
| **Lifeguard payroll fringe (40 %)** | **7,840** | `luna`, `sonnet` (headline), `fable` (sensitivity only) |
| Extra insurance & taxes | 5,600 | — |
| Heating (full) | 6,000 | `sol`/`opus`/`fable` used €3,000 for summer-only |
| Maintenance | 8,000 | — |
| **30 replacement city loungers (30 × 35 × 5)** | **5,250** | `luna`, `terra` (argued away), `fable` (sensitivity only) |

`gpt-5.6-sol` was the only model to reproduce **€64,290 exactly**. `opus` and `sonnet` reached €56,450 (fringe in sensitivity, loungers included); `terra` €59,040 (fringe yes, loungers no); `luna` €51,200 (neither).

**Why.** Both missed items require *connecting two separate statements*:

- **Loungers:** "the pool would … reduce its private sunbathing area to half its size" (60 → 30) **+** "the hotel has reserved 60 beach loungers … €35 per … month" → to hold capacity you rent 30 more → €5,250/yr. `terra` explicitly reasoned "no such rental is specified as mandatory" and dropped it.
- **Lifeguard fringe:** the case states "payroll taxes and other fringe benefits are about 40 % of the payroll" as a general rule; models that read the lifeguard line ("€2,800 per month for a lifeguard") in isolation did not apply the 40 % to it.

Models that read each cost line literally missed both; models that treated the case as an integrated system caught them.

---

### 4.7 Recommendation divergence and framing sensitivity (Q5/Q6)

The `Lösungsskizze` comparison table implies the most attractive option is **open April/October + advertising + pool** (highest extra profit contribution €4,679.92; pool NPV at 6 % ≈ +€2,766).

In the **standalone Q5**, four of six models recommended the **opposite — keep the status quo, build nothing**:

- `claude-opus-5` (score **98**): "April/October is *structurally*, not marginally, unprofitable … break-even occupancy 47.8 % vs. a max plausible 40 % … Rossi's premise is a cost-allocation illusion." Pool NPV @ 8 % = −€25,147, IRR ≈ 3.1 %.
- `gpt-5.6-terra` (score **20**): same conclusion, same electricity reasoning, thinner structure, and it double-counted the demand lever by carrying the €12,000 advertising into the 40 %-pool scenario.
- `claude-sonnet-5` (85), `gpt-5.6-sol` (95): "reject the extension; evaluate the pool separately; approve a summer-only pool only below a ~10.7 % hurdle rate."
- `claude-fable-5` (95), `gpt-5.6-luna` (90): recommended **build pool + open** (aligned with the key) — but via a large positive NPV driven by their own occupancy assumptions.

**Why the models say "reject":** it is the direct, logical consequence of the €29,600 electricity figure from §4.1B. With ≈ €46,000–93,000 of genuinely new annual cash cost to open two near-empty shoulder months, off-season room revenue of €49.50–54.50 cannot cover it, and break-even occupancy (48–55 %) sits above the 10–40 % the case allows. The `grading_criteria` for Q5 explicitly permits a well-argued deviating recommendation, which is why `opus` scored 98 — but `terra` was graded as "contradicts the model solution" for the same conclusion (§6).

**Framing sensitivity:** in the **combined Q6**, `opus` and `fable` *both* recommended **build pool + open** — the key-aligned answer — because the one-shot format pushed them to also quantify the pool's *summer* occupancy uplift (≈ +€53,800 CM), which offsets the shoulder-month loss. The same model gives opposite recommendations depending on whether the five parts arrive together or separately.

---

## 5. Gold-Key Quality Issues

Three of the five headline findings are at least partly defects in the material, not the models:

| # | Issue | Evidence | Effect on scores |
|---|---|---|---|
| G1 | **Q4 electricity = €346** is almost certainly wrong. The case says electricity depends on *rooms available*; 61 extra days of availability against a €74,320 / 153-day base is ≈ €29,600. The key's per-room-sold ÷ 5 ÷ ×60 chain is dimensionally inconsistent and implies €2.88/room/month. | `Lösungsskizze` Table 8; all six models independently derive ≈ €29,600 | Depresses Q4 to a 20–45 ceiling; flips the Q5 recommendation for 4/6 models |
| G2 | **No off-season cleaning rule.** The key's "scale to 40 % demand at 7.5 rooms/cleaner, round to 4" is unstated in the case. Both "exclude as variable" and "retain full crew" are defensible and the criteria penalise both. | §4.5 | −10 to −25 on Q4 for every model |
| G3 | **Inference-only cost items** (€5,250 loungers, €7,840 lifeguard fringe) are treated as mandatory by the criteria but require chaining separated sentences. | §4.6 | −5 to −15 on Q4/Q5 for `fable`, `luna`, `terra` |
| G4 | **Linen derivation not shown.** The case yields a clean €2.00/guest only via the designer's guest count; the published gold jumps straight to €3.80 with no visible working, so any model that recomputes from occupancy lands at €3.72 and is flagged. | §4.3 | Chronic −2 to −5 across Q1–Q4; repeatedly cited in judge notes |
| G5 | **Q3 wording vs. key.** Prompt asks for "*the* incremental contribution margin per occupied room/day" (singular); key expects two per-category figures. | §4.2 | `fable` 10, `sol` 20 |

---

## 6. Judge Scoring Inconsistency

The single-pass judge (`gpt-5-mini`) produced large score swings on materially equivalent answers:

| Case | Model A | Model B | Same? | Scores |
|---|---|---|---|---|
| **Q2** | `gpt-5.6-sol` — €75,223.11 via blended-rate method | `gpt-5.6-luna` — €75,223.11, line-for-line the same method | Identical final number and derivation | **90 vs. 40** |
| **Q2** | `claude-opus-5` — ΔCM €20,403, PBT €75,223 | `claude-fable-5` — ΔCM €20,404, PBT €75,224, same rate assumptions | Equivalent | **95 vs. 70** |
| **Q5** | `claude-opus-5` — reject all, keep status quo, NPV @ 8 % = −€25k | `gpt-5.6-terra` — reject all, keep status quo, negative NPV | Same conclusion, same electricity logic | **98 vs. 20** |
| **Q3** | `claude-sonnet-5` — blended €46.6, per-category shown | `gpt-5.6-sol` — blended €46.6 | Both blend the two room types | **95 vs. 20** |

The judge alternates between two implicit criteria — *"matches the gold numbers"* and *"internally sound and well-argued"* — and which one dominates appears close to random across otherwise-similar answers. This inflates the apparent between-model spread on Q2, Q3 and Q5. It does **not** affect Q1 (everyone converges) or Q4 (everyone is genuinely below the key).

The **combined Q6** is judged more leniently than the sum of its parts: `fable` scores 85 on Q6 but 10 on the standalone Q3; `terra` scores 75 on Q6 but 20 on the standalone Q5. The per-part `grading_criteria` in Q6 instructs the judge to score each sub-question separately before aggregating — that does not appear to be happening.

---

## 7. Per-Model Notes

| Model | Mean | Read |
|---|---|---|
| **claude-opus-5** | 83.3 | Strongest and most consistent. Full method + explicit relevant-costing + sensitivity analysis on every part. Only Q4 (40) hurt it, and that is the G1/G2 key issue. Its Q5 (98) is the benchmark answer for the task — it names Rossi's "off-season loss" as a cost-allocation illusion. |
| **claude-sonnet-5** | 79.2 | Best on Q3 (95). Weakest on Q4 (20) — excluded cleaning labour *and* mis-scaled the pool costs. Low self-reported confidence throughout (0.35–0.55) despite generally correct work. |
| **gpt-5.6-sol** | 72.5 | Only model to nail the €64,290 pool cost exactly. Undone on Q3 (20) by the single-blend presentation and on Q4 (45) by the €47,040 cleaning figure. |
| **claude-fable-5** | 64.2 | Correct methods, but the consolidation step produces **truncated / over-elaborated** final answers (Q3 = 10, Q2 = 70). Same underlying "answer" as `opus` on Q2/Q5, scored far lower. |
| **gpt-5.6-luna** | 61.7 | Two distinct failures: pulled electricity into the unit CM on Q3 (40), and got judge-dinged on Q2 (40) for a numerically correct answer identical to `sol`'s. |
| **gpt-5.6-terra** | 55.8 | Q5 = 20 is mostly judge noise (§6), but `terra` genuinely double-counted the demand lever (carried the €12,000 ads into the 40 %-pool scenario) and dropped the €5,250 lounger cost by argument. Q3 (30): led with the wrong (electricity-in-CM) interpretation as its final answer. |

---

## 8. Recommendations

### 8.1 Fix the case / key before re-scoring

1. **Resolve the Q4 electricity figure (G1).** Either correct the model solution to ≈ €29,600 (= €74,320 × extra-days ⁄ 153, consistent with "rooms available"), or add a sentence to the case stating that shoulder-month electricity is minimal and giving the intended basis. Until then, Q4 and Q5 scores against this key are unreliable and the Q5 "reject" answers are arguably *more* correct than the key's implied recommendation.
2. **State the off-season cleaning rule (G2)** in the case ("cleaning is staffed to expected occupancy at roughly 7.5 rooms per cleaner"), or widen `grading_criteria` to accept "excluded as occupancy-variable" and "full crew retained" as valid, with the point only for internal consistency.
3. **Demote the two inference items (G3)** — replacement loungers, lifeguard fringe — from mandatory to bonus in `grading_criteria`, or add them to the case as explicit Exhibit line items.
4. **Publish the linen derivation (G4)** in the gold answer (€2.00/guest → €3.80/room) and widen Q1/Q3 tolerance so that a recomputed €3.71–3.72 is not flagged as a deviation.
5. **Reword Q3 (G5)** to "for each room category, the incremental contribution margin per occupied room/day", or accept a single blended €46.6 as full marks.

### 8.2 Judging

6. **Run the judge ≥ 3× and average** for `open_text` / `calculation` case tasks. The Q2/Q3/Q5 evidence shows single-pass variance of 30–60 points on equivalent answers. (`judge_experiment.py --repeats 3` can quantify this offline first.)
7. **Pin the rubric weighting** — state in `grading_criteria` what share of the score is *method* vs. *matching the gold number* — so the judge stops alternating between the two.
8. **Enforce per-part scoring on Q6.** The combined task should score each sub-question with the same standalone rubric before aggregating; today it is markedly more lenient.

### 8.3 If the task group is kept as-is

9. Treat **Q1** as the only reliable score in the set. **Q3/Q4** are contaminated by G1–G5; **Q2/Q5** are contaminated by judge noise. Report the sub-question scores separately, not a single case average.
10. The genuine, model-side lesson worth keeping: **all six models struggle to distinguish a capacity cost from a volume cost when the case describes it as "a function of rooms".** That is a real and reportable capability gap (§4.1) and it is worth a dedicated, clean single-question probe with an unambiguous key.

---

## 9. Appendix: Reference Card

| Metric | Value |
|---|---|
| Models evaluated | 6 (opus-5, sonnet-5, fable-5, gpt-5.6-luna/sol/terra) |
| Tasks | 6 (`20260907_0001`–`0006`), open_text / calculation, Master, Management Accounting |
| Trials per model per task | 3 · judge once · JUDGE_MODEL = gpt-5-mini |
| Highest mean | claude-opus-5 — 83.3 % |
| Lowest mean | gpt-5.6-terra — 55.8 % |
| Best-scored sub-question | Q1 — mean 95.8 % (all models converge, reconcile to €54,820 PBT) |
| Worst-scored sub-question | Q4 — mean 29.2 % (no model > 45) |
| Widest spread | Q3 — 10 to 95 |
| Dominant error 1 | Electricity: variable-vs-capacity misclassification (Q3) / magnitude vs. key (Q4/Q5, all 6 models) |
| Dominant error 2 | Blended vs. per-category CM (Q3 — `fable` 10, `sol` 20) |
| Dominant error 3 | Linen €3.7155 vs. gold €3.80 (all models, every quantitative part) |
| Dominant error 4 | Off-season cleaning: omitted (Claude) or ~3× overstated (GPT) on Q4 |
| Dominant error 5 | Judge variance: identical Q2 answers scored 40 vs. 90; identical Q5 conclusions scored 20 vs. 98 |
| Key defects identified | 5 (G1 electricity €346; G2 no cleaning rule; G3 inference items mandatory; G4 linen derivation hidden; G5 Q3 singular wording) |
| Gold pool annual cost | €64,290 (only `gpt-5.6-sol` reproduced it exactly) |
| Gold Q5 pool NPV @ 6 % | +€2,766 (key) vs. models' −€15k to −€33k @ 8 % |

---

*AccountingBench — WU Vienna · Financial Accounting & Auditing Group*
*Report generated 2026-09-08*
