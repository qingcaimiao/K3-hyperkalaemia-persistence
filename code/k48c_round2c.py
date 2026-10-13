# -*- coding: utf-8 -*-
"""K3 第二轮 [1]-[4] 干净重跑：截断分层 / RCV 亚组 / 复测次数分布 / 竞争事件"""
import duckdb, pandas as pd, numpy as np, json, sys, warnings
from sklearn.linear_model import LogisticRegression
warnings.filterwarnings('ignore')
W = sys.argv[1] if len(sys.argv) > 1 else 'MIMIC'
DB = 'MIMIC-IV' if W == 'MIMIC' else 'eICU-CRD'
M = 'D:/shujuku/mimic-iv-3.1'; E = 'D:/shujuku/EICU 2.0'
T = lambda p: "read_csv_auto('{}', strict_mode=false, ignore_errors=true)".format(p)
con = duckdb.connect(); con.execute('SET threads=4')
BASE = 1440
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
med = d.groupby('sid').k.median()
GROUPS = ['transient', 'intermittent', 'sustained']
RES = {}


def build(H):
    rows = []
    for sid, g in d.groupby('sid', sort=False):
        pre = g[g.t <= BASE]
        if len(pre) == 0 or float(pre.k.max()) >= 5.5: continue
        post = g[(g.t > BASE) & (g.t <= H)]
        if len(post) == 0: continue
        pos = post[post.k >= 5.5]
        if len(pos) == 0:
            rows.append(dict(sid=int(sid), grp='no_event', k_idx=np.nan, n_after=0,
                             complete=-1, k_med=float(med.get(sid, np.nan)))); continue
        idx = pos.iloc[0]; a = post[(post.t > idx.t) & (post.t <= idx.t + BASE)]
        n = len(a)
        grp = 'unclassified' if n == 0 else ('sustained' if bool((a.k >= 5.5).all())
                                             else ('intermittent' if bool((a.k >= 5.5).any()) else 'transient'))
        rows.append(dict(sid=int(sid), grp=grp, k_idx=float(idx.k), n_after=int(n),
                         complete=int(idx.t + BASE <= H), k_med=float(med.get(sid, np.nan))))
    return pd.DataFrame(rows)


def regress(sub, seed=3, nb=400):
    sub = sub.copy(); names = ['g_' + g for g in GROUPS]
    _n0 = int((sub.grp == 'no_event').sum())
    assert _n0 >= 50, '回归缺少参照组（no_event 仅 %d 例）' % _n0
    assert len(GROUPS) == len(names)
    for g, c in zip(GROUPS, names): sub[c] = (sub.grp == g).astype(int)
    sub['k_idx_f'] = pd.to_numeric(sub.k_idx, errors='coerce').fillna(5.4)
    sub['age_f'] = pd.to_numeric(sub.age, errors='coerce').fillna(sub.age.median())
    sub['sex_m'] = (sub.sex.astype(str).str.upper().str[0] == 'M').astype(int)
    feats = names + ['k_idx_f', 'age_f', 'sex_m']
    X = sub[feats].astype(float).values; y = sub.died_inhosp.astype(int).values
    if len(np.unique(y)) < 2 or len(sub) < 60: return {}
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


for H, lab in [(4320, '72 h'), (10080, '7 d')]:
    c = build(H).merge(oc, on='sid', how='left')
    lmk = c[c.los_hosp_min > H].copy()
    ev_ = lmk[lmk.grp != 'no_event']
    comp = ev_[ev_.complete == 1]; trunc = ev_[ev_.complete == 0]
    print('\n=== [1] %s %s：事件 %d，完整 %d / 截断 %d' % (DB, lab, len(ev_), len(comp), len(trunc)))
    d1 = {}
    for g in GROUPS + ['unclassified']:
        nc, nt = int((comp.grp == g).sum()), int((trunc.grp == g).sum())
        print('   %-14s 完整 %4d (%.1f%%) | 截断 %4d (%.1f%%)' % (
            g, nc, 100 * nc / max(len(comp), 1), nt, 100 * nt / max(len(trunc), 1)))
        d1['complete_' + g] = nc; d1['trunc_' + g] = nt
    d1.update(n_complete=int(len(comp)), n_truncated=int(len(trunc)),
              mort_complete=round(100 * float(comp.died_inhosp.mean()), 1),
              mort_trunc=round(100 * float(trunc.died_inhosp.mean()), 1),
              kidx_complete=round(float(pd.to_numeric(comp.k_idx, errors='coerce').median()), 2),
              kidx_trunc=round(float(pd.to_numeric(trunc.k_idx, errors='coerce').median()), 2))
    print('   基线K中位 %.2f/%.2f；死亡率 %.1f%%/%.1f%%' % (d1['kidx_complete'], d1['kidx_trunc'],
                                                       d1['mort_complete'], d1['mort_trunc']))
    RES['1_dist|' + lab] = d1
    subA = lmk[(lmk.grp == 'no_event') | ((lmk.grp != 'unclassified') & (lmk.complete == 1))]
    assert (subA.grp == 'no_event').sum() == (lmk.grp == 'no_event').sum(), '参照组被误删'
    RES['1_complete_only|' + lab] = regress(subA)
    l2 = lmk.copy(); l2.loc[l2.complete == 0, 'grp'] = 'unclassified'
    RES['1_trunc_as_unc|' + lab] = regress(l2[l2.grp != 'unclassified'])
    print('   仅完整窗 OR:', {k: (v['or_'], v['lo'], v['hi']) for k, v in RES['1_complete_only|' + lab].items()})
    print('   截断归未分类 OR:', {k: (v['or_'], v['lo'], v['hi']) for k, v in RES['1_trunc_as_unc|' + lab].items()})
    if H == 10080:
        c_whole = c

# [2] RCV
RCV = 1.14 if W == 'MIMIC' else 1.07
_all = c_whole[c_whole.los_hosp_min > 4320].copy()
app = _all[_all.grp != 'no_event'].copy()
app['beyond'] = (pd.to_numeric(app.k_idx, errors='coerce') > app.k_med + RCV).astype(int)
RES['2_share'] = dict(n=int(len(app)), k=int(app.beyond.sum()), pct=round(100 * float(app.beyond.mean()), 1))
print('\n=== [2] %s 72 h：index > 本人中位+RCV %d/%d (%.1f%%)' % (DB, app.beyond.sum(), len(app), 100 * app.beyond.mean()))
# 参照组保留全部 no_event；仅对事件组施加 RCV 限制
sb = _all[(_all.grp == 'no_event') | ((_all.grp != 'unclassified') & (_all.sid.isin(app[app.beyond == 1].sid)))]
assert (sb.grp == 'no_event').sum() == (_all.grp == 'no_event').sum(), '参照组被误删'
RES['2_only'] = regress(sb)
print('   该亚组 OR:', {k: (v['or_'], v['lo'], v['hi']) for k, v in RES['2_only'].items()})

# [3] 复测次数
print('\n=== [3] %s 各状态复测次数（全队列）' % DB)
D3 = {}
for g in GROUPS:
    s = c_whole[c_whole.grp == g]
    if not len(s): continue
    D3[g] = dict(n=int(len(s)), median=float(s.n_after.median()),
                 q1=float(s.n_after.quantile(.25)), q3=float(s.n_after.quantile(.75)),
                 n_one=int((s.n_after == 1).sum()),
                 pct_one=round(100 * float((s.n_after == 1).mean()), 1))
    print('   %-14s n=%4d 中位 %.1f (IQR %.0f–%.0f) | 仅 1 次 %d (%.1f%%)' % (
        g, D3[g]['n'], D3[g]['median'], D3[g]['q1'], D3[g]['q3'], D3[g]['n_one'], D3[g]['pct_one']))
RES['3_dist'] = D3

# [4] 竞争事件
l72 = c_whole[c_whole.los_hosp_min > 4320]
died = int(l72.died_inhosp.sum()); alive = len(l72) - died
print('\n=== [4] %s 72 h landmark：死亡 %d / 存活出院 %d (%.1f%% / %.1f%%)' % (
    DB, died, alive, 100 * died / len(l72), 100 * alive / len(l72)))
RES['4_compete'] = dict(n=len(l72), died=died, alive=alive)
late = l72[l72.los_hosp_min > 4320 + 2880]
RES['4_excl48'] = regress(late[late.grp != 'unclassified'])
print('   排除 48h 内出院后 n=%d：%s' % (
    len(late[late.grp != 'unclassified']),
    {k: (v['or_'], v['lo'], v['hi']) for k, v in RES['4_excl48'].items()}))

json.dump(RES, open('out/k48c_%s.json' % W.lower(), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n写出 out/k48c_%s.json' % W.lower())
