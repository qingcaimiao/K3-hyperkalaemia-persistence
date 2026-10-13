# -*- coding: utf-8 -*-
"""K3 补充：五档状态的全队列死亡率 + 5.5–5.9 索引带内的 landmark 率（供表5用）"""
import duckdb, pandas as pd, numpy as np, json, warnings
from sklearn.linear_model import LogisticRegression
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
SELECT co.stay_id AS sid, DATE_DIFF('minute', co.intime, a.dischtime) AS los_hosp_min,
       a.hospital_expire_flag AS died_inhosp, p.gender AS sex,
       TRY_CAST(p.anchor_age AS DOUBLE)+GREATEST(TRY_CAST(EXTRACT(YEAR FROM co.intime) AS INT)-p.anchor_year,0) AS age
FROM co JOIN {T(M + '/hosp/admissions.csv')} a ON a.hadm_id=co.hadm_id
        JOIN {T(M + '/hosp/patients.csv')} p ON p.subject_id=co.subject_id"""
om = con.execute(qm).df()
qe = f"""SELECT patientunitstayid AS sid, TRY_CAST(hospitaldischargeoffset AS DOUBLE) AS los_hosp_min,
       CASE WHEN lower(coalesce(hospitaldischargestatus,'')) LIKE 'expired%' THEN 1 ELSE 0 END AS died_inhosp,
       gender AS sex, TRY_CAST(age AS DOUBLE) AS age FROM {T(E + '/patient.csv')} WHERE {CIT}"""
oe = con.execute(qe).df()

GROUPS = ['transient', 'intermittent', 'conf_not_assessed', 'sustained']
D5 = ['no_event'] + GROUPS + ['unclassified']
rows = []

for nm, dpkl, oc in [('MIMIC-IV', 'out/k3_k_series_mimic.pkl', om),
                     ('eICU-CRD', 'out/k3_k_series_eicu.pkl', oe)]:
    d = pd.read_pickle(dpkl).sort_values(['sid', 't']).reset_index(drop=True)
    # ---- 1) 全队列五档（无 landmark 截断）----
    full = []
    for sid, g in d.groupby('sid', sort=False):
        pre = g[g.t <= BASE]
        if len(pre) == 0 or float(pre.k.max()) >= 5.5: continue
        post = g[g.t > BASE]
        if len(post) == 0: continue
        pos = post[post.k >= 5.5]
        if len(pos) == 0:
            full.append(dict(sid=int(sid), grp='no_event', k_idx=np.nan)); continue
        idx = pos.iloc[0]
        a = post[(post.t > idx.t) & (post.t <= idx.t + BASE)]
        if len(a) == 0: grp = 'unclassified'
        elif bool((a.k >= 5.5).all()): grp = 'sustained'
        elif bool((a.k >= 5.5).any()): grp = 'intermittent'
        else: grp = 'transient'
        full.append(dict(sid=int(sid), grp=grp, k_idx=float(idx.k)))
    fc = pd.DataFrame(full).merge(oc, on='sid', how='left')
    print('=== %s 全队列五档（n=%s）' % (nm, format(len(fc), ',')))
    for g in D5:
        s = fc[fc.grp == g]
        if not len(s): continue
        print('   %-20s n=%6s 死亡 %5.1f%%' % (g, format(len(s), ','), 100 * s.died_inhosp.mean()))
        rows.append(dict(part='whole', db=nm, grp=g, n=int(len(s)),
                         died=round(100 * float(s.died_inhosp.mean()), 1)))

    # ---- 2) 5.5–5.9 索引带内的 72h / 7d landmark 率 ----
    for H, lab in [(4320, '72 h'), (10080, '7 d')]:
        lmk_rows = []
        for sid, g in d.groupby('sid', sort=False):
            pre = g[g.t <= BASE]
            if len(pre) == 0 or float(pre.k.max()) >= 5.5: continue
            post = g[(g.t > BASE) & (g.t <= H)]
            if len(post) == 0: continue
            pos = post[post.k >= 5.5]
            if len(pos) == 0: continue
            idx = pos.iloc[0]
            a = post[(post.t > idx.t) & (post.t <= idx.t + BASE)]
            if len(a) == 0: grp = 'unclassified'
            elif bool((a.k >= 5.5).all()): grp = 'sustained'
            elif bool((a.k >= 5.5).any()): grp = 'intermittent'
            else: grp = 'transient'
            lmk_rows.append(dict(sid=int(sid), grp=grp, k_idx=float(idx.k)))
        lc = pd.DataFrame(lmk_rows).merge(oc, on='sid', how='left')
        lc = lc[lc.los_hosp_min > H]
        band = lc[(lc.k_idx >= 5.5) & (lc.k_idx < 6.0)]
        print('  -- %s landmark，索引带 5.5–5.9（n=%s）' % (lab, format(len(band), ',')))
        for g in ['transient', 'intermittent', 'sustained']:
            s = band[band.grp == g]
            if not len(s): continue
            print('       %-14s n=%4s 死亡 %5.1f%%' % (g, format(len(s), ','), 100 * s.died_inhosp.mean()))
            rows.append(dict(part='band55_59|' + lab, db=nm, grp=g, n=int(len(s)),
                             died=round(100 * float(s.died_inhosp.mean()), 1)))

pd.DataFrame(rows).to_csv('out/k40_whole_band.csv', index=False, encoding='utf-8-sig')
print('\n写出 out/k40_whole_band.csv')
