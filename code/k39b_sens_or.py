# -*- coding: utf-8 -*-
"""只重算 sustained 测量次数敏感性（≥2 次 / ≥3 次）的完整 OR 与 CI。
用法：python k39b_sens_or.py <MIMIC|eICU>
纪律：并行列表一律 assert len(a)==len(b)，并打印变量名与系数。
"""
import duckdb, pandas as pd, numpy as np, json, sys, warnings
from sklearn.linear_model import LogisticRegression
warnings.filterwarnings('ignore')

WHICH = sys.argv[1] if len(sys.argv) > 1 else 'MIMIC'
M = 'D:/shujuku/mimic-iv-3.1'; E = 'D:/shujuku/EICU 2.0'
T = lambda p: "read_csv_auto('{}', strict_mode=false, ignore_errors=true)".format(p)
con = duckdb.connect(); con.execute('SET threads=4')
BASE = 1440
CIC = "regexp_matches(first_careunit,'CCU|CVICU')"
CIT = "regexp_matches(unittype,'Cardiac ICU|CCU|CSICU|CTICU')"

if WHICH == 'MIMIC':
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
GROUPS = ['transient', 'intermittent', 'conf_not_assessed', 'sustained']


def build(H, minm):
    rows = []
    for sid, g in d.groupby('sid', sort=False):
        pre = g[g.t <= BASE]
        if len(pre) == 0 or float(pre.k.max()) >= 5.5: continue
        post = g[(g.t > BASE) & (g.t <= H)]
        if len(post) == 0: continue
        pos = post[post.k >= 5.5]
        if len(pos) == 0:
            rows.append(dict(sid=int(sid), grp='no_event', k_idx=np.nan)); continue
        idx = pos.iloc[0]
        a = post[(post.t > idx.t) & (post.t <= idx.t + BASE)]
        n = len(a)
        if n == 0: grp = 'unclassified'
        elif bool((a.k >= 5.5).all()): grp = 'sustained' if n >= minm else 'conf_not_assessed'
        elif bool((a.k >= 5.5).any()): grp = 'intermittent'
        else: grp = 'transient'
        rows.append(dict(sid=int(sid), grp=grp, k_idx=float(idx.k)))
    return pd.DataFrame(rows)


def regress(sub, seed=3, nb=400):
    sub = sub.copy()
    names = ['g_' + g for g in GROUPS]
    assert len(GROUPS) == len(names), 'groups/names 长度不一致'
    for g, c in zip(GROUPS, names):
        sub[c] = (sub.grp == g).astype(int)
    sub['k_idx_f'] = pd.to_numeric(sub.k_idx, errors='coerce').fillna(5.4)
    sub['age_f'] = pd.to_numeric(sub.age, errors='coerce').fillna(sub.age.median())
    sub['sex_m'] = (sub.sex.astype(str).str.upper().str[0] == 'M').astype(int)
    feats = names + ['k_idx_f', 'age_f', 'sex_m']
    X = sub[feats].astype(float).values; y = sub.died_inhosp.astype(int).values
    m = LogisticRegression(max_iter=4000).fit(X, y); coef = m.coef_[0]
    assert len(feats) == len(coef), 'feats/coef 长度不一致'
    print('   [%s] 变量与系数：%s' % (WHICH, ' | '.join('%s %.3f' % (f, c) for f, c in zip(feats, coef))))
    rng = np.random.default_rng(seed); bs = []
    for _ in range(nb):
        i = rng.integers(0, len(y), len(y))
        if len(np.unique(y[i])) < 2: continue
        try:
            b = LogisticRegression(max_iter=4000).fit(X[i], y[i]).coef_[0]
            assert len(b) == len(feats)
            bs.append(b)
        except Exception:
            pass
    bs = np.array(bs)
    res = {}
    for j, nm_ in enumerate(names):
        ci = np.exp(np.percentile(bs[:, j], [2.5, 97.5]))
        res[nm_[2:]] = dict(or_=round(float(np.exp(coef[j])), 2), lo=round(float(ci[0]), 2), hi=round(float(ci[1]), 2))
    assert not any(np.isnan(v['lo']) for v in res.values()), 'CI 计算失败'
    return res


OUT = {}
for minm, tag in [(2, 'sust>=2'), (3, 'sust>=3')]:
    E5 = build(10080, minm)          # 先用 7 天 landmark 建一次（覆盖全部需要的人）
    E5_72 = build(4320, minm)
    for H, lab, base in [(4320, '72 h', E5_72), (10080, '7 d', E5)]:
        coh = base.merge(oc, on='sid', how='left')
        lmk = coh[(coh.los_hosp_min > H) & (coh.grp != 'unclassified')]
        print('  %s %s landmark n=%s' % (tag, lab, format(len(lmk), ',')))
        OUT['%s|%s|%s' % (tag, WHICH if WHICH == 'MIMIC' else 'eICU-CRD', lab)] = regress(lmk)

fn = 'out/k39b_sens_%s.json' % WHICH.lower()
json.dump(OUT, open(fn, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('写出', fn)
