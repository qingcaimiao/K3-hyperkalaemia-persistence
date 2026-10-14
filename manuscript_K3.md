# Most episodes of incident hyperkalaemia defined by a single threshold in cardiac intensive care do not persist: definition, short-term stability and prognosis in two databases

Qingcai Miao 3, Jianhong Cen 3, Lu Chen 3, Runzhi Lu 3 and Renjie Zhang 1,2,*

1 Department of Cardiology (Cardiology Unit I), Handan First Hospital, No. 25 Congtai Road, Handan 056000, Hebei, China
2 Handan Key Laboratory of Cardiac Precision Medicine, Handan First Hospital, No. 25 Congtai Road, Handan 056000, Hebei, China
3 Hebei North University, No. 11 Diamond South Road, Zhangjiakou Economic Development Zone, Zhangjiakou 075000, Hebei, China

* Correspondence: zhangrenjie725@sina.com

ORCID iDs: Qingcai Miao, https://orcid.org/0009-0006-1479-6726; Renjie Zhang, https://orcid.org/0009-0009-4026-2068

E-mail addresses: 15511075821@163.com (Q.M.); 1046649694@qq.com (J.C.); 18703137731@163.com (L.C.); 298837507@qq.com (R.L.); zhangrenjie725@sina.com (R.Z.)

---

## Abstract

**Background** Hyperkalaemia in cardiac intensive care is defined by one threshold, although guidelines advise a repeat sample. Whether such an episode persists, and whether persistence is prognostic, is unknown.

**Methods** Among cardiac intensive care admissions with potassium records in the Medical Information Mart for Intensive Care IV (MIMIC-IV, 23,429) and the eICU Collaborative Research Database (eICU-CRD, 41,917), the 20,322 and 28,805 with a baseline potassium below 5.5 mmol/L and a measurement after 24 hours were classified by the next 24 hours after a first value ≥5.5 mmol/L as transient, intermittent, sustained or unclassified. We quantified within-patient variability, bounded the contribution of analytical error, and related each state to in-hospital death after a 72-hour landmark.

**Results** Episodes occurred in 1,182 (5.82%) and 997 (3.46%) admissions; 86 (0.42%) and 100 (0.35%) were sustained. Analytical error alone predicted 38–83% confirmation, so the reversion reflects genuine fluctuation, not assay error, and recorded treatment did not explain it. Adjusted odds ratios for death were 11.87 (5.59–20.49) and 8.05 (4.16–15.15) for sustained episodes and 1.56 (0.99–2.45) and 2.77 (1.82–3.93) for transient episodes; the persistent state was significant in all sensitivity analyses, whereas the excess for transient episodes was not significant in MIMIC-IV. Only 52.0% and 42.0% were re-measured within six hours.

**Conclusions** Most single-threshold episodes in cardiac intensive care do not persist, and the observed rates exclude an isolated assay error. Excess mortality is carried mainly by the persistent state, so the two should be reported separately.

**Keywords** hyperkalaemia; potassium; cardiac intensive care; outcome definition; measurement variability; MIMIC-IV; eICU

---

## 1. Introduction

Potassium is one of the most frequently measured analytes in intensive care. Hyperkalaemia is associated with arrhythmia and death in cardiac patients [1,2], with mortality among unselected cardiac intensive care patients [3], and with mortality among patients whose elevation is severe enough to require hospitalisation [4]. In practice, an episode is identified by a single laboratory value crossing a threshold (most often 5.5 mmol/L, the lower bound of the mild band in current guidance [5]), and the choice of threshold already changes the measured incidence substantially [6]. Everything that follows from that identification, including estimated incidence, risk-factor associations, trial eligibility and quality metrics, inherits the properties of that threshold.

Clinical guidance has long recognised that a single elevated value may not represent a persistent state. UK Kidney Association guidance directs clinicians to exclude spurious hyperkalaemia and repeat the sample, grades management by *confirmed* potassium, and specifies repeat measurement at 1, 2, 4, 6 and 24 hours after treatment of moderate or severe hyperkalaemia [7]; an emergency-physician consensus likewise recommends repeat measurement after an abnormal result but does not specify intervals [8]. Pre-analytical causes are well described, including haemolysis, prolonged tourniquet time, fist-clenching and pneumatic-tube transport [9–12]. The literature on pseudohyperkalaemia is, however, almost entirely about *laboratory artefacts*, that is, values that do not reflect the patient's true potassium at all.

What is not known is how a threshold-defined episode behaves **as an episode**. Three strands of work come close without addressing it. Studies of potassium variability show that fluctuation is itself prognostically informative in intensive care [13] and in acute kidney injury [14], but they summarise variability over an entire stay rather than asking whether a particular episode persists. Studies of recurrence show that repeated hyperkalaemic episodes are associated with worse cardiovascular outcomes [15], but recurrence is a property of successive episodes rather than of one. And the decision to repeat a sample because haemolysis is suspected has been examined directly [16], but as a laboratory question about a single value rather than as a question about the duration of a clinical state. We therefore set out to define what a threshold-defined episode consists of in cardiac intensive care, to determine how often it persists, and to test whether persistence carries prognostic meaning.

A different possibility has attracted less attention: that the value is analytically correct, but reflects a **short-lived physiological state**. If potassium genuinely fluctuates on the timescale of hours in critically ill patients, then a single threshold crossing will frequently be followed by a value below that threshold, without any error having occurred. The two mechanisms carry different implications. An artefact argues for ignoring the value; a genuinely transient state argues that the episode was real, that it differs prognostically from a persistent episode, and that "incident hyperkalaemia" as currently defined is a composite of states that ought to be reported separately.

We therefore set out to quantify, in two independent databases, (i) how often a threshold-defined episode of incident hyperkalaemia is followed by a value below the threshold, (ii) whether that reversion is attributable to analytical error or to genuine short-term variability, and (iii) whether the states so defined differ in prognosis and in how they are detected in practice. The question addressed here concerns the outcome definition itself, not how well that outcome can be predicted.

---

## 2. Materials and Methods

### 2.1 Data sources and setting

We used two publicly available critical care databases. MIMIC-IV (version 3.1), an electronic health record database from a single tertiary academic medical centre in Boston, USA, served as the primary database [17]; the eICU Collaborative Research Database (eICU-CRD, version 2.0), a multicentre tele-intensive-care database covering hospitals across the United States, served for replication [18]. Both are de-identified; their collection was approved by the institutional review boards of the Beth Israel Deaconess Medical Center and the Massachusetts Institute of Technology (MIMIC-IV) and by the institutional review boards of the participating sites (eICU-CRD), with waiver of informed consent. This report follows the STROBE statement [19].

Cardiac intensive care was defined by the unit of first admission: coronary care or cardiovascular intensive care units in MIMIC-IV (`Coronary Care Unit (CCU)`, `Cardiac Vascular Intensive Care Unit (CVICU)`), and the cardiac, coronary, or cardiothoracic surgical intensive care units in eICU-CRD. Only the first intensive care admission of each hospital admission was retained. Potassium was taken from the hospital laboratory record (MIMIC-IV item 50971, blood chemistry; eICU-CRD laboratory name `potassium`), restricted to values between 1 and 15 mmol/L, and to the window from 24 hours before to 7 days after intensive care admission.

### 2.2 Cohort

The baseline window was the 24 hours centred on intensive care admission (24 hours before to 24 hours after). Admissions entered the analysis cohort if the highest potassium in that window was below 5.5 mmol/L and at least one potassium measurement was recorded after hour 24. Admissions whose potassium was already at or above 5.5 mmol/L in the baseline window were excluded, because a subsequent elevated value would not represent an incident episode.

**Cohort definition and length-of-stay sensitivity.** The cohort requires only a baseline-normal potassium and a measurement after hour 24; it does not require that the intensive care stay itself last beyond 24 hours. The two databases carry laboratory results on different records (in MIMIC-IV on the hospital record, in eICU-CRD against the intensive care stay), so the definition was applied identically in both and its consequence examined directly. Restricting the eICU-CRD cohort to admissions whose intensive care stay exceeded 24 hours gives 23,205 admissions, 913 apparent episodes, 222 confirmed (24.3%) and 93 sustained (10.2%) episodes, against 28,805, 997, 234 (23.5%) and 100 (10.0%) under the primary definition; every result was materially unchanged. In MIMIC-IV the hospital record carries the laboratory result, so both definitions give 20,322 admissions and 1,182 episodes.

### 2.3 Outcome states

For every admission, the first potassium measurement after hour 24 that was at least 5.5 mmol/L was designated the index value. Five mutually exclusive states were then defined from **all** measurements in the 24 hours after the index value:

- **transient**: every subsequent measurement was below 5.5 mmol/L;
- **intermittent**: at least one subsequent measurement reached 5.5 mmol/L, but not all of them did;
- **sustained**: every subsequent measurement was at least 5.5 mmol/L;
- **unclassified**: no measurement followed within 24 hours, so persistence could not be determined.

Defining the states from the whole 24-hour trajectory rather than from the next measurement alone (Figure 1A) avoids calling an episode persistent when the elevation has already resolved, and avoids calling it resolved when the value rises again later in the window. For continuity with the literature and with the analytical-error bounding below we also report the conventional definition, under which an episode is **confirmed** when the *next* measurement is at least 5.5 mmol/L; this counts the intermittent episodes whose next value was still elevated together with all sustained episodes. A first threshold crossing is called an **apparent** episode regardless of which state followed, so that apparent episodes correspond to the outcome as it is conventionally defined: the occurrence of a value above the threshold, irrespective of what follows.

![](figures_k3/FigK3_1_definition.png "6.5")

**Figure 1.** Outcome definition and incidence. (A) A first potassium ≥5.5 mmol/L after hour 24 (an apparent episode) is classified by **all** measurements in the following 24 hours into transient (every value below 5.5 mmol/L), intermittent (some but not all values at least 5.5), sustained (every value at least 5.5) and unclassified (no further measurement) states. (B) Incidence of each state as a percentage of the analysis cohort.

### 2.4 Short-term stability and the state-transition matrix

Within-patient variability was estimated from all pairs of consecutive potassium measurements separated by 24 hours or less, as the standard deviation of the paired difference divided by √2; the coefficient of variation was that value divided by the mean of all potassium measurements in that database, and the 95% reference change value as 1.96 × √2 × the within-patient standard deviation. For each index value we also computed whether it exceeded that patient's own median potassium by more than the reference change value.

A state-transition matrix was constructed from all pairs of consecutive measurements after hour 24 separated by 24 hours or less, cross-tabulating the potassium band of the first measurement against the probability that the next measurement reached 5.5 mmol/L. This matrix uses the **whole cardiac intensive care population, including patients whose baseline potassium was already at or above 5.5 mmol/L**, because it describes the general behaviour of potassium rather than the follow-up of the cohort; restricting it to baseline-normal patients changes the probability of a repeat value ≥5.5 from 32.3% to 29.3% in MIMIC-IV and from 33.9% to 31.4% in eICU-CRD.

### 2.5 Bounding the contribution of analytical error

To separate an assay artefact from genuine fluctuation we computed the confirmation rate that would be expected under competing assumptions about the source of variation, using the reliability formulation for regression to the mean: given an index value, the expected next value is λ·(index value) + (1 − λ)·(population mean), with λ = τ²/(τ² + σ²), where τ² is the between-patient variance of true potassium and σ² the variance of the assumed source of variation; the prediction interval uses σ²(1 + λ). τ² was estimated by the method of moments from the same measurement series: the variance of patient means minus the mean within-patient sampling variance over patients with at least three measurements, the within-patient variance being half the variance of successive differences within 24 hours. For each scenario the expected confirmation rate was then the mean over the observed index values of 1 − Φ[(5.5 − μ_i)/s], where μ_i = λ·k_i + (1 − λ)·m and s = σ·√(1 + λ), with m the population mean potassium. Three analytical-error scenarios were evaluated, corresponding to a laboratory coefficient of variation for potassium of 1.5%, 3.0% and 5.0% (the last being deliberately conservative, since analytical imprecision for potassium is generally below 2% and pre-analytical error is the larger term). The three analytical-error scenarios differ in σ² but share the estimated τ², so the whole bounding exercise is conditional on that estimate; τ² was therefore also varied over a fourfold range to show how much the expected rates depend on it. A fourth scenario used the *observed* within-patient variability, which contains genuine physiological fluctuation as well as error, and therefore gives the confirmation rate that would be expected if a patient's true potassium never changed.

### 2.6 Prognostic association

Death during the hospital admission was related to the state defined above. Because a patient who dies cannot subsequently have a sustained episode, the state would be determined by the outcome if follow-up were unrestricted; classification would then be systematically shifted towards "transient" among those who died. We therefore used a **landmark design**: states were defined from the potassium trajectory between 24 hours and the landmark, and the outcome was in-hospital death *after* the landmark, with the cohort restricted to admissions whose stay (or death) extended beyond it. A 72-hour landmark was pre-specified as the primary analysis because it retains 89.7% of the MIMIC-IV cohort and 80.1% of the eICU-CRD cohort, and a 7-day landmark as a sensitivity analysis. Odds ratios were estimated by logistic regression with the no-event group as reference, adjusted for the index value, age and sex; the unclassified group was excluded because its outcome state is unknown, and missing age was imputed with the cohort median. Unadjusted whole-cohort rates, which are subject to the bias described above, are reported alongside to show its magnitude.

**Sensitivity analyses for the prognostic model.** Four checks were prespecified against the possibility that the gradient reflects the mechanics of follow-up rather than the state itself. First, because the 24-hour classification window may be cut short by the landmark, the state distribution was compared between episodes whose window ended before the landmark and episodes whose window was truncated, and the model was refitted among episodes with an untruncated window only and again in a version that assigned truncated episodes to the unclassified group. Second, because truncation arises from the exposure window starting at a variable time, the whole analysis was repeated with a **fixed exposure window of 24 to 48 hours** for every admission, so that no episode is classified on a longer or shorter window than any other. Third, the model was refitted restricting to episodes whose index value exceeded the patient's own median potassium by more than the reference change value, since a crossing that does not clear that margin may be ordinary fluctuation rather than an event. Fourth, because discharge alive removes a patient from the risk of in-hospital death, discharge was treated formally as a competing event: the cumulative incidence of in-hospital death after the landmark was estimated with the Aalen–Johansen estimator, so that patients discharged alive leave the risk set rather than being counted as event-free survivors, and the model was additionally refitted after excluding patients discharged within 48 hours of the landmark, for whom a subsequent death would be invisible. Because an episode can only be detected where potassium was measured and measurement frequency differed between the states, the model was also refitted within strata of measurement density (at or above the median, and in the top quartile, of the number of potassium measurements after hour 24). A minimum of two repeat measurements was required before a state could be assigned, so that episodes resting on a single further value became unclassified rather than being classified as sustained or transient. Odds ratios were also reported separately for episodes with and without recorded potassium-lowering treatment, and an E-value was computed for each state against the no-episode group, indicating how strong an unmeasured confounder would have to be, on the risk-ratio scale, to explain the association away; odds ratios were converted to risk ratios as RR = OR / (1 − p0 + p0 · OR), with p0 the observed mortality in the no-episode group. In eICU-CRD the confidence intervals for the proportions (incidence, re-measurement and confirmation) were also obtained by resampling hospitals rather than patients, with 1,000 resamples.

### 2.7 Detection in practice

For each apparent episode we recorded the interval to the next potassium measurement and whether that measurement was within 2, 4, 6, 12 or 24 hours, expressing the proportion re-measured within each window as the current compliance with the recommendation to confirm. For a six-hour window the number needed to re-measure was defined as the number of episodes re-measured within six hours divided by the number confirmed within that window, that is, the number of patients who must be re-measured to identify one confirmed episode. Because patients who are not re-measured cannot be classified, we report the classification-specific bounds obtained by assigning all unclassified episodes to transient, and then to sustained.

To address whether potassium-lowering treatment could account for reversion, we sought five categories of treatment: insulin given with glucose, a potassium-binding resin, intravenous calcium, sodium bicarbonate and renal replacement therapy. An episode was classified as treated if any was recorded between the index value and the repeat measurement, or, in a wider definition, from six hours before the index value to the repeat measurement.

### 2.8 Statistical analysis

Analyses were performed in Python 3.13 (pandas, NumPy, scikit-learn, DuckDB). Confidence intervals for proportions used the bootstrap. In eICU-CRD, which pools many hospitals, the confidence intervals for the odds ratios were also re-estimated with the hospital as the resampling unit, because patients within a hospital are not independent. A sensitivity model added three markers of illness severity that could be extracted comparably from both databases: the highest creatinine in the first 24 hours (available for 99.7% and 97.8% of the landmark cohort, with a missing-indicator term), any mechanical ventilation (56.4% and 34.2%) and any vasopressor infusion (49.7% and 18.4%). No imputation of missing potassium values was performed; a measurement that was not taken is not a normal value, and treating it as one would bias the results towards normality. The state definition was repeated at thresholds of 5.0, 6.0 and 6.5 mmol/L, and requiring a minimum of two or of three measurements within the 24-hour window before an episode could be classed as sustained. All analyses were run independently in both databases and are reported side by side. The cohort was derived in the sequence shown in Figure 2.

![](figures_k3/FigK3_2_flow.png "6.5")

**Figure 2.** Derivation of the analysis cohort. Admissions with no potassium in the ±24-hour baseline window and admissions whose baseline potassium was already ≥5.5 mmol/L were excluded, the latter because a subsequent elevated value would not represent an incident episode; admissions with no potassium measurement after hour 24 were excluded because the episode state could not be determined.

---

## 3. Results

### 3.1 Cohort and incidence of the states

Potassium was recorded in 23,429 cardiac intensive care admissions in MIMIC-IV and 41,917 in eICU-CRD (Figure 2). Excluding 98 and 682 admissions with no measurement in the baseline window, 2,128 and 3,626 with a baseline potassium ≥5.5 mmol/L, and 881 and 8,804 with no measurement after hour 24 left 20,322 and 28,805 admissions in the analysis cohort; the median number of measurements per admission was 8 (IQR 6–11) and 6 (IQR 4–9). Patients with an episode were measured more often than those without (median 9–16 versus 8 measurements in MIMIC-IV and 7–15 versus 6 in eICU-CRD, across the four states; Table 1), a point to which we return.

### Table 1. Cohort characteristics by outcome state

| | MIMIC-IV | | | eICU-CRD | | |
|---|---|---|---|---|---|---|
| **State** | **n** | **Age, median (y)** | **Male (%)** | **n** | **Age, median (y)** | **Male (%)** |
| No episode | 19,140 | 70.0 | 63.8 | 27,808 | 66.0 | 58.0 |
| Transient | 757 | 71.0 | 62.5 | 493 | 66.0 | 61.3 |
| Intermittent | 189 | 69.0 | 66.7 | 169 | 63.0 | 65.7 |
| Sustained | 86 | 67.0 | 70.9 | 100 | 66.0 | 69.0 |
| Unclassified (not re-measured) | 150 | 70.5 | 63.3 | 235 | 69.0 | 51.9 |
| **Whole cohort** | **20,322** | **70.0** | **63.8** | **28,805** | **66.0** | **58.1** |

Baseline potassium (highest value in the 24-hour window) was 4.4 mmol/L in MIMIC-IV and 4.3 mmol/L in eICU-CRD among admissions without an episode, and 4.6–4.8 mmol/L in both databases among those with one (medians by state: transient 4.7 and 4.6, intermittent 4.8 and 4.6, sustained 4.8 and 4.8, unclassified 4.7 and 4.7). The median number of potassium measurements per admission was 8 (IQR 6–11) without an episode and 9–16 with one in MIMIC-IV (12, 16, 12 and 9 in the transient, intermittent, sustained and unclassified groups respectively), and 6 (IQR 4–9) versus 7–15 in eICU-CRD (11, 15, 9.5 and 7); ascertainment and outcome are therefore not independent.

A first potassium ≥5.5 mmol/L after hour 24 occurred in 1,182 of 20,322 admissions in MIMIC-IV (5.82%, 95% CI 5.50–6.14) and 997 of 28,805 in eICU-CRD (3.46%, 3.25–3.68) (Table 2, Figure 1B). Of these apparent episodes, **only 224 (19.0%) and 234 (23.5%) were still elevated at the next measurement** (next-value-confirmed), and only 86 (0.42% of the cohort) and 100 (0.35%) were sustained, that is, never fell below the threshold across the following 24 hours. Expressed against the apparent episodes, sustained episodes were 7.3% and 10.0%. Reversion was therefore the rule rather than the exception: among episodes that were followed up (1,032 and 762 with a repeat measurement within 24 hours), the median repeat value was 4.85 mmol/L in MIMIC-IV and 5.10 mmol/L in eICU-CRD, and **73.4% and 64.7% had no further value at or above the threshold at any point in the 24 hours**. The stricter definition does not change the conclusion: classifying by the next measurement alone would call 78.3% and 69.3% of re-measured episodes transient, but 51 (6.3%) and 35 (6.6%) of those rose again within the window, which is why they are reported separately as intermittent.

### Table 2. Definition of outcome states and their incidence

| State | Definition | MIMIC-IV n (%) | eICU-CRD n (%) |
|---|---|---|---|
| Cohort | Baseline potassium <5.5 mmol/L and ≥1 measurement after hour 24 | 20,322 | 28,805 |
| **Apparent** | First potassium ≥5.5 mmol/L after hour 24 | **1,182 (5.82)** | **997 (3.46)** |
| Transient | Every measurement in the next 24 h <5.5 mmol/L | 757 (3.73) | 493 (1.71) |
| Intermittent | ≥1 but not all measurements in the next 24 h ≥5.5 mmol/L | 189 (0.93) | 169 (0.59) |
| **Sustained** | Every measurement in the next 24 h ≥5.5 mmol/L | **86 (0.42)** | **100 (0.35)** |
| Unclassified | No measurement within 24 h | 150 (0.74) | 235 (0.82) |
| Re-measured within 24 h | | 1,032 | 762 |
| Fully reverted / re-measured | | 73.4% | 64.7% |
| Next-value-confirmed (comparison definition, not a separate state) | Next measurement ≥5.5 mmol/L | 224 (19.0% of apparent) | 234 (23.5%) |
| Measurements in the 24-h window, median (IQR): transient / intermittent / sustained | | 2 (1–3) / 3 (2–4) / 2 (1–3) | 2 (1–3) / 4 (3–6) / 1 (1–2) |
| Sustained episodes resting on a single repeat measurement, n (%) | | 40 (46.5) | 69 (69.0) |
| Sustained / apparent | | 7.3% | 10.0% |
| Median repeat value (mmol/L) | | 4.85 | 5.10 |

The four states are mutually exclusive and together account for all apparent episodes (757 + 189 + 86 + 150 = 1,182; 493 + 169 + 100 + 235 = 997). Figures in parentheses are percentages of the whole cohort. The conventional "confirmed" definition counts only the *next* measurement and therefore includes the 138 (MIMIC-IV) and 134 (eICU-CRD) intermittent episodes whose next value was still elevated plus all sustained episodes, while excluding the 51 and 35 intermittent episodes whose next value had already fallen; it is the definition on which the analytical-error bounding of Table 4 is based, and its denominator is the 1,032 and 762 re-measured episodes. The median repeat value is computed among those re-measured episodes; among the episodes that reverted it is 4.60 and 4.70 mmol/L. Restricting the eICU-CRD cohort to admissions whose intensive care stay exceeded 24 h gives 23,205 admissions, 913 apparent episodes, 222 confirmed (24.3%) and 93 sustained (10.2%) episodes, with no material change in any result. In MIMIC-IV both definitions give 20,322 admissions and 1,182 episodes.

### 3.2 Potassium fluctuates substantially over hours, and the fluctuation is reproducible across databases

Consecutive measurements within 24 hours differed by more than would be expected from assay imprecision alone. The within-patient standard deviation was 0.410 mmol/L (coefficient of variation 9.71%) in MIMIC-IV and 0.386 mmol/L (9.40%) in eICU-CRD, and the corresponding 95% reference change values were 1.14 and 1.07 mmol/L (Table 3, Figure 3). These two independently collected datasets agree closely, which is the first evidence that the variability is a property of the patients rather than of either record system.

### Table 3. Within-patient variability and state transitions

| | MIMIC-IV | eICU-CRD |
|---|---|---|
| Consecutive pairs ≤24 h apart | 150,619 | 193,242 |
| Within-patient SD (mmol/L) | 0.410 | 0.386 |
| Within-patient CV (%) | 9.71 | 9.40 |
| 95% reference change value (mmol/L) | 1.14 | 1.07 |
| Index value exceeding own median + RCV (%) | 64.0 | 64.8 |
| Increment from previous value ≤RCV (%) | 46.3 | 51.1 |
| **Transition: next value ≥5.5 mmol/L** | | |
| Current 4.5–4.9 | 1.8% (n=16,685) | 1.9% (n=11,339) |
| Current 5.0–5.4 | 10.0% (n=5,372) | 10.7% (n=3,842) |
| Current 5.5–5.9 | **32.3% (n=1,698)** | **33.9% (n=1,236)** |
| Current ≥6.0 | 39.0% (n=807) | 54.5% (n=688) |

The coefficient of variation is the within-patient standard deviation divided by the mean of all potassium measurements in that database. The two variability percentages in the upper block are computed among the apparent episodes (1,182 in MIMIC-IV and 997 in eICU-CRD) and therefore differ slightly from the corresponding percentages within the 72-hour landmark cohort given in Section 3.6 (63.6% and 65.6%). Transition matrix computed in the whole cardiac intensive care population (including patients with a baseline potassium ≥5.5 mmol/L); restricted to baseline-normal patients the figures for 5.5–5.9 are 29.3% and 31.4% (n = 1,083 and 818).

![](figures_k3/FigK3_3_variability.png "6.5")

**Figure 3.** Within-patient variability and the explanations for reversion. The two left panels show the distribution of the difference between consecutive potassium measurements up to 24 hours apart, in MIMIC-IV and eICU-CRD; the dashed lines mark the 95% reference change value and the inset gives the within-patient standard deviation, its coefficient of variation and the reference change value. The right panel gives the expected confirmation rate under each assumed source of variation (analytical imprecision at a coefficient of variation of 1.5%, 3.0% and 5.0%, and the observed within-patient variability) beside the observed rate; the same quantities are tabulated in Table 4.

Two consequences followed. First, the apparent rise is often small relative to that background: the index value exceeded the patient's own median by more than the reference change value in only 64.0% and 64.8% of episodes, and the increment from the preceding measurement was within the reference change value in 46.3% and 51.1%. Second, the transition matrix shows that an isolated reading carries limited information about the next one (Table 3, Figure 4): a potassium of 5.5–5.9 mmol/L was followed by a value ≥5.5 mmol/L in only 32.3% (MIMIC-IV) and 33.9% (eICU-CRD) of instances, compared with 10.0% and 10.7% for a reading of 5.0–5.4, and 1.8% and 1.9% for 4.5–4.9. The matrix agrees between databases at 5.5–5.9 and diverges only at ≥6.0 (39.0% versus 54.5%), the band in which management is most likely to differ between a single academic centre and a tele-ICU network.

![](figures_k3/FigK3_4_transition.png "6.5")

**Figure 4.** State-transition matrix. Row percentages for the band of the next measurement, according to the band of the current measurement, in the whole cardiac intensive care population of each database. Cell values are rounded to the nearest integer. The right-hand column gives, for each current band, the exact row percentage whose next value is at least 5.5 mmol/L, the collapsed probability quoted in Table 3; because the cells are rounded individually, their sum may differ from it by up to one percentage point.

### 3.3 The reversion is not laboratory error

If a threshold-defined episode were merely an assay artefact, the next measurement should also be elevated, because the errors would be independent. Analytical imprecision for potassium is small, and the expected confirmation rate under a coefficient of variation of 1.5%, 3.0% or even 5.0% would be 78.8%, 60.1% and 37.8% in MIMIC-IV and 82.8%, 67.7% and 46.5% in eICU-CRD (Table 4). The observed confirmation rates of 21.7% and 30.7% lie below all of these, and comfortably below even the most conservative analytical assumption. **A pure measurement artefact is therefore excluded.**

### Table 4. Expected confirmation rate under competing explanations

| Assumed source of variation | SD (mmol/L) | Expected confirmation, MIMIC-IV | Expected confirmation, eICU-CRD |
|---|---|---|---|
| Laboratory analytical error, CV 1.5% | 0.063 / 0.062 | 78.8% | 82.8% |
| Laboratory analytical error, CV 3.0% | 0.127 / 0.123 | 60.1% | 67.7% |
| Laboratory analytical error, CV 5.0% | 0.211 / 0.205 | 37.8% | 46.5% |
| Observed within-patient variability | 0.410 / 0.386 | 14.7% | 19.2% |
| **Observed confirmation** | — | **21.7%** | **30.7%** |

Confirmation was defined as a next measurement ≥5.5 mmol/L. Expected and observed rates are both computed among apparent episodes with a repeat measurement within 24 hours (1,032 in MIMIC-IV and 762 in eICU-CRD); the observed rate is therefore higher than the same count expressed against all apparent episodes, including those never re-measured (19.0% and 23.5%; Table 2). The observed rate lies below every analytical-error scenario and above the scenario in which all variability is attributed to genuine fluctuation.

The observed rates are, by contrast, entirely compatible with genuine fluctuation. If the observed within-patient variability is taken to be noise (that is, if a patient's true potassium is assumed constant and only the state is allowed to vary), the expected confirmation rate is 14.7% and 19.2%, close to but slightly below the observed 21.7% and 30.7%. In other words, the data behave as if potassium truly moves by about 10% on a timescale of hours, and as if a small additional component of the index values reflects a genuinely persistent elevation. Notably, the states were reached by different testing trajectories rather than by obviously different patients: whole-cohort mortality was 11.8% and 17.4% for transient episodes but 51.2% and 53.0% for sustained episodes (see below), whereas the median baseline potassium spanned only 4.4–4.8 mmol/L in MIMIC-IV and 4.3–4.8 mmol/L in eICU-CRD across the states (Table 1).

**Treatment does not account for the reversion.** Potassium-lowering treatment is recorded very differently in the two systems: between the index value and the repeat measurement it was recorded for 375 of 1,032 re-measured *apparent* episodes in MIMIC-IV (36.3%) but for only 31 of 762 in eICU-CRD (4.1%), so the two cannot be pooled. (The corresponding count within the 72-hour landmark cohort used in Section 3.6 is 28 for eICU-CRD; the two figures differ only because the cohorts differ.) Where the comparison is possible it runs against the treatment explanation. In MIMIC-IV the confirmation rate was 27.5% among episodes with recorded treatment and 18.4% among those without (odds ratio 1.60, 95% CI 1.17–2.10); in eICU-CRD it was 29.0% and 30.8% respectively (1.30, 0.72–2.38). Episodes in which treatment was recorded were therefore, if anything, *more* likely to remain above the threshold, and excluding treated episodes makes reversion more prominent rather than less. This is consistent with the treatment being a response to the severity of the episode rather than the cause of its resolution, but the recording is too incomplete in eICU-CRD for that interpretation to be tested there.

### 3.4 Transient, intermittent and persistent episodes carry progressively higher mortality

In the unrestricted whole cohort, in-hospital mortality was 11.8% (MIMIC-IV) and 17.4% (eICU-CRD) for transient episodes, 22.8% and 23.1% for intermittent episodes and 51.2% and 53.0% for sustained episodes, against 4.4% and 5.8% for admissions without an episode (Table 5). These figures are inflated for the persistent states by construction, because a patient who dies cannot later have a value below the threshold; the bias is quantified by the landmark analysis.

### Table 5. In-hospital death by state, before and after landmark restriction

| State | Whole cohort, n | Whole cohort, % | 72-h landmark, n | 72-h landmark, % | Adjusted OR (95% CI) | 7-day landmark, % | Adjusted OR (95% CI) |
|---|---|---|---|---|---|---|---|
| **MIMIC-IV** | | | | | | | |
| No episode | 19,140 | 4.4 | 17,585 | 4.4 | 1 (reference) | 6.2 | 1 (reference) |
| Transient | 757 | 11.8 | 412 | 7.8 | 1.56 (0.99–2.45) | 11.2 | 1.91 (1.29–2.74) |
| Intermittent | 189 | 22.8 | 102 | 18.6 | 4.41 (2.32–7.57) | 16.7 | 2.98 (1.90–4.51) |
| Sustained | 86 | 51.2 | 39 | 41.0 | 11.87 (5.59–20.49) | 20.0 | 3.47 (1.41–6.55) |
| Unclassified | 150 | 32.0 | 89 | 14.6 | excluded | 14.7 | excluded |
| **eICU-CRD** | | | | | | | |
| No episode | 27,808 | 5.8 | 22,602 | 6.4 | 1 (reference) | 7.6 | 1 (reference) |
| Transient | 493 | 17.4 | 245 | 13.1 | 2.77 (1.82–3.93) | 15.1 | 2.75 (1.60–3.52) |
| Intermittent | 169 | 23.1 | 89 | 15.7 | 4.52 (1.85–6.30) | 14.9 | 3.02 (1.27–4.34) |
| Sustained | 100 | 53.0 | 43 | 34.9 | 8.05 (4.16–15.15) | 27.5 | 5.61 (2.31–8.79) |
| Unclassified | 235 | 32.8 | 108 | 15.7 | excluded | 14.2 | excluded |

The five groups are mutually exclusive and account for the whole cohort (MIMIC-IV 19,140 + 757 + 189 + 86 + 150 = 20,322; eICU-CRD 27,808 + 493 + 169 + 100 + 235 = 28,805). Odds ratios are adjusted for index potassium value, age and sex, with the no-episode group as reference; the unclassified group is excluded because its state is unknown, and its mortality (32.0% and 32.8% in the whole cohort) lies between the intermittent and sustained groups. Whole-cohort rates are inflated for the persistent states because a patient who dies cannot subsequently be found below the threshold, and are shown to quantify that bias: for sustained episodes the whole-cohort rate is 51.2% and 53.0% against 41.0% and 34.9% at the 72-hour landmark. At the 7-day landmark the sustained group is small (n = 40 in each database), which is why its odds ratio attenuates. The gradient was monotonic in the adjusted odds ratios in all four database–landmark combinations, and in the crude rates in three of the four (in eICU-CRD at 7 days the intermittent rate, 14.9%, was marginally below the transient rate, 15.1%). The classification window was truncated by the landmark in 32.9% (MIMIC-IV) and 35.5% (eICU-CRD) of episodes at 72 hours, and in 11.7% and 12.2% at 7 days. Within the most populous index-value band, 5.5–5.9 mmol/L, the ordering was preserved at both landmarks (72 h: MIMIC-IV 7.3%, 16.7% and 39.3%; eICU-CRD 13.0%, 18.8% and 44.0%; 7 d: MIMIC-IV 11.7%, 17.0% and 25.0%; eICU-CRD 14.7%, 19.7% and 32.0%).

With a 72-hour landmark (18,227 and 23,087 admissions), mortality was 4.4% and 6.4% without an episode, 7.8% and 13.1% for transient, 18.6% and 15.7% for intermittent and 41.0% and 34.9% for sustained episodes (Table 5). After adjustment for the index value, age and sex, the odds ratios were 1.56 (95% CI 0.99–2.45) and 2.77 (1.82–3.93) for transient, 4.41 (2.32–7.57) and 4.52 (1.85–6.30) for intermittent, and 11.87 (5.59–20.49) and 8.05 (4.16–15.15) for sustained episodes (Figure 5). The gradient was monotonic in the adjusted odds ratios in all four database–landmark combinations. The same ordering was reproduced with the 7-day landmark and within the most populous index-value band, 5.5–5.9 mmol/L (Table 5), indicating that it is not simply a restatement of how high the index value was. Whole-cohort rates fell furthest for the states most determined by the outcome: from 51.2% to 20.0% and from 53.0% to 27.5% for sustained episodes, but only from 11.8% to 11.2% and from 17.4% to 15.1% for transient episodes.

![](figures_k3/FigK3_5_forest.png "6.5")

**Figure 5.** Adjusted odds ratios for in-hospital death after a 72-hour landmark, by outcome state, in both databases. Odds ratios are adjusted for the index potassium value, age and sex, with admissions without an episode as the reference; horizontal lines are 95% bootstrap confidence intervals from patient-level resampling (400 replicates, the same intervals as in Table 5); the hospital-clustered intervals for eICU-CRD, which are wider, are reported in Section 3.6.

Re-estimating the confidence intervals with the hospital as the resampling unit in eICU-CRD left the point estimates unchanged but widened the intervals slightly (72-hour landmark: transient 1.94–3.88, intermittent 2.10–6.27, sustained 3.81–17.82), indicating that treating patients within a hospital as independent slightly understates the uncertainty for the persistent state.

Adding baseline creatinine, mechanical ventilation and vasopressor use to the adjustment set attenuated the odds ratios but preserved the ordering: at the 72-hour landmark they were 1.35 (95% CI 0.88–2.17), 3.32 (1.54–5.79) and 7.69 (3.22–14.24) in MIMIC-IV and 2.12 (1.43–3.01), 3.10 (1.45–4.58) and 7.28 (2.75–15.07) in eICU-CRD. The ordering between states is therefore not merely a restatement of illness severity, although part of its magnitude reflects it.

Because a persistent state can only be recognised from repeated measurements, we repeated the analysis requiring at least two, and then at least three, measurements within the 24-hour window before an episode could be called sustained. This reclassifies much of the sustained group, since in the whole cohort 40 of 86 sustained episodes in MIMIC-IV (46.5%) and 69 of 100 in eICU-CRD (69.0%) rested on a single repeat value. The ordering nevertheless survived at every database and landmark, and the adjusted odds ratio for sustained episodes remained far above that for transient episodes (at the 72-hour landmark: with a minimum of two measurements, 9.62 [3.44–19.50] and 19.28 [5.79–39.32]; with a minimum of three, 8.10 [1.77–16.43] and 13.39 [1.33–28.97]; Table S5).

The unclassified episodes cannot be assigned without an assumption, so we report the extreme case: if every unclassified episode had in fact ended in death **and** were allocated to a state, mortality would be 24.2% and 39.7% at the 72-hour landmark and 22.7% and 36.0% at 7 days if all were allocated to transient, rising to 82.0% and 81.5% (72 hours) and 72.2% and 80.1% (7 days) if all were allocated to sustained. These are bounds constructed to be extreme rather than estimates, and they are reported to show that the ordering survives the worst case; the unclassified group's actual mortality (32.0% and 32.8% in the whole cohort) is intermediate, which is what would be expected if it is a mixture of states.

### 3.5 Detection in practice: most episodes are not confirmed within six hours

Guidance recommends re-measuring potassium after an abnormal result, and specifies intervals of 1, 2, 4, 6 and 24 hours after treatment of moderate or severe hyperkalaemia [7]; an emergency-physician consensus recommends repeat measurement without specifying intervals [8]. In practice, 15.4% (MIMIC-IV) and 20.0% (eICU-CRD) of apparent episodes were re-measured within 2 hours, 35.9% and 32.0% within 4 hours, and **52.0% and 42.0% within 6 hours**; 12.7% and 23.6% were not re-measured within 24 hours at all (Table 6, Figure 6A). A six-hour rule would therefore leave 567 and 578 episodes unconfirmed at that point.

### Table 6. Re-measurement after an apparent episode

| Window | MIMIC-IV re-measured | MIMIC-IV not covered | eICU-CRD re-measured | eICU-CRD not covered |
|---|---|---|---|---|
| 2 h | 15.4% | 1,000 | 20.0% | 798 |
| 4 h | 35.9% | 758 | 32.0% | 678 |
| **6 h** | **52.0%** | 567 | **42.0%** | 578 |
| 12 h | 76.7% | 275 | 60.2% | 397 |
| 24 h | 87.3% | 150 | 76.4% | 235 |
| Next-value-confirmed episodes identified within 6 h | 137 (of 224) | | 151 (of 234) | |
| Repeat measurements per confirmed episode (6 h) | 4.5 | | 2.8 | |

Coverage is the proportion of apparent episodes (1,182 in MIMIC-IV and 997 in eICU-CRD) with at least one further potassium measurement within the window; "not covered" is the number of apparent episodes without one. "Next-value-confirmed episodes identified within 6 h" counts apparent episodes whose first repeat measurement within 6 h was ≥5.5 mmol/L, against the 224 and 234 episodes confirmed by the next measurement in the whole 24-hour window. The number of repeat measurements per confirmed episode at 6 h is the number of episodes re-measured within 6 h (615 and 419) divided by the number confirmed within 6 h (137 and 151), that is, the number of patients who must be re-measured under a six-hour rule in order to identify one confirmed episode.

![](figures_k3/FigK3_6_rule.png "6.5")

**Figure 6.** Detection of episodes in current practice and the yield of a re-measurement rule. (A) Proportion of apparent episodes with at least one further potassium measurement within 2, 4, 6, 12 and 24 hours. (B) Number of repeat measurements required to identify one confirmed episode within each window. MIMIC-IV, blue; eICU-CRD, red.


---

The yield of such a rule is quantifiable. Within a six-hour window, 137 (MIMIC-IV) and 151 (eICU-CRD) episodes were confirmed, meaning that **4.5 and 2.8 repeat measurements were required to identify one confirmed episode** (Figure 6B). The window that captured 61.2% and 64.5% of all confirmed episodes was 6 hours; 12 hours captured 94.2% and 86.3%.

The yield did not improve by restricting the rule to higher values. In eICU-CRD, applying the six-hour rule only to episodes with an index value ≥6.5 mmol/L was the most efficient stratum (2.1 measurements per confirmed episode), but in MIMIC-IV the same stratum was the least efficient (7.2). The two databases also disagree about which stratum is relatively most efficient, and treatment is recorded too differently between them for the mechanism to be identifiable from these data: in MIMIC-IV, where potassium-lowering treatment was recorded for 36.3% of re-measured episodes, recorded treatment was associated with a *higher* rather than a lower confirmation rate (27.5% versus 18.4%), so the divergence cannot be attributed to treatment having already lowered the repeat value. Stratified yield therefore does not transfer between databases, and this particular comparison is exploratory: the strata are small, treatment and measurement timing differ between the systems, and the mechanism could not be identified from the available data.

### 3.6 Robustness of the prognostic gradient

**The persistent state is not simply a product of sparse measurement.** A state is assigned from whatever measurements fall within the 24-hour window, and for the sustained state this was a single further value in 46.5% of episodes in MIMIC-IV and 69.0% in eICU-CRD (Table 2). If sustained episodes were being flagged mainly because a patient too ill to be re-measured was measured once, those episodes should be the more lethal ones. They are not: within sustained episodes, those resting on a single repeat measurement had a *lower* in-hospital mortality than those with two or more (47.5% versus 54.3% in MIMIC-IV; 44.9% versus 71.0% in eICU-CRD), and among transient episodes the two groups were nearly identical (10.5% versus 12.4%; 17.3% versus 17.6%). The number of repeat measurements therefore carries little prognostic information of its own. Requiring at least two repeat measurements before a state could be assigned, which moves 151 and 129 single-value episodes into the unclassified group, left the persistent state strongly associated with death after a 72-hour landmark (9.23 [2.99–18.06] in MIMIC-IV; 20.17 [6.96–41.68] in eICU-CRD), with the ordering intact. (The variant in which the same requirement is imposed on the sustained state alone, leaving the transient and intermittent definitions untouched, is given in Table S7; the two analyses answer different questions and are not in conflict.)

**The persistent state is not an artefact of the classification window.** Because the 24-hour window is cut short whenever the index value falls close to the landmark, the state distribution was compared between episodes whose window ended before the landmark and episodes whose window was truncated. Truncation affected 211 of 642 episodes in MIMIC-IV and 172 of 485 in eICU-CRD at 72 hours, and 88 of 755 and 72 of 592 at 7 days. Truncated episodes were far more often unclassified (32.7% and 40.1% versus 4.6% and 12.5% at 72 hours) but the proportion classified as sustained was essentially identical (6.2% versus 6.0% in MIMIC-IV; 8.1% versus 9.3% in eICU-CRD), and the same held at 7 days (5.7% versus 5.2%; 6.9% versus 6.7%). Truncation therefore converts episodes into unclassified ones rather than into persistent ones. Truncated episodes were, however, sicker (in-hospital mortality 16.6% versus 10.4% and 17.4% versus 15.3%). Excluding every episode with a truncated window, which is equivalent to assigning all of them to the unclassified group since a truncated episode is either left unclassified or moved there, preserved the ordering and left the persistent state strongly associated with death: 1.20 (95% CI 0.68–2.26), 3.78 (2.07–6.96) and 7.36 (2.51–15.77) in MIMIC-IV and 2.80 (1.79–4.23), 4.08 (1.54–6.30) and 6.74 (2.13–14.45) in eICU-CRD for transient, intermittent and sustained episodes.

**A symmetric exposure window.** To remove the asymmetry altogether, the whole analysis was repeated with the exposure window fixed at 24 to 48 hours for every admission, so that no episode is classified over a longer window than any other. With a 72-hour landmark the persistent state remained strongly associated with death in both databases (MIMIC-IV 7.20 [3.68–14.05]; eICU-CRD 8.31 [3.56–17.00]). With this narrower window the intermittent state became rare (38 and 43 episodes) and its estimate correspondingly imprecise (1.53 [0.33–4.60] and 1.05 [0.56–2.65]), and transient episodes were of borderline significance (1.65 [0.90–3.44] and 2.71 [1.36–4.29]). Fixing the window also discards every episode whose first elevation occurred after hour 48: 211 of 642 episodes at the 72-hour landmark in MIMIC-IV (32.9%) and 172 of 485 in eICU-CRD (35.5%). The scarcity of intermittent episodes under a fixed window therefore reflects the length of the window as much as any instability of the state. The variable-index analysis is therefore retained as the primary one, and the fixed-window estimates are reported as the extreme case.

**Regression to the mean.** A third of index values did not clear the patient's own variability: the index value exceeded the patient's own median potassium by more than the reference change value in 63.6% of the 642 episodes of the 72-hour landmark cohort in MIMIC-IV and 65.6% of the 485 in eICU-CRD (the corresponding figures for the whole cohort of apparent episodes are 64.0% and 64.8%; Table 3). Restricting the model to episodes that cleared that margin preserved the ordering and left the persistent state associated with death (4.94, 95% CI 1.57–16.04, in MIMIC-IV; 8.04, 1.70–16.27, in eICU-CRD), with transient and intermittent episodes at 1.39 (0.80–2.63) and 4.43 (2.16–9.21) in MIMIC-IV and 2.26 (1.28–3.28) and 3.16 (1.33–5.66) in eICU-CRD. This restriction therefore attenuated rather than strengthened the estimate for the persistent state in MIMIC-IV (11.87 to 4.94) and left it essentially unchanged in eICU-CRD (8.05 to 8.04), and the transient state did not reach significance in MIMIC-IV. Departures from a patient's own usual potassium that are this large are thus not simply regression to the mean, but the margin is not a refined definition of the state and the restriction is paid for in precision.

**Competing events.** After the 72-hour landmark, 95.3% of the cohort in MIMIC-IV and 93.4% in eICU-CRD were discharged alive rather than dying in hospital, so discharge rather than death is the dominant exit from the risk set. Treated formally as a competing event, the Aalen–Johansen cumulative incidence of in-hospital death over the 30 days after the landmark was 4.14%, 7.77%, 16.67% and 41.03% in MIMIC-IV and 6.09%, 12.65%, 15.73% and 32.56% in eICU-CRD for no-episode, transient, intermittent and sustained episodes respectively (at 7 days: 2.46%, 4.85%, 12.75% and 25.64%; 4.02%, 8.98%, 10.11% and 20.93%). These are close to the crude proportions because follow-up after the landmark is short, but they are the appropriate quantities when discharge competes with death, and the ordering is unchanged. Model-based results were the same: excluding patients discharged within 48 hours of the landmark, for whom a later death would be invisible, left the ordering intact (2.57 [1.81–3.56], 4.10 [2.60–6.11] and 6.94 [3.23–12.30] in MIMIC-IV; 3.37 [2.30–4.36], 4.29 [2.06–6.39] and 7.77 [3.74–12.65] in eICU-CRD).

**Measurement density.** The number of potassium measurements after hour 24 differed between the states, so the model was refitted within strata of measurement density. Restricting to admissions at or above the median density left the gradient intact (1.75 [1.04–2.70], 4.45 [2.39–7.18] and 8.98 [3.59–19.61] in MIMIC-IV; 2.56 [1.53–3.83], 3.90 [2.09–6.49] and 9.90 [3.53–18.69] in eICU-CRD), as did restriction to the top quartile (2.38 [1.35–3.96], 4.69 [2.54–8.07] and 9.07 [3.67–19.89]; 2.73 [1.49–4.03], 3.58 [1.84–6.26] and 10.92 [2.58–22.35]). The association is therefore not produced by patients who happened to be tested more often.

**Dialysis, treatment strata and unmeasured confounding.** Renal replacement therapy was recorded for 6.2% and 4.3% of episodes; excluding those episodes left the gradient essentially unchanged (2.17 [1.62–2.88], 4.78 [3.04–6.93] and 14.48 [8.19–23.41] in MIMIC-IV; 3.07 [2.34–4.55], 3.82 [2.28–7.24] and 12.36 [7.71–26.10] in eICU-CRD). Reporting the two treatment strata separately gave the same ordering in both databases (untreated: 2.27 [1.60–3.43], 4.25 [2.32–6.81] and 12.45 [5.08–25.03] in MIMIC-IV; 3.03 [2.30–4.64], 4.05 [2.68–7.28] and 12.49 [8.00–23.90] in eICU-CRD; treated: 3.22 [2.04–6.10], 6.13 [3.30–12.87] and 15.20 [7.93–41.26] in MIMIC-IV). In eICU-CRD only 28 of the 485 episodes (5.8%) in the 72-hour landmark cohort had recorded treatment, and the stratum-specific estimates were correspondingly unstable (sustained 1.71, 95% CI 0.92–13.95; Table S7); they are reported for completeness and are not interpreted. Against a reference risk of 4.4% and 6.4%, the E-value for the persistent state was 15.5 and 10.6 (Table S9), meaning that an unmeasured confounder would have to be associated with both persistence and death by a risk ratio of that magnitude (larger than that of any covariate examined here) to explain the association away; the corresponding E-values were 7.1 and 6.8 for intermittent episodes and 2.4 and 4.4 for transient episodes.

**Clustered confidence intervals for the proportions.** In eICU-CRD, resampling hospitals rather than patients widened the intervals without changing any conclusion: incidence 3.46% (95% CI 3.0–3.9), re-measurement within six hours 42.0% (36.3–47.7), confirmation by the next measurement 23.5% (19.4–27.7) and the sustained share of apparent episodes 10.0% (8.4–11.8).

**Threshold definition.** The state definition was repeated at thresholds of 5.0, 6.0 and 6.5 mmol/L. The number of apparent episodes fell steeply as the threshold rose (from 2,629 to 308 in MIMIC-IV and from 2,316 to 205 in eICU-CRD), and the sustained share of re-measured episodes fell with it (from 16.3% to 3.2% and from 21.7% to 9.8%), so persistence was a minority at every threshold examined, including the values at which treatment is usually initiated (Table 7).

### Table 7. Sensitivity of the persistence estimate to the potassium threshold

| Threshold (mmol/L) | Apparent, n | Re-measured within 24 h, n | ≥1 further value ≥ threshold, n (%) | Sustained, n (%) |
|---|---|---|---|---|
| **MIMIC-IV** | | | | |
| 5.0 | 2,629 | 1,998 | 643 (32.2) | 326 (16.3) |
| 5.5 | 1,182 | 1,032 | 275 (26.6) | 86 (8.3) |
| 6.0 | 567 | 498 | 83 (16.7) | 22 (4.4) |
| 6.5 | 308 | 280 | 34 (12.1) | 9 (3.2) |
| **eICU-CRD** | | | | |
| 5.0 | 2,316 | 1,422 | 592 (41.6) | 309 (21.7) |
| 5.5 | 997 | 762 | 269 (35.3) | 100 (13.1) |
| 6.0 | 432 | 357 | 113 (31.7) | 34 (9.5) |
| 6.5 | 205 | 164 | 51 (31.1) | 16 (9.8) |

Both percentage columns use the episodes re-measured within 24 hours as the denominator. "At least one further value ≥ threshold" uses the whole 24-hour trajectory (the intermittent and sustained states combined) and is therefore more inclusive than the conventional next-measurement definition used in Table 4. The number of episodes falls steeply as the threshold rises, and so does the proportion that persists; persistence remains a minority at every threshold examined, including the values at which treatment is usually initiated.

---

---

## 4. Discussion

In two independent databases we found that fewer than a quarter of episodes of incident hyperkalaemia defined by a single threshold of 5.5 mmol/L in cardiac intensive care were still present at the next measurement, that this reversion is not explainable by laboratory error alone, and that the intermittent and persistent states carry a markedly higher mortality than no episode at all, whereas the excess associated with a purely transient episode is directionally consistent but smaller. The findings reframe what a "new episode of hyperkalaemia" is in this population.

**The value is real, but the state is brief.** The two mechanisms that can produce a single elevated value followed by a normal one have opposite clinical meanings. A pre-analytical artefact means the patient was never hyperkalaemic, and the correct response is to disregard the result; the extensive literature on pseudohyperkalaemia addresses precisely this scenario, with haemolysis, tourniquet time and sample transport as the usual culprits [9–12]. A genuinely transient elevation means the episode was real and the patient was, briefly, at risk. Our analysis discriminates between them using the internal variability of the data. Because potassium is measured with high analytical precision, a threshold crossing caused by assay error would be followed by another elevated value 38–83% of the time (the range spanned by the three analytical-error scenarios in both databases); we observed 22–31%. The observed rate instead matches the expectation under the variability actually present in the data, about 9.4–9.7% between consecutive measurements within a day. The practical implication is uncomfortable for a purely artefact-based reading: most of these episodes would not be prevented by better phlebotomy.

**"Incident hyperkalaemia" is a composite.** The prognostic gradient we observed is monotonic across four independent analyses (two databases and two landmark definitions) and is preserved within a single index-value band. Episodes that reverted within 24 hours still carried 1.6- to 2.8-fold adjusted odds of death, intermittent episodes 3.0- to 4.5-fold and sustained episodes 3.5- to 11.9-fold; for transient episodes the lower bound of the confidence interval reached 1 in MIMIC-IV (0.99), so that component of the gradient should be regarded as directional rather than established. This is the pattern that would be expected if the underlying condition has a spectrum: a brief excursion is a marker of a vulnerable patient, a persistent elevation is a marker of a more advanced one. It follows that a single-threshold definition pools patients whose risk differs substantially, and that estimated incidence depends on how long the window is. In our data, reported incidence falls from 5.82% to 1.35% (MIMIC-IV) and from 3.46% to 0.93% (eICU-CRD) when at least one further value above the threshold is required, and to 0.42% and 0.35% when persistence throughout the 24-hour window is required, while, importantly, the transient episodes that are removed are not low-risk episodes.

**Why this matters for prediction and for trials.** Our results identify a constraint that is intrinsic to the outcome rather than to any model of it. Any prediction model built for the threshold-defined event is being asked to predict a composite in which, among episodes that were re-measured, roughly two thirds to three quarters (73.4% and 64.7%) had no further value above the threshold at any point in the following day, and which mixes states whose mortality odds differ severalfold. Discrimination against such a target is limited by the definition of the target, not only by the predictors brought to bear on it. The same applies to enrolment: a trial, registry or quality metric that admits patients on a single threshold crossing admits a population in which a comparable proportion no longer meet the criterion a day later. Whether that is desirable depends on whether the intervention targets the excursion or the persistent state, a choice that should be made explicitly.

**What is robust, and what is not.** The reversion itself is the most robust finding: it survives every definitional choice we made, and its explanation by assay error is excluded under all three analytical-error scenarios. The prognostic signal is carried mainly by the persistent state, which remained associated with death in every specification we examined, including the primary model, the exclusion of truncated windows, the fixed 24–48 hour exposure window, a minimum of two or three measurements, adjustment for creatinine, ventilation and vasopressors, the exclusion of episodes with renal replacement therapy, both treatment strata, the exclusion of early discharges, and hospital-clustered intervals. Odds ratios were between about 4 and 15, with E-values of 10.6 and 15.5. The excess associated with a purely transient episode is smaller and less secure: it was significant in eICU-CRD in most specifications but did not reach significance in MIMIC-IV in the specification that preserves the full cohort (1.56 [0.99–2.45]), and remaining non-significant when the index value was required to clear the patient's own variability (1.39, 0.80–2.63), the excess reaching significance only in the subset without renal replacement therapy (2.17, 1.62–2.88). The intermittent state was stronger but not uniformly so: it remained significant in every database–landmark combination except the fixed 24–48 hour window, in which the state became rare (38 and 43 episodes) and its estimate correspondingly imprecise. The gradient across states should therefore be read as a robust difference between a persistent elevation and no episode, with the transient and intermittent states in between but less precisely placed; "all states are prognostically distinct" would be too strong a summary of these data.

**Detection is the rate-limiting step.** We found that only 42–52% of episodes were re-measured within six hours, although the recommendation to confirm is explicit in guidance [7,8]. The cost of closing that gap is modest in the units we studied: fewer than five repeat measurements, and in one database fewer than three, would identify a confirmed episode. Two caveats temper this. First, the exercise is operational: with these data we can show how many episodes would be identified, not that identifying them changes outcome. Second, patients who are not re-measured are not a random subset: in this cohort their in-hospital mortality was 1.9 times that of patients who were re-measured in MIMIC-IV and 1.4 times in eICU-CRD (32.0% versus 17.1% and 32.8% versus 23.4% respectively), so unmeasured trajectories are likely to be enriched for the states of greatest interest, and the measured yield is a lower bound.

**Limitations.** The analysis is observational and the two databases are drawn from United States practice; the transferability of the numerical values to other systems is untested.

*Ascertainment.* Episodes are defined by laboratory measurements that were actually taken, so patients who were never tested contribute nothing, and the cohort requires a measurement after hour 24, so those who died or left before that point are excluded by design. The landmark analysis trades this for a different restriction: a 72-hour landmark excludes 10.3% of the MIMIC-IV cohort and 19.9% of the eICU-CRD cohort, and a 7-day landmark a substantially larger share, so the adjusted odds ratios describe patients who survived long enough to be classified, and the accompanying whole-cohort rates show how much the estimates move when that restriction is removed. Within the landmark the 24-hour classification window is truncated by the landmark in 33–36% of episodes at 72 hours and 12% at 7 days. The unclassified group is a genuine gap rather than a value: it is reported as its own group rather than assigned, and its mortality (32.0% and 32.8% in the whole cohort) lies between the intermittent and sustained groups.

*Confounding.* The primary adjusted odds ratios include only the index potassium value, age and sex. Renal function, acute illness severity, vasopressor use, mechanical ventilation and renin–angiotensin–aldosterone system inhibitors all plausibly affect both whether an episode persists and whether the patient dies. Three of these (baseline creatinine, mechanical ventilation and vasopressor use) could be extracted comparably from both databases, and adding them attenuated the odds ratios while preserving their ordering (Section 3.4); the remainder, notably the use of renin–angiotensin–aldosterone system inhibitors, could not. Residual confounding by severity is therefore likely, and the odds ratios should be read as describing the prognostic weight of the state rather than as estimates of an independent causal effect. In eICU-CRD, which pools many hospitals, re-estimating the intervals with the hospital as the resampling unit widened them slightly (from 4.16–15.15 to 3.81–17.82 for sustained episodes) without changing the conclusions.

*Mechanism.* The expected confirmation rates under assay error depend on τ², the between-patient variance of true potassium, which we estimated by the method of moments rather than observed. Halving τ² lowers the expected rate under a 5.0% analytical coefficient of variation from 37.8% to 19.6% in MIMIC-IV, close to the 21.7% observed; a quartering lowers it to 7.5%. The full range, from 0.25 to 4 times the fitted τ², is given in Table S8. The exclusion of an assay artefact therefore rests on τ² being of the right order. Two considerations support the estimate: it was large relative to the analytical variance (λ = 0.69–0.96 across scenarios), and it was recovered independently in a second database (0.101 and 0.164). It nevertheless remains an estimate, and the exclusion of assay error is a statement about the aggregate behaviour of the data rather than about any individual value. We could not identify pre-analytical error directly, since haemolysis indices, tourniquet time and sample transit are not recorded in either database; our conclusion is therefore that the *aggregate* behaviour of the data is incompatible with an assay artefact, not that no individual episode was artefactual. Oral potassium supplements, insulin and beta-agonists are not recorded in a form that can be aligned to a specific measurement, so the statement that treatment did not explain the reversion applies to recorded treatment only, and a contribution of unrecorded treatment to individual reversion cannot be excluded. The within-patient variability used to bound that behaviour contains genuine short-term physiological change as well as measurement error, and measurements taken around dialysis, surgery or treatment were not excluded, so the coefficient of variation is an upper bound on analytical noise rather than a pure physiological quantity. Treatment is a plausible mechanism for some reversion and cannot be formally excluded, because it could not be quantified in a way that transfers between databases: potassium-lowering treatment recorded between the index value and the repeat measurement covered 36.3% of re-measured episodes in MIMIC-IV (375 of 1,032) but only 4.1% in eICU-CRD (31 of 762), reflecting how completely the two systems record treatment rather than how often it was given. Where it could be examined, treatment did not explain reversion: in MIMIC-IV the confirmation rate was higher among episodes with recorded treatment than among those without (27.5% versus 18.4%), and in eICU-CRD it was essentially unchanged (29.0% versus 30.8%), so within the range that the records allow, treatment does not explain the reversion; but because treatment recording is so incomplete in eICU-CRD, and because patients who received treatment without it being recorded cannot be identified, a treatment response in individual episodes remains possible. Oral potassium supplementation, insulin and beta-agonists, each of which can lower a subsequent value directly, are not recorded in a form that could be extracted, and were not accounted for.

Episodes are counted only where a measurement was taken, so the incidences reported here are incidences among patients who were measured after hour 24 rather than natural incidences; because patients who were measured more often were both more likely to have an episode detected and less likely to die (Section 3.4), the incidence estimates are conditional on the testing pattern and the prognostic estimates may be attenuated, and we did not attempt inverse-probability weighting for the measurement process. Finally, no episode in this analysis was adjudicated against a clinical review, and the clinical intent behind each measurement (surveillance, response to an alert, or routine panel) is not recoverable.

---

## 5. Conclusions

In cardiac intensive care, most episodes of incident hyperkalaemia defined by a single potassium threshold below which the patient was previously stable are not present when potassium is next measured; the observed reversion is incompatible with an isolated assay error and is most consistent with genuine short-term fluctuation. The prognostic signal was carried mainly by the persistent state, which was associated with death in every specification examined, whereas the transient and intermittent states were intermediate and less precisely placed, reaching significance in eICU-CRD but not, for the transient state, in MIMIC-IV; the 7-day estimates rest on fewer than 50 sustained episodes per database and should be read with that in mind. Reporting "new hyperkalaemia" as a single quantity therefore conceals clinically meaningful heterogeneity; occurrence and persistence should be reported as separate outcomes, and studies and trials should state which they intend to measure.

---

## Declarations

## Supplementary Materials

The following supporting information can be downloaded at the journal website. Table S1: definitions and code
lists; Table S2: cohort derivation; Table S3: full state-transition matrix; Table S4: expected confirmation rate
under competing explanations; Table S5: sensitivity of the persistent state to the minimum number of measurements;
Table S6: sensitivity of the persistence estimate to the potassium threshold; Table S7: robustness of the adjusted
odds ratio for in-hospital death; Table S8: sensitivity of the expected confirmation rate to the between-patient
variance of true potassium; Table S9: E-values for each state against the no-episode group. The STROBE checklist
for this study is provided as an additional supplementary file.

## Author Contributions

Conceptualization, Q.M. and R.Z.; Methodology, Q.M. and R.Z.; Software, Q.M.; Validation, Q.M., J.C. and L.C.; Formal Analysis, Q.M.; Investigation, Q.M.; Resources, J.C., L.C. and R.L.; Data Curation, Q.M.; Writing – Original Draft Preparation, Q.M.; Writing – Review & Editing, J.C., L.C., R.L. and R.Z.; Visualization, Q.M.; Supervision, R.Z.; Project Administration, R.Z. All authors have read and agreed to the published version of the manuscript.

## Funding

This research received no external funding.

## Institutional Review Board Statement

The study was conducted in accordance with the Declaration of Helsinki. Both databases are de-identified and
publicly available under credentialed data-use agreements. Their original collection was approved by the
institutional review boards of the Beth Israel Deaconess Medical Center and the Massachusetts Institute of
Technology (MIMIC-IV) and by the institutional review boards of the participating sites (eICU-CRD), with a waiver
of informed consent. No additional ethics approval was required for this secondary analysis of de-identified data.

## Informed Consent Statement

Not applicable. Patient consent was waived because both databases contain only de-identified retrospective data
collected under their original approvals.

## Data Availability Statement

MIMIC-IV (version 3.1) and the eICU Collaborative Research Database (version 2.0) are available on PhysioNet
(refs. [17,18]) to researchers holding a credentialed data-use agreement. Those agreements prohibit the
redistribution of patient-level data, so the derived patient-level datasets cannot be shared publicly. The analysis
code and the derived aggregate tables are archived at GitHub (https://github.com/qingcaimiao/K3-hyperkalaemia-persistence)
and deposited in Zenodo (https://doi.org/10.5281/zenodo.23343472).

## Acknowledgments

During the preparation of this work the authors used a large language model assistant (DeepSeek-V4.1-Flash,
DeepSeek AI, Hangzhou, China) to assist with review of the analysis code and with language editing.
The tool did not generate research data or results, and all outputs were reviewed and edited by the authors, who
take full responsibility for the content of this publication.

## Conflicts of Interest

The authors declare no conflicts of interest.

## Abbreviations

The following abbreviations are used in this manuscript:

| Abbreviation | Definition |
|---|---|
| CCU | coronary care unit |
| CI | confidence interval |
| CV | coefficient of variation |
| CVICU | cardiac vascular intensive care unit |
| E-value | minimum strength of association that an unmeasured confounder would need in order to explain away an observed association |
| eICU-CRD | eICU Collaborative Research Database |
| IQR | interquartile range |
| MIMIC-IV | Medical Information Mart for Intensive Care IV |
| OR | odds ratio |
| RCV | reference change value |
| RR | risk ratio |
| SD | standard deviation |
| STROBE | Strengthening the Reporting of Observational Studies in Epidemiology |
---

## References

1. Rossignol, P.; Legrand, M.; Kosiborod, M.; Hollenberg, S. M.; Peacock, W. F.; Emmett, M.; Epstein, M.; Kovesdy, C. P.; Yilmaz, M. B.; Stough, W. G.; Gayat, E.; Pitt, B.; Zannad, F.; Mebazaa, A. Emergency management of severe hyperkalemia: Guideline for best practice and opportunities for the future. *Pharmacol. Res.* 2016, 113, 585-591. https://doi.org/10.1016/j.phrs.2016.09.039
2. Rossignol, P.; Dobre, D.; McMurray, J. J. V.; Swedberg, K.; Krum, H.; van Veldhuisen, D. J.; Shi, H.; Messig, M.; Vincent, J.; Girerd, N.; Bakris, G.; Pitt, B.; Zannad, F. Incidence, Determinants, and Prognostic Significance of Hyperkalemia and Worsening Renal Function in Patients With Heart Failure Receiving the Mineralocorticoid Receptor Antagonist Eplerenone or Placebo in Addition to Optimal Medical Therapy. *Circ. Heart Fail.* 2014, 7, 51-58. https://doi.org/10.1161/CIRCHEARTFAILURE.113.000792
3. Brueske, B.; Sidhu, M. S.; Schulman-Marcus, J.; Kashani, K. B.; Barsness, G. W.; Jentzer, J. C. Hyperkalemia Is Associated With Increased Mortality Among Unselected Cardiac Intensive Care Unit Patients. *J. Am. Heart Assoc.* 2019, 8, e011814. https://doi.org/10.1161/JAHA.118.011814
4. An, J. N.; Lee, J. P.; Jeon, H. J.; Kim, D. H.; Oh, Y. K.; Kim, Y. S.; Lim, C. S. Severe hyperkalemia requiring hospitalization: predictors of mortality. *Crit. Care* 2012, 16, R225. https://doi.org/10.1186/cc11872
5. Rosano, G. M. C.; Tamargo, J.; Kjeldsen, K. P.; Lainscak, M.; Agewall, S.; Anker, S. D.; Ceconi, C.; Coats, A. J. S.; Drexel, H.; Filippatos, G.; Kaski, J. C.; Lund, L.; Niessner, A.; Ponikowski, P.; Savarese, G.; Schmidt, T. A.; Seferovic, P.; Wassmann, S.; Walther, T.; Lewis, B. S. Expert consensus document on the management of hyperkalaemia in patients with cardiovascular disease treated with renin angiotensin aldosterone system inhibitors: coordinated by the Working Group on Cardiovascular Pharmacotherapy of the European Society of Cardiology. *Eur. Heart J. Cardiovasc. Pharmacother.* 2018, 4, 180-188. https://doi.org/10.1093/ehjcvp/pvy015
6. Martín-Pérez, M.; Ruigómez, A.; Michel, A.; García Rodríguez, L. A. Impact of hyperkalaemia definition on incidence assessment: implications for epidemiological research based on a large cohort study in newly diagnosed heart failure patients in primary care. *BMC Fam. Pract.* 2016, 17, 51. https://doi.org/10.1186/s12875-016-0448-5
7. UK Kidney Association. Clinical Practice Guideline: Treatment of Acute Hyperkalaemia in Adults. Available online: https://ukkidney.org (accessed on 13 October 2026).
8. Rafique, Z.; Peacock, F.; Armstead, T.; Bischof, J. J.; Hudson, J.; Weir, M. R.; Neuenschwander, J. Hyperkalemia management in the emergency department: An expert panel consensus. *J. Am. Coll. Emerg. Physicians Open* 2021, 2, e12572. https://doi.org/10.1002/emp2.12572
9. Smellie, W. S. A. Spurious hyperkalaemia. *BMJ* 2007, 334, 693-695. https://doi.org/10.1136/bmj.39119.607986.47
10. Sevastos, N.; Theodossiades, G.; Efstathiou, S.; Papatheodoridis, G. V.; Manesis, E.; Archimandritis, A. J. Pseudohyperkalemia in serum: the phenomenon and its clinical magnitude. *J. Lab. Clin. Med.* 2006, 147, 139-144. https://doi.org/10.1016/j.lab.2005.11.008
11. Meng, Q. H.; Wagar, E. A. Pseudohyperkalemia: A new twist on an old phenomenon. *Crit. Rev. Clin. Lab. Sci.* 2015, 52, 45-55. https://doi.org/10.3109/10408363.2014.966898
12. Kellerman, P. S.; Thornbery, J. M. Pseudohyperkalemia Due to Pneumatic Tube Transport in a Leukemic Patient. *Am. J. Kidney Dis.* 2005, 46, 746-748. https://doi.org/10.1053/j.ajkd.2005.06.005
13. Zhang, Y.; Liang, S.; Wen, H. The impact of serum potassium ion variability on 28-day mortality in ICU patients. *PLoS ONE* 2024, 19, e0310046. https://doi.org/10.1371/journal.pone.0310046
14. Chávez-Íñiguez, J. S.; Maggiani-Aguilera, P.; Aranda-García de Quevedo, A.; Claure-Del Granado, R.; Vega-Vega, O.; López-Giacoman, S. R.; Chávez-Alonso, G.; Oliva-Martínez, A. E.; Díaz-Villavicencio, B.; Calderón-García, C. E.; González-Barajas, D.; Arizaga-Nápoles, M.; De la Vega-Méndez, F. M.; Navarro-Blackaller, G.; Medina-González, R.; Ibarra-Hernández, M.; García-García, G. Serum Potassium Trajectory during Acute Kidney Injury and Mortality Risk. *Nephron* 2023, 147, 521-530. https://doi.org/10.1159/000529588
15. Bakris, G.; Agiro, A.; Mu, F.; Cook, E. E.; Greatsinger, A.; Sundar, M.; Guo, H.; Louden, E.; Colman, E.; Desai, P. Consequences of Recurrent Hyperkalemia on Cardiovascular Outcomes and Mortality. *JACC Adv.* 2024, 3, 101331. https://doi.org/10.1016/j.jacadv.2024.101331
16. Kaila, R.; Hendrickson, M.; Avendano, P.; Davey, C.; Cullen, R.; Colbenson, G.; Louie, J. Hyperkalemia in a Hemolyzed Sample in Pediatric Patients. *Pediatr. Emerg. Care* 2023, 39, e1-e5. https://doi.org/10.1097/PEC.0000000000002857
17. Johnson, A. E. W.; Bulgarelli, L.; Shen, L.; Gayles, A.; Shammout, A.; Horng, S.; Pollard, T. J.; Hao, S.; Moody, B.; Gow, B.; Lehman, L. W. H.; Celi, L. A.; Mark, R. G. MIMIC-IV, a freely accessible electronic health record dataset. *Sci. Data* 2023, 10, 1. https://doi.org/10.1038/s41597-022-01899-x
18. Pollard, T. J.; Johnson, A. E. W.; Raffa, J. D.; Celi, L. A.; Mark, R. G.; Badawi, O. The eICU Collaborative Research Database, a freely available multi-center database for critical care research. *Sci. Data* 2018, 5, 180178. https://doi.org/10.1038/sdata.2018.178
19. von Elm, E.; Altman, D. G.; Egger, M.; Pocock, S. J.; Gøtzsche, P. C.; Vandenbroucke, J. P. The Strengthening the Reporting of Observational Studies in Epidemiology (STROBE) statement: guidelines for reporting observational studies. *Lancet* 2007, 370, 1453-1457. https://doi.org/10.1016/S0140-6736(07)61602-X

---
