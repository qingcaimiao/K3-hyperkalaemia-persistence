# -*- coding: utf-8 -*-
"""K3 补充：表1 描述性统计（五档：年龄中位/男性%/测量次数中位/基线血钾）"""
import duckdb, pandas as pd, numpy as np, warnings
warnings.filterwarnings('ignore')
M = 'D:/shujuku/mimic-iv-3.1'; E = 'D:/shujuku/EICU 2.0'
T = lambda p: "read_csv_auto('{}', strict_mode=false, ignore_errors=true)".format(p)
con = duckdb.connect(); con.execute('SET threads=6')
BASE = 1440
CIC = "regexp_matches(first_careunit,'CCU|CVICU')"
CIT = "regexp_matches(unittype,'Cardiac ICU|CCU|CSICU|CTICU')"

qm = f"""WITH icu AS (SELECT stay_id, subject_id, hadm_id, intime,
             ROW_NUMBER() OVER (PARTITION BY hadm_id ORDER BY intime) AS rn
             FROM {T(M + '/icu/icustays.csv')} WHERE {CIC}), co AS (SELECT * FROM icu WHERE rn=1)
SELECT co.stay_id AS sid, p.gender AS sex,
       TRY_CAST(p.anchor_age AS DOUBLE)+GREATEST(TRY_CAST(EXTRACT(YEAR FROM co.intime) AS INT)-p.anchor_year,0) AS age
FROM co JOIN {T(M + '/hosp/patients.csv')} p ON p.subject_id=co.subject_id"""
om = con.execute(qm).df()
qe = f"""SELECT patientunitstayid AS sid, gender AS sex, TRY_CAST(age AS DOUBLE) AS age
       FROM {T(E + '/patient.csv')} WHERE {CIT}"""
oe = con.execute(qe).df()

D5 = ['no_event', 'transient', 'intermittent', 'sustained', 'unclassified']
rows, txt = [], []
for nm, dpkl, oc in [('MIMIC-IV', 'out/k3_k_series_mimic.pkl', om),
                     ('eICU-CRD', 'out/k3_k_series_eicu.pkl', oe)]:
    d = pd.read_pickle(dpkl).sort_values(['sid', 't']).reset_index(drop=True)
    pre = d[d.t <= BASE].groupby('sid').agg(pre_max=('k', 'max'))
    nmeas = d.groupby('sid').size().rename('n_k')
    rec = []
    for sid, g in d.groupby('sid', sort=False):
        pm = pre.pre_max.get(sid, np.nan)
        if pd.isna(pm) or pm >= 5.5: continue
        post = g[g.t > BASE]
        if len(post) == 0: continue
        pos = post[post.k >= 5.5]
        if len(pos) == 0:
            rec.append(dict(sid=int(sid), grp='no_event', pre_max=float(pm))); continue
        idx = pos.iloc[0]
        a = post[(post.t > idx.t) & (post.t <= idx.t + BASE)]
        if len(a) == 0: grp = 'unclassified'
        elif bool((a.k >= 5.5).all()): grp = 'sustained'
        elif bool((a.k >= 5.5).any()): grp = 'intermittent'
        else: grp = 'transient'
        rec.append(dict(sid=int(sid), grp=grp, pre_max=float(pm)))
    e = pd.DataFrame(rec).merge(oc, on='sid', how='left').merge(nmeas, on='sid', how='left')
    print('=== %s (n=%s)' % (nm, format(len(e), ',')))
    for g in D5:
        s = e[e.grp == g]
        if not len(s): continue
        age_m = float(pd.to_numeric(s.age, errors='coerce').median())
        male = 100 * float((s.sex.astype(str).str.upper().str[0] == 'M').mean())
        nk_m = float(s.n_k.median())
        nk_iqr = (float(s.n_k.quantile(.25)), float(s.n_k.quantile(.75)))
        pre_m = float(s.pre_max.median()); pre_lo = float(s.pre_max.quantile(.25)); pre_hi = float(s.pre_max.quantile(.75))
        print('  %-14s n=%6s age %.1f male %.1f%% 测量中位 %.1f (IQR %.0f-%.0f) 基线K中位 %.1f (%.1f-%.1f)'
              % (g, format(len(s), ','), age_m, male, nk_m, nk_iqr[0], nk_iqr[1], pre_m, pre_lo, pre_hi))
        rows.append(dict(db=nm, grp=g, n=len(s), age_median=age_m, male_pct=round(male, 1),
                         n_k_median=nk_m, n_k_q1=nk_iqr[0], n_k_q3=nk_iqr[1],
                         baseline_k_median=pre_m, baseline_k_q1=pre_lo, baseline_k_q3=pre_hi))
pd.DataFrame(rows).to_csv('out/k42_table1.csv', index=False, encoding='utf-8-sig')
print('\n写出 out/k42_table1.csv')
