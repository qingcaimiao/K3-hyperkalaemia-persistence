# K3 — Persistence of threshold-defined hyperkalaemia in cardiac intensive care

Analysis code and derived aggregate results for the manuscript:

> **Most episodes of incident hyperkalaemia defined by a single threshold in cardiac intensive care do not persist:
> definition, short-term stability and prognosis in two databases**

Submitted to the *Journal of Clinical Medicine* (MDPI).

**Archived version of record:** v1.0.0 — https://doi.org/10.5281/zenodo.23343472
(concept DOI, always resolving to the latest version: https://doi.org/10.5281/zenodo.23343471)

> **Note on versions.** The archived v1.0.0 corresponds to the analysis as reported. Figure file names in v1.0.0 predate a final renumbering of the figures to match their order of first citation in the manuscript and, for the cohort flow diagram, a correction to an overlapping data label; the `main` branch carries the final figure files and the pre-submission audit scripts. The analysis itself is unchanged between v1.0.0 and `main`.

---

## What the study does

A single potassium value ≥5.5 mmol/L defines an episode of incident hyperkalaemia. This repository contains the code
that treats that threshold crossing **as the object of analysis**: how often the value falls again within 24 hours,
whether the fall is explained by analytical error, and whether persistence carries prognostic information.

Two independent, publicly available intensive care databases are analysed separately and reported side by side:

| Database | Version | Source | Cohort analysed |
|---|---|---|---|
| MIMIC-IV | 3.1 | PhysioNet (credentialed access) | 20,322 admissions |
| eICU-CRD | 2.0 | PhysioNet (credentialed access) | 28,805 admissions, 44 hospitals |

---

## Important: no patient-level data are distributed here

Both source databases are released under credentialed data-use agreements that **prohibit redistribution of
patient-level data**. Accordingly, this repository contains **only analysis code and derived aggregate results**
(states, odds ratios, confidence intervals, counts). It contains no individual-level records and cannot be used to
re-identify any patient. Researchers who wish to reproduce the analysis at the record level must obtain access to
MIMIC-IV and eICU-CRD from PhysioNet themselves.

## Repository layout

```
code/       Analysis scripts, in the order they were run (see pipeline below)
results/    Derived aggregate outputs (CSV/JSON) — one file per analysis step
figures/    Final figures (600 dpi PNG and TIFF), as submitted
```

## Pipeline (order of execution)

The scripts are numbered in the order of the analysis. A summary of the stages:

| Stage | Scripts | Purpose |
|---|---|---|
| 1. Extraction | `k29_pivot_probe.py`, `k30_k3_phase1.py` | Build the potassium time series and the analysis cohort from both databases |
| 2. Variability | `k31a_k3_rtm.py`, `k31b_k3_tx.py`, `k31c_k3_noise.py`, `k31d_k3_gap.py` | Within-patient variability, reference change value, transition matrix, analytical-error bounds |
| 3. States | `k32_k3_phase3.py`, `k33_k3_phase3b.py` | Outcome-state definition and landmark analyses |
| 4. Detection | `k34_k3_rule.py`, `k35*_verify.py`, `k36_desc.py` | Re-measurement practice and the yield of a repeat-measurement rule |
| 5. Figures | `k37_figs_k3.py`, `k41b_fig_flow.py`, `k46_figs_redo.py`, `k46b_fig3_redo.py` | Final figures at 600 dpi |
| 6. Five-state reclassification | `k39_k3_reclass.py`, `k39b_sens_or.py`, `k40_k3_whole_band.py` | Transient / intermittent / sustained / unclassified states; minimum-measurement sensitivity |
| 7. Robustness | `k48*_round2*.py`, `k49_k3_fixedwin.py`, `k50_k3_round3.py`, `k51_k3_compete.py`, `k53_k3_rcv.py`, `k54_k3_trunc.py` | Truncated windows, fixed exposure window, competing-risk (Aalen–Johansen), measurement density, treatment strata, E-values, hospital-clustered bootstrap |
| 8. Tables and checks | `k41_k3_bounds_flow.py`, `k42_k3_table1.py`, `k43_k3_cluster.py`, `k47_supp_tables.py`, `k52_supp_s89.py` | Manuscript tables and supplementary tables S1–S9 |
| 9. Verification | `k44_k3_refs_check.py`, `k45*_novelty.py`, `k55_jcm_refs.py`, `k56_jcm_frontmatter.py` | Reference verification (Crossref + Europe PMC), novelty searches, journal formatting |
| 10. Audit | `_k3_audit.py`, `_k3_audit2.py`, `_k3_footnote_check.py`, `_k3_fullscan.py`, `_k3_final_check.py` | Independent recomputation of every number, table-footnote checks, whole-text number traceability, EN/CN consistency |

## Reproducing the analysis

1. Obtain MIMIC-IV v3.1 and eICU-CRD v2.0 from PhysioNet and place them locally (paths are set at the top of
   `k30_k3_phase1.py`).
2. `pip install -r requirements.txt`
3. Run the scripts in the numbered order above. Intermediate artefacts are written to `out/`; aggregate outputs used
   in the manuscript are those in `results/`.

Because the source databases are credentialed, the pipeline cannot be executed without a data-use agreement. The
aggregate results in `results/` are sufficient to verify every number reported in the manuscript and its
supplementary tables.

## Notes on reproducibility

- Every number in the manuscript and the supplementary tables is produced by these scripts. No value was
  transcribed by hand.
- Sensitivity analyses reuse the primary cohort-construction functions; each script asserts that its cohort
  distribution matches the corresponding table in the manuscript.
- References were verified against Crossref and Europe PMC; journal abbreviations and author lists were taken from
  the publisher record rather than transcribed.

## Licence

Code: MIT (see `LICENSE`). The source data are governed by their own data-use agreements and are not covered by
this licence.
