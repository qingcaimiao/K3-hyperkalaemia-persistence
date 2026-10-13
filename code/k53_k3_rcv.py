# -*- coding: utf-8 -*-
"""K3 第四轮审计：统一 RCV 敏感性到主分析（表 5）队列口径，并复核 4.60/4.70、landmark 覆盖率。
产出 out/k53_k3_audit.csv
"""
import duckdb, pandas as pd, numpy as np, json, sys, warnings
from sklearn.linear_model import LogisticRegression
warnings.filterwarnings('ignore')
W = sys.argv[1] if len(sys.argv) > 1 else 'MIMIC'
DB = 'MIMIC-IV' if W == 'MIMIC' else 'eICU-CRD'
M = 'D:/shujuku/mimic-iv-3.1'; E = 'D:/shujuku/EICU 2.0'
T = lambda p: "read_csv_auto('{}', strict_mode=false, ignore_errors=true)".format(p)
con = duckdb.connect(); con.execute('SET threads=4')
BASE = 1440; H = 4320
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
    ser = 'out/k3_k_series_mimic.pkl'; evf = 'out/k3_events_mimic.pkl'
else:
    q = f"""SELECT patientunitstayid AS sid, TRY_CAST(hospitaldischargeoffset AS DOUBLE) AS los_hosp_min,
       CASE WHEN lower(coalesce(hospitaldischargestatus,'')) LIKE 'expired%' THEN 1 ELSE 0 END AS died_inhosp,
       gender AS sex, TRY_CAST(age AS DOUBLE) AS age FROM {T(E + '/patient.csv')} WHERE {CIT}"""
    ser = 'out/k3_k_series_eicu.pkl'; evf = 'out/k3_events_eicu.pkl'
oc = con.execute(q).df()
d = pd.read_pickle(ser).sort_values(['sid', 't']).reset_index(drop=True)
med = d.groupby('sid').k.median()
GROUPS = ['transient', 'intermittent', 'sustained']
ph = json.load(open('out/k3_phase2c.json', encoding='utf-8'))
p1 = json.load(open('out/k3_phase1.json', encoding='utf-8'))
RCV = float(p1[DB]['rcv'])
OUT = []


def build(full=False, landmark=H):
    rows = []
    for sid, g in d.groupby('sid', sort=False):
        pre = g[g.t <= BASE]
        if len(pre) == 0 or float(pre.k.max()) >= 5.5:
            continue
        post = g[g.t > BASE] if full else g[(g.t > BASE) & (g.t <= landmark)]
        if len(post) == 0:
            continue
        pos = post[post.k >= 5.5]
        base = dict(sid=int(sid), k_med=float(med.get(sid, np.nan)))
        if len(pos) == 0:
            rows.append(dict(base, grp='no_event', k_idx=np.nan)); continue
        idx = pos.iloc[0]
        a = post[(post.t > idx.t) & (post.t <= idx.t + BASE)]
        n = len(a); nge = int((a.k >= 5.5).sum())
        grp = ('unclassified' if n == 0 else
               ('sustained' if nge == n else ('intermittent' if nge > 0 else 'transient')))
        rows.append(dict(base, grp=grp, k_idx=float(idx.k)))
    return pd.DataFrame(rows)


def regress(sub, seed=3, nb=400):
    sub = sub.copy(); names = ['g_' + g for g in GROUPS]
    assert int((sub.grp == 'no_event').sum()) >= 50, '缺参照组'
    for g, c in zip(GROUPS, names):
        sub[c] = (sub.grp == g).astype(int)
    sub['k_idx_f'] = pd.to_numeric(sub.k_idx, errors='coerce').fillna(5.4)
    sub['age_f'] = pd.to_numeric(sub.age, errors='coerce').fillna(sub.age.median())
    sub['sex_m'] = (sub.sex.astype(str).str.upper().str[0] == 'M').astype(int)
    feats = names + ['k_idx_f', 'age_f', 'sex_m']
    X = sub[feats].astype(float).values; y = sub.died_inhosp.astype(int).values
    if len(np.unique(y)) < 2 or len(sub) < 60:
        return {}
    coef = LogisticRegression(max_iter=4000).fit(X, y).coef_[0]
    rng = np.random.default_rng(seed); bs = []
    for _ in range(nb):
        i = rng.integers(0, len(y), len(y))
        if len(np.unique(y[i])) < 2:
            continue
        try:
            bs.append(LogisticRegression(max_iter=4000).fit(X[i], y[i]).coef_[0])
        except Exception:
            pass
    bs = np.array(bs); out = {}
    for j, nm in enumerate(GROUPS):
        ci = np.exp(np.percentile(bs[:, j], [2.5, 97.5])) if len(bs) > 50 else [np.nan]*2
        out[nm] = (round(float(np.exp(coef[j])), 2), round(float(ci[0]), 2), round(float(ci[1]), 2))
    return out


print('==========', DB, '| RCV =', RCV)
# ---------- 1. 全队列 beyond_pct（复现 Table 3） ----------
call = build(full=True).merge(oc, on='sid', how='left')
app_all = call[call.grp != 'no_event'].copy()
b_all = (pd.to_numeric(app_all.k_idx, errors='coerce') > app_all.k_med + RCV)
OUT.append(dict(db=DB, metric='beyond_pct_whole_cohort', n=int(len(app_all)),
                k=int(b_all.sum()), pct=round(100*float(b_all.mean()), 1)))
print('[1] 全队列 apparent %d 例；超过本人中位+RCV %d 例 (%.1f%%)' %
      (len(app_all), b_all.sum(), 100*b_all.mean()))

# ---------- 2. 表 5 队列（72h landmark）内的 beyond_pct ----------
cl = build(full=False).merge(oc, on='sid', how='left')
cl['los_hosp_min'] = pd.to_numeric(cl.los_hosp_min, errors='coerce')
cl = cl[cl.los_hosp_min > H].copy()
dist = dict(cl.grp.value_counts())
print('[2] 表5队列 %d：%s' % (len(cl), dist))
assert dist.get('no_event') == (17585 if W == 'MIMIC' else 22602), '与表 5 口径不符'
ev = cl[cl.grp != 'no_event'].copy()
b_lm = (pd.to_numeric(ev.k_idx, errors='coerce') > ev.k_med + RCV)
OUT.append(dict(db=DB, metric='beyond_pct_landmark_cohort', n=int(len(ev)),
                k=int(b_lm.sum()), pct=round(100*float(b_lm.mean()), 1)))
print('[2] 表5队列事件 %d 例；超过本人中位+RCV %d 例 (%.1f%%)' %
      (len(ev), b_lm.sum(), 100*b_lm.mean()))

# ---------- 3. RCV 限制后的 OR（表 5 队列口径） ----------
sub = cl[cl.grp != 'unclassified'].copy()
sub['beyond'] = (pd.to_numeric(sub.k_idx, errors='coerce') > sub.k_med + RCV)
s2 = sub[(sub.grp == 'no_event') | sub.beyond]
assert (s2.grp == 'no_event').sum() == (cl.grp == 'no_event').sum(), '参照组被误删'
r = regress(s2)
print('[3] RCV 限制后（表5队列）OR:', r)
for g in GROUPS:
    OUT.append(dict(db=DB, metric='OR_rcv_restricted_' + g, n=None, k=None,
                    pct=None, or_=r[g][0], lo=r[g][1], hi=r[g][2]))
# 主分析 OR 复核
rm = regress(sub)
print('[3b] 主分析 OR 复核:', rm)

# ---------- 4. 复查 / 回落中位 ----------
evt = pd.read_pickle(evf); rem = evt[evt.k_next.notna()]; rev = rem[rem.k_next < 5.5]
OUT.append(dict(db=DB, metric='median_repeat_all_remeasured', n=int(len(rem)), pct=None,
                or_=round(float(rem.k_next.median()), 2)))
OUT.append(dict(db=DB, metric='median_repeat_reverted_only', n=int(len(rev)), pct=None,
                or_=round(float(rev.k_next.median()), 2)))
print('[4] 被复查 %d，中位 %.2f；回落者 %d，中位 %.2f' %
      (len(rem), rem.k_next.median(), len(rev), rev.k_next.median()))

# ---------- 5. landmark 覆盖率 ----------
OUT.append(dict(db=DB, metric='landmark72_retention_pct', n=int(len(cl)), k=int(len(call)),
                pct=round(100 * len(cl) / len(call), 1)))
OUT.append(dict(db=DB, metric='landmark7d_retention_pct', n=None, k=None, pct=None))
print('[5] 72h landmark 保留 %d/%d = %.1f%%' % (len(cl), len(call), 100*len(cl)/len(call)))

pd.DataFrame(OUT).to_csv('out/k53_audit_%s.csv' % W.lower(), index=False)
print('已写 out/k53_audit_%s.csv' % W.lower())
