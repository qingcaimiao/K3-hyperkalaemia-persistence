# -*- coding: utf-8 -*-
"""k64: reduce em-dash density in the English manuscript.
Only prose em dashes are replaced (commas, parentheses, colons, or sentence splits).
The single em dash used as a missing-value marker inside Table 4 is retained.
Every replacement is asserted to occur exactly once; the script aborts otherwise.
"""
import io, sys

P = 'out/manuscript_K3.md'
s = io.open(P, encoding='utf-8').read()
before = s.count('\u2014')

PAIRS = [
 # 1  Introduction: threshold parenthetical
 ("crossing a threshold \u2014 most often 5.5 mmol/L, the lower bound of the mild band in current guidance [5] \u2014 and the choice of threshold already changes the measured incidence substantially [6].",
  "crossing a threshold (most often 5.5 mmol/L, the lower bound of the mild band in current guidance [5]), and the choice of threshold already changes the measured incidence substantially [6]."),
 # 2  Introduction: artefacts apposition
 ("almost entirely about *laboratory artefacts* \u2014 that is, values that do not reflect the patient's true potassium at all.",
  "almost entirely about *laboratory artefacts*, that is, values that do not reflect the patient's true potassium at all."),
 # 3  Methods 2.2: record level parenthetical
 ("The two databases carry laboratory results on different records \u2014 in MIMIC-IV on the hospital record, in eICU-CRD against the intensive care stay \u2014 so the definition was applied identically in both and its consequence examined directly.",
  "The two databases carry laboratory results on different records (in MIMIC-IV on the hospital record, in eICU-CRD against the intensive care stay), so the definition was applied identically in both and its consequence examined directly."),
 # 4-7  Methods 2.3: definition list -> colon
 ("- **transient** \u2014 every subsequent measurement was below 5.5 mmol/L;",
  "- **transient**: every subsequent measurement was below 5.5 mmol/L;"),
 ("- **intermittent** \u2014 at least one subsequent measurement reached 5.5 mmol/L, but not all of them did;",
  "- **intermittent**: at least one subsequent measurement reached 5.5 mmol/L, but not all of them did;"),
 ("- **sustained** \u2014 every subsequent measurement was at least 5.5 mmol/L;",
  "- **sustained**: every subsequent measurement was at least 5.5 mmol/L;"),
 ("- **unclassified** \u2014 no measurement followed within 24 hours, so persistence could not be determined.",
  "- **unclassified**: no measurement followed within 24 hours, so persistence could not be determined."),
 # 8  Methods 2.7: treatment categories -> colon + new sentence
 ("we sought five categories of treatment \u2014 insulin given with glucose, a potassium-binding resin, intravenous calcium, sodium bicarbonate and renal replacement therapy \u2014 and classified an episode as treated if any was recorded",
  "we sought five categories of treatment: insulin given with glucose, a potassium-binding resin, intravenous calcium, sodium bicarbonate and renal replacement therapy. An episode was classified as treated if any was recorded"),
 # 9  Results 3.1
 ("were sustained \u2014 that is, never fell below the threshold across the following 24 hours.",
  "were sustained, that is, never fell below the threshold across the following 24 hours."),
 # 10 Results 3.3: noise parenthetical
 ("If the observed within-patient variability is taken to be noise \u2014 that is, if a patient's true potassium is assumed constant and only the state is allowed to vary \u2014 the expected confirmation rate is 14.7% and 19.2%,",
  "If the observed within-patient variability is taken to be noise (that is, if a patient's true potassium is assumed constant and only the state is allowed to vary), the expected confirmation rate is 14.7% and 19.2%,"),
 # 11 Results 3.4: reclassification -> split sentence
 ("This reclassifies much of the sustained group \u2014 in the whole cohort, 40 of 86 sustained episodes in MIMIC-IV (46.5%) and 69 of 100 in eICU-CRD (69.0%) rested on a single repeat value \u2014 yet the ordering survived at every database and landmark, and the adjusted odds ratio for sustained episodes remained far above that for transient episodes",
  "This reclassifies much of the sustained group, since in the whole cohort 40 of 86 sustained episodes in MIMIC-IV (46.5%) and 69 of 100 in eICU-CRD (69.0%) rested on a single repeat value. The ordering nevertheless survived at every database and landmark, and the adjusted odds ratio for sustained episodes remained far above that for transient episodes"),
 # 12 Results 3.6
 ("Requiring at least two repeat measurements before a state could be assigned \u2014 which moves 151 and 129 single-value episodes into the unclassified group \u2014 left the persistent state strongly associated with death",
  "Requiring at least two repeat measurements before a state could be assigned, which moves 151 and 129 single-value episodes into the unclassified group, left the persistent state strongly associated with death"),
 # 13 Results 3.6
 ("Excluding every episode with a truncated window \u2014 which is equivalent to assigning all of them to the unclassified group, since a truncated episode is either left unclassified or moved there \u2014 preserved the ordering",
  "Excluding every episode with a truncated window, which is equivalent to assigning all of them to the unclassified group since a truncated episode is either left unclassified or moved there, preserved the ordering"),
 # 14 Results 3.6 fixed window -> colon + split
 ("Fixing the window also discards every episode whose first elevation occurred after hour 48 \u2014 211 of 642 episodes at the 72-hour landmark in MIMIC-IV (32.9%) and 172 of 485 in eICU-CRD (35.5%) \u2014 so the scarcity of intermittent episodes under a fixed window reflects the length of the window as much as any instability of the state.",
  "Fixing the window also discards every episode whose first elevation occurred after hour 48: 211 of 642 episodes at the 72-hour landmark in MIMIC-IV (32.9%) and 172 of 485 in eICU-CRD (35.5%). The scarcity of intermittent episodes under a fixed window therefore reflects the length of the window as much as any instability of the state."),
 # 15 Results 3.6 regression to the mean
 ("left the persistent state associated with death \u2014 4.94 (95% CI 1.57\u201316.04) in MIMIC-IV and 8.04 (1.70\u201316.27) in eICU-CRD \u2014 with transient and intermittent episodes at",
  "left the persistent state associated with death (4.94, 95% CI 1.57\u201316.04, in MIMIC-IV; 8.04, 1.70\u201316.27, in eICU-CRD), with transient and intermittent episodes at"),
 # 16 Results 3.6 E-value
 ("by a risk ratio of that magnitude \u2014 larger than that of any covariate examined here \u2014 to explain the association away",
  "by a risk ratio of that magnitude (larger than that of any covariate examined here) to explain the association away"),
 # 17 Discussion: monotonic
 ("is monotonic across four independent analyses \u2014 two databases and two landmark definitions \u2014 and is preserved within a single index-value band.",
  "is monotonic across four independent analyses (two databases and two landmark definitions) and is preserved within a single index-value band."),
 # 18 Discussion: composite
 ("when persistence throughout the 24-hour window is required \u2014 while, importantly, the transient episodes that are removed are not low-risk episodes.",
  "when persistence throughout the 24-hour window is required, while, importantly, the transient episodes that are removed are not low-risk episodes."),
 # 19 Discussion: what is robust -> colon-free long list
 ("which remained associated with death in every specification we examined \u2014 the primary model, the exclusion of truncated windows, the fixed 24\u201348 hour exposure window, a minimum of two or three measurements, adjustment for creatinine, ventilation and vasopressors, the exclusion of episodes with renal replacement therapy, both treatment strata, the exclusion of early discharges, and hospital-clustered intervals \u2014 with odds ratios between about 4 and 15 and E-values of 10.6 and 15.5.",
  "which remained associated with death in every specification we examined, including the primary model, the exclusion of truncated windows, the fixed 24\u201348 hour exposure window, a minimum of two or three measurements, adjustment for creatinine, ventilation and vasopressors, the exclusion of episodes with renal replacement therapy, both treatment strata, the exclusion of early discharges, and hospital-clustered intervals. Odds ratios were between about 4 and 15, with E-values of 10.6 and 15.5."),
 # 20 Discussion: detection
 ("are not a random subset \u2014 in this cohort their in-hospital mortality was 1.9 times",
  "are not a random subset: in this cohort their in-hospital mortality was 1.9 times"),
 # 21 Limitations: ascertainment
 ("the cohort requires a measurement after hour 24 \u2014 those who died or left before that point are excluded by design.",
  "the cohort requires a measurement after hour 24, so those who died or left before that point are excluded by design."),
 # 22 Limitations: confounding
 ("Three of these \u2014 baseline creatinine, mechanical ventilation and vasopressor use \u2014 could be extracted comparably from both databases",
  "Three of these (baseline creatinine, mechanical ventilation and vasopressor use) could be extracted comparably from both databases"),
 # 23 Limitations: confounding (clustered CI)
 ("widened them slightly \u2014 from 4.16\u201315.15 to 3.81\u201317.82 for sustained episodes \u2014 without changing the conclusions.",
  "widened them slightly (from 4.16\u201315.15 to 3.81\u201317.82 for sustained episodes) without changing the conclusions."),
 # 24 Limitations: mechanism
 ("treatment did not explain reversion \u2014 in MIMIC-IV the confirmation rate was higher among episodes with recorded treatment",
  "treatment did not explain reversion: in MIMIC-IV the confirmation rate was higher among episodes with recorded treatment"),
 # 25 Table 7 footnote
 ("uses the whole 24-hour trajectory \u2014 the intermittent and sustained states combined \u2014 and is therefore more inclusive",
  "uses the whole 24-hour trajectory (the intermittent and sustained states combined) and is therefore more inclusive"),
 # 26 Limitations: mechanism (second dash in the same paragraph)
 ("(29.0% versus 30.8%) \u2014 so within the range that the records allow, treatment does not explain the reversion;",
  "(29.0% versus 30.8%), so within the range that the records allow, treatment does not explain the reversion;"),
]
errs = []
for i, (o, n) in enumerate(PAIRS, 1):
    c = s.count(o)
    if c != 1:
        errs.append(f"  pair {i}: found {c} times -> {o[:70]!r}")
        continue
    s = s.replace(o, n, 1)

if errs:
    print("ABORT - replacements not unique/exact:")
    print('\n'.join(errs)); sys.exit(1)

after = s.count('\u2014')
resid = [(i + 1, l.strip()[:100]) for i, l in enumerate(s.split('\n')) if '\u2014' in l]
print(f"prose em dashes: {before} -> {after}   (replacements applied: {len(PAIRS)})")
print("remaining occurrences:")
for i, l in resid:
    print(f"  L{i}: {l}")
assert after == 1, "expected exactly one em dash left (the missing-value marker in Table 4)"
io.open(P, 'w', encoding='utf-8').write(s)
print("written:", P)
