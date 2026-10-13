# -*- coding: utf-8 -*-
"""K3 对称暴露窗分析（回应"截断是否高估 sustained"）：
暴露窗对所有人统一为 (24h, 48h]，landmark 72h / 7d。左右两侧口径完全对称，不存在截断差异。
用法：python k49_k3_fixedwin.py <MIMIC|eICU>
"""
import duckdb, pandas as pd, numpy as np, json, sys, warnings
from sklearn.linear_model import LogisticRegression
warnings.filterwarnings('ignore')
W = sys.argv[1] if len(sys.argv) > 1 else 'MIMIC'
DB = 'MIMIC-IV' if W == 'MIMIC' else 'eICU-CRD'
M = 'D:/shujuku/mimic-iv-3.1'; E = 'D:/shujuku/EICU 2.0'
T = lambda p: "read_csv_auto('{}', strict_mode=false, ignore_errors=true)".format(p)
con = duckdb.connect(); con.execute('SET threads=4')
BASE = 1440; WIN_END = 2880          # 固定暴露窗 (24h, 48h]
CIC = "regexp_matches(first_careunit,'CCU|CVICU')"
CIT = "regexp_matches(unittype,'Cardiac ICU|CCU|CSICU|CTICU')"
if W == 'MIMIC':
    q = f"""WITH icu AS (SELECT stay_id, subject_id, hadm_id, intime,
             ROW_NUMBER() OVER (PARTITION BY hadm_id ORDER BY intime) AS rn
             FROM {T(M + '/icu/icustays.csv')} WHERE {CIC}), co AS (SELECT * FROM icu WHERE rn=1)
SELECT co.stay_id AS sid, DATE_DIFF('minute', co.intime, a.dischtime) AS los_hosp_min,
       a.hospital_expire_flag AS died_inhosp, p.gender AS sex,
       TRY_CAST(p.anchor_age AS DOUBLE)+GREATEST(TRY_CAST(EXTRACT(YEAR FROM co.intime) AS INT)-p.anchor_year,0) AS age
FROM co JOIN {T(M + '/hosp/admissions.csv')} a ON a.hadm_id=co.hadm_id
        JOIN {T(M + '/hosp/patients.csv')} p ON p.subject_id=co.subject_id"""
    ser = 'out/k3_k_series_mimic.pkl'
else:
    q = f"""SELECT patientunitstayid AS sid, TRY_CAST(hospitaldischargeoffset AS DOUBLE) AS los_hosp_min,
       CASE WHEN lower(coalesce(hospitaldischargestatus,'')) LIKE 'expired%' THEN 1 ELSE 0 END AS died_inhosp,
       gender AS sex, TRY_CAST(age AS DOUBLE) AS age FROM {T(E + '/patient.csv')} WHERE {CIT}"""
    ser = 'out/k3_k_series_eicu.pkl'
oc = con.execute(q).df()
d = pd.read_pickle(ser).sort_values(['sid', 't']).reset_index(drop=True)
GROUPS = ['transient', 'intermittent', 'sustained']


def build():
    rows = []
    for sid, g in d.groupby('sid', sort=False):
        pre = g[g.t <= BASE]
        if len(pre) == 0 or float(pre.k.max()) >= 5.5: continue
        w = g[(g.t > BASE) & (g.t <= WIN_END)]          # 固定窗，人人相同
        if len(w) == 0: continue                        # 窗内无测量 → 不入组
        pos = w[w.k >= 5.5]
        if len(pos) == 0:
            rows.append(dict(sid=int(sid), grp='no_event', k_idx=np.nan, n_after=0)); continue
        idx = pos.iloc[0]
        a = w[w.t > idx.t]
        n = len(a)
        if n == 0: grp = 'unclassified'
        elif bool((a.k >= 5.5).all()): grp = 'sustained'
        elif bool((a.k >= 5.5).any()): grp = 'intermittent'
        else: grp = 'transient'
        rows.append(dict(sid=int(sid), grp=grp, k_idx=float(idx.k), n_after=int(n)))
    return pd.DataFrame(rows)


def regress(sub, seed=3, nb=400):
    sub = sub.copy()
    names = ['g_' + g for g in GROUPS]
    assert len(GROUPS) == len(names)
    for g, c in zip(GROUPS, names):
        sub[c] = (sub.grp == g).astype(int)
    sub['k_idx_f'] = pd.to_numeric(sub.k_idx, errors='coerce').fillna(5.4)
    sub['age_f'] = pd.to_numeric(sub.age, errors='coerce').fillna(sub.age.median())
    sub['sex_m'] = (sub.sex.astype(str).str.upper().str[0] == 'M').astype(int)
    feats = names + ['k_idx_f', 'age_f', 'sex_m']
    X = sub[feats].astype(float).values; y = sub.died_inhosp.astype(int).values
    m = LogisticRegression(max_iter=4000).fit(X, y); coef = m.coef_[0]
    assert len(feats) == len(coef)
    rng = np.random.default_rng(seed); bs = []
    for _ in range(nb):
        i = rng.integers(0, len(y), len(y))
        if len(np.unique(y[i])) < 2: continue
        try:
            b = LogisticRegression(max_iter=4000).fit(X[i], y[i]).coef_[0]
            assert len(b) == len(feats); bs.append(b)
        except Exception: pass
    bs = np.array(bs); out = {}
    for j, nm_ in enumerate(names):
        ci = np.exp(np.percentile(bs[:, j], [2.5, 97.5]))
        out[nm_[2:]] = dict(or_=round(float(np.exp(coef[j])), 2), lo=round(float(ci[0]), 2),
                            hi=round(float(ci[1]), 2))
    return out


c = build().merge(oc, on='sid', how='left')
RES = {}
for H, lab in [(4320, '72 h'), (10080, '7 d')]:
    lmk = c[c.los_hosp_min > H]
    print('\n=== %s 固定暴露窗 (24h,48h]，%s landmark，n=%s' % (DB, lab, format(len(lmk), ',')))
    for g in ['no_event'] + GROUPS + ['unclassified']:
        s = lmk[lmk.grp == g]
        if not len(s): continue
        print('   %-14s n=%5s 死亡 %5.1f%%' % (g, format(len(s), ','), 100 * s.died_inhosp.mean()))
    sub = lmk[lmk.grp != 'unclassified']
    RES[lab] = regress(sub)
    print('   OR:', {k: (v['or_'], v['lo'], v['hi']) for k, v in RES[lab].items()})
    RES[lab + '_n'] = dict(n=int(len(lmk)), no_event=int((lmk.grp == 'no_event').sum()),
                           transient=int((lmk.grp == 'transient').sum()),
                           intermittent=int((lmk.grp == 'intermittent').sum()),
                           sustained=int((lmk.grp == 'sustained').sum()),
                           unclassified=int((lmk.grp == 'unclassified').sum()),
                           mort_no_event=round(100 * float(lmk[lmk.grp == 'no_event'].died_inhosp.mean()), 1),
                           mort_transient=round(100 * float(lmk[lmk.grp == 'transient'].died_inhosp.mean()), 1) if (lmk.grp == 'transient').any() else None,
                           mort_intermittent=round(100 * float(lmk[lmk.grp == 'intermittent'].died_inhosp.mean()), 1) if (lmk.grp == 'intermittent').any() else None,
                           mort_sustained=round(100 * float(lmk[lmk.grp == 'sustained'].died_inhosp.mean()), 1) if (lmk.grp == 'sustained').any() else None)
json.dump(RES, open('out/k49_fixedwin_%s.json' % W.lower(), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('\n写出 out/k49_fixedwin_%s.json' % W.lower())
