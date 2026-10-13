# -*- coding: utf-8 -*-
"""K3 第三批：eICU 医院层面聚类 bootstrap + 补充严重度校正（基线肌酐 / 机械通气 / 血管活性药）

纪律：凡两个列表并行索引处一律 assert len(a)==len(b)，并打印变量名与系数。
产出：out/k43_cluster.csv（72h landmark，五档 OR，含 普通bootstrap 与 医院聚类bootstrap 两套 CI）
      out/k43_adj.csv（加入严重度变量后的 OR）
"""
import duckdb, pandas as pd, numpy as np, json, warnings
from sklearn.linear_model import LogisticRegression
warnings.filterwarnings('ignore')
M = 'D:/shujuku/mimic-iv-3.1'; E = 'D:/shujuku/EICU 2.0'
T = lambda p: "read_csv_auto('{}', strict_mode=false, ignore_errors=true)".format(p)
con = duckdb.connect(); con.execute('SET threads=6')
BASE = 1440; H = 4320
CIC = "regexp_matches(first_careunit,'CCU|CVICU')"
CIT = "regexp_matches(unittype,'Cardiac ICU|CCU|CSICU|CTICU')"
GROUPS = ['transient', 'intermittent', 'sustained']

# ---------- MIMIC 协变量 ----------
qm = f"""WITH icu AS (SELECT stay_id, subject_id, hadm_id, intime,
             ROW_NUMBER() OVER (PARTITION BY hadm_id ORDER BY intime) AS rn
             FROM {T(M + '/icu/icustays.csv')} WHERE {CIC}), co AS (SELECT * FROM icu WHERE rn=1)
SELECT co.stay_id AS sid, a.hospital_expire_flag AS died_inhosp, p.gender AS sex,
       TRY_CAST(p.anchor_age AS DOUBLE)+GREATEST(TRY_CAST(EXTRACT(YEAR FROM co.intime) AS INT)-p.anchor_year,0) AS age,
       DATE_DIFF('minute', co.intime, a.dischtime) AS los_hosp_min
FROM co JOIN {T(M + '/hosp/admissions.csv')} a ON a.hadm_id=co.hadm_id
        JOIN {T(M + '/hosp/patients.csv')} p ON p.subject_id=co.subject_id"""
om = con.execute(qm).df()
qcr_m = f"""WITH icu AS (SELECT stay_id, hadm_id, intime, ROW_NUMBER() OVER (PARTITION BY hadm_id ORDER BY intime) AS rn
              FROM {T(M + '/icu/icustays.csv')} WHERE {CIC}), co AS (SELECT * FROM icu WHERE rn=1)
SELECT co.stay_id AS sid, MAX(TRY_CAST(le.valuenum AS DOUBLE)) AS cr_base
FROM co JOIN {T(M + '/hosp/labevents.csv')} le ON le.hadm_id=co.hadm_id
WHERE le.itemid=50912 AND le.charttime >= co.intime AND le.charttime <= co.intime + INTERVAL 24 HOUR
  AND TRY_CAST(le.valuenum AS DOUBLE) BETWEEN 0.05 AND 50 GROUP BY 1"""
cr_m = con.execute(qcr_m).df()
qmv_m = f"""WITH icu AS (SELECT stay_id, hadm_id, intime, ROW_NUMBER() OVER (PARTITION BY hadm_id ORDER BY intime) AS rn
              FROM {T(M + '/icu/icustays.csv')} WHERE {CIC}), co AS (SELECT * FROM icu WHERE rn=1)
SELECT DISTINCT co.stay_id AS sid, 1 AS mv FROM co
JOIN {T(M + '/icu/procedureevents.csv')} pe ON pe.stay_id=co.stay_id
WHERE pe.itemid IN (225792, 225794)"""
mv_m = con.execute(qmv_m).df()
qvp_m = f"""WITH icu AS (SELECT stay_id, hadm_id, intime, ROW_NUMBER() OVER (PARTITION BY hadm_id ORDER BY intime) AS rn
              FROM {T(M + '/icu/icustays.csv')} WHERE {CIC}), co AS (SELECT * FROM icu WHERE rn=1)
SELECT DISTINCT co.stay_id AS sid, 1 AS vp FROM co
JOIN {T(M + '/icu/inputevents.csv')} ie ON ie.stay_id=co.stay_id
WHERE ie.itemid IN (221906,221289,221662,221653,221749,222315)"""
vp_m = con.execute(qvp_m).df()

# ---------- eICU 协变量 ----------
qe = f"""SELECT patientunitstayid AS sid, hospitalid AS hosp,
       CASE WHEN lower(coalesce(hospitaldischargestatus,'')) LIKE 'expired%' THEN 1 ELSE 0 END AS died_inhosp,
       gender AS sex, TRY_CAST(age AS DOUBLE) AS age,
       TRY_CAST(hospitaldischargeoffset AS DOUBLE) AS los_hosp_min
       FROM {T(E + '/patient.csv')} WHERE {CIT}"""
oe = con.execute(qe).df()
qcr_e = f"""SELECT p.patientunitstayid AS sid, MAX(TRY_CAST(l.labresult AS DOUBLE)) AS cr_base
FROM {T(E + '/patient.csv')} p JOIN {T(E + '/lab.csv')} l ON l.patientunitstayid=p.patientunitstayid
WHERE lower(l.labname)='creatinine' AND l.labresultoffset BETWEEN -1440 AND 1440
  AND TRY_CAST(l.labresult AS DOUBLE) BETWEEN 0.05 AND 50 GROUP BY 1"""
cr_e = con.execute(qcr_e).df()
qmv_e = f"""SELECT DISTINCT patientunitstayid AS sid, 1 AS mv FROM {T(E + '/respiratorycare.csv')}
WHERE (ventstartoffset IS NOT NULL AND ventstartoffset >= 0)
   OR lower(coalesce(airwaytype,'')) LIKE '%endotracheal%' OR lower(coalesce(airwaytype,'')) LIKE '%tracheostomy%'"""
mv_e = con.execute(qmv_e).df()
qvp_e = f"""SELECT DISTINCT patientunitstayid AS sid, 1 AS vp FROM {T(E + '/infusionDrug.csv')}
WHERE lower(drugname) LIKE '%norepinephrine%' OR lower(drugname) LIKE '%epinephrine%'
   OR lower(drugname) LIKE '%dopamine%' OR lower(drugname) LIKE '%dobutamine%'
   OR lower(drugname) LIKE '%phenylephrine%' OR lower(drugname) LIKE '%vasopressin%'"""
vp_e = con.execute(qvp_e).df()
print('协变量覆盖：MIMIC CICU %s 例（肌酐 %s，通气 %s，升压药 %s）| eICU %s 例（肌酐 %s，通气 %s，升压药 %s）'
      % (f'{len(om):,}', f'{len(cr_m):,}', f'{len(mv_m):,}', f'{len(vp_m):,}',
         f'{len(oe):,}', f'{len(cr_e):,}', f'{len(mv_e):,}', f'{len(vp_e):,}'))


def classify(d, oc):
    rec = []
    for sid, g in d.groupby('sid', sort=False):
        pre = g[g.t <= BASE]
        if len(pre) == 0 or float(pre.k.max()) >= 5.5: continue
        post = g[(g.t > BASE) & (g.t <= H)]
        if len(post) == 0: continue
        pos = post[post.k >= 5.5]
        if len(pos) == 0:
            rec.append(dict(sid=int(sid), grp='no_event', k_idx=np.nan)); continue
        idx = pos.iloc[0]
        a = post[(post.t > idx.t) & (post.t <= idx.t + BASE)]
        if len(a) == 0: grp = 'unclassified'
        elif bool((a.k >= 5.5).all()): grp = 'sustained'
        elif bool((a.k >= 5.5).any()): grp = 'intermittent'
        else: grp = 'transient'
        rec.append(dict(sid=int(sid), grp=grp, k_idx=float(idx.k)))
    return pd.DataFrame(rec).merge(oc, on='sid', how='left')


def fit(sub, feats, y_col='died_inhosp', cluster=None, seed=3, nb=400):
    X = sub[feats].astype(float).values; y = sub[y_col].astype(int).values
    m = LogisticRegression(max_iter=5000).fit(X, y)
    assert len(feats) == len(m.coef_[0]), 'feats/coef 长度不一致'
    print('     变量与系数：' + ' | '.join('%s %.3f' % (f, c) for f, c in zip(feats, m.coef_[0])))
    rng = np.random.default_rng(seed); bs = []
    if cluster is None:
        for _ in range(nb):
            i = rng.integers(0, len(y), len(y))
            if len(np.unique(y[i])) < 2: continue
            try: bs.append(LogisticRegression(max_iter=5000).fit(X[i], y[i]).coef_[0])
            except Exception: pass
    else:
        cl = pd.Series(cluster).values
        uniq = np.unique(cl)
        for _ in range(nb):
            pick = rng.choice(uniq, len(uniq), replace=True)
            idx = np.concatenate([np.where(cl == c)[0] for c in pick])
            if len(np.unique(y[idx])) < 2: continue
            try: bs.append(LogisticRegression(max_iter=5000).fit(X[idx], y[idx]).coef_[0])
            except Exception: pass
    bs = np.array(bs)
    out = {}
    for j, f in enumerate(feats):
        ci = np.exp(np.percentile(bs[:, j], [2.5, 97.5])) if len(bs) > 50 else [np.nan, np.nan]
        out[f] = (round(float(np.exp(m.coef_[0][j])), 2), round(float(ci[0]), 2), round(float(ci[1]), 2))
    return out, len(bs)


rows_c, rows_a = [], []
for nm, dpkl, oc, cr, mv, vp in [('MIMIC-IV', 'out/k3_k_series_mimic.pkl', om, cr_m, mv_m, vp_m),
                                 ('eICU-CRD', 'out/k3_k_series_eicu.pkl', oe, cr_e, mv_e, vp_e)]:
    d = pd.read_pickle(dpkl).sort_values(['sid', 't']).reset_index(drop=True)
    e = classify(d, oc)
    e = e.merge(cr, on='sid', how='left').merge(mv, on='sid', how='left').merge(vp, on='sid', how='left')
    e['mv'] = e.mv.fillna(0); e['vp'] = e.vp.fillna(0)
    e['cr_base_f'] = pd.to_numeric(e.cr_base, errors='coerce')
    e['cr_missing'] = e.cr_base_f.isna().astype(int)
    e['cr_base_f'] = e.cr_base_f.fillna(e.cr_base_f.median() if e.cr_base_f.notna().any() else 1.0)
    e['k_idx_f'] = pd.to_numeric(e.k_idx, errors='coerce').fillna(5.4)
    e['age_f'] = pd.to_numeric(e.age, errors='coerce').fillna(e.age.median())
    e['sex_m'] = (e.sex.astype(str).str.upper().str[0] == 'M').astype(int)
    for g in GROUPS:
        e['g_' + g] = (e.grp == g).astype(int)
    sub = e[(e.los_hosp_min > H) & (e.grp != 'unclassified')].copy()

    print('\n=== %s  72 h landmark（n=%s）' % (nm, f'{len(sub):,}'))
    print('  [A] 原模型（索引值/年龄/性别），医院聚类 bootstrap：')
    f1 = ['g_transient', 'g_intermittent', 'g_sustained', 'k_idx_f', 'age_f', 'sex_m']
    o1, n1 = fit(sub, f1, cluster=(sub.hosp.values if nm == 'eICU-CRD' else None))
    for g in GROUPS:
        print('     %-14s %.2f (%.2f–%.2f)' % (g, o1['g_' + g][0], o1['g_' + g][1], o1['g_' + g][2]))
        rows_c.append(dict(db=nm, group=g, or_=o1['g_' + g][0], lo=o1['g_' + g][1], hi=o1['g_' + g][2],
                           bootstrap='hospital-clustered' if nm == 'eICU-CRD' else 'simple',
                           n_boot=n1, n=len(sub)))
    print('  [B] 加严重度（+肌酐/机械通气/升压药）：')
    f2 = f1 + ['cr_base_f', 'mv', 'vp']
    o2, n2 = fit(sub, f2, cluster=(sub.hosp.values if nm == 'eICU-CRD' else None))
    for g in GROUPS:
        print('     %-14s %.2f (%.2f–%.2f)' % (g, o2['g_' + g][0], o2['g_' + g][1], o2['g_' + g][2]))
        rows_a.append(dict(db=nm, group=g, or_=o2['g_' + g][0], lo=o2['g_' + g][1], hi=o2['g_' + g][2],
                           cov_mv=round(100 * float(sub.mv.mean()), 1), cov_vp=round(100 * float(sub.vp.mean()), 1),
                           cov_cr=round(100 * float(1 - sub.cr_missing.mean()), 1), n=len(sub)))
    for v in ['cr_base_f', 'mv', 'vp']:
        print('     %-14s %.2f (%.2f–%.2f)' % (v, o2[v][0], o2[v][1], o2[v][2]))

pd.DataFrame(rows_c).to_csv('out/k43_cluster.csv', index=False, encoding='utf-8-sig')
pd.DataFrame(rows_a).to_csv('out/k43_adj.csv', index=False, encoding='utf-8-sig')
print('\n写出 out/k43_cluster.csv / k43_adj.csv')
