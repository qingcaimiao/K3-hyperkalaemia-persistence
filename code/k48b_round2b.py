# -*- coding: utf-8 -*-
"""K3 第二轮补充（[5] 聚类比例 CI、[6] E-value、[7] RRT、[8] 治疗分层完整 OR）"""
import pandas as pd, numpy as np, json, sys, warnings
from sklearn.linear_model import LogisticRegression
import duckdb
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
    ser = 'out/k3_k_series_mimic.pkl'; txp = 'out/k3_events_tx_m.pkl'; kind = 'mimic'
else:
    q = f"""SELECT patientunitstayid AS sid, hospitalid AS hosp,
       TRY_CAST(hospitaldischargeoffset AS DOUBLE) AS los_hosp_min,
       CASE WHEN lower(coalesce(hospitaldischargestatus,'')) LIKE 'expired%' THEN 1 ELSE 0 END AS died_inhosp,
       gender AS sex, TRY_CAST(age AS DOUBLE) AS age FROM {T(E + '/patient.csv')} WHERE {CIT}"""
    ser = 'out/k3_k_series_eicu.pkl'; txp = 'out/k3_events_tx_e.pkl'; kind = 'eicu'
oc = con.execute(q).df()
d = pd.read_pickle(ser).sort_values(['sid', 't']).reset_index(drop=True)
ev = pd.read_pickle(txp)
GROUPS = ['transient', 'intermittent', 'sustained']
RES = {}


def build(Hh):
    rows = []
    for sid, g in d.groupby('sid', sort=False):
        pre = g[g.t <= BASE]
        if len(pre) == 0 or float(pre.k.max()) >= 5.5: continue
        post = g[(g.t > BASE) & (g.t <= Hh)]
        if len(post) == 0: continue
        pos = post[post.k >= 5.5]
        if len(pos) == 0:
            rows.append(dict(sid=int(sid), grp='no_event', k_idx=np.nan)); continue
        idx = pos.iloc[0]; a = post[(post.t > idx.t) & (post.t <= idx.t + BASE)]
        n = len(a)
        grp = 'unclassified' if n == 0 else ('sustained' if bool((a.k >= 5.5).all())
                                             else ('intermittent' if bool((a.k >= 5.5).any()) else 'transient'))
        rows.append(dict(sid=int(sid), grp=grp, k_idx=float(idx.k)))
    return pd.DataFrame(rows)


def regress(sub, seed=3, nb=400):
    sub = sub.copy(); names = ['g_' + g for g in GROUPS]
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
                            hi=round(float(ci[1]), 2), n=int(len(sub)))
    return out


def prop_ci(vec, cluster=None, seed=3, nb=1000):
    v = np.asarray(vec, dtype=float); p = float(np.nanmean(v))
    if cluster is not None:
        rng = np.random.default_rng(seed); cl = np.asarray(cluster); uniq = np.unique(cl)
        bs = []
        for _ in range(nb):
            pk = rng.choice(uniq, len(uniq), replace=True)
            ix = np.concatenate([np.where(cl == c)[0] for c in pk])
            bs.append(float(np.nanmean(v[ix])) if len(ix) else np.nan)
        lo, hi = np.nanpercentile(bs, [2.5, 97.5])
    else:
        lo = hi = np.nan
    return round(100 * p, 1), round(100 * float(lo), 1), round(100 * float(hi), 1)


# [5] 聚类比例 CI
c = build(10080).merge(oc, on='sid', how='left')
cl = oc.set_index('sid').hosp if W == 'eICU' else None
print('=== [5] %s 比例与医院聚类 CI' % DB)
n_app = int((c.grp != 'no_event').sum())
p, lo, hi = prop_ci((c.grp != 'no_event').astype(int).values,
                    cluster=(cl.reindex(c.sid).values if cl is not None else None))
_cl_txt = '(医院聚类 CI %.1f–%.1f)' % (lo, hi) if W == 'eICU' else '（单中心，无聚类）'
print('   发病率 %d/%d = %.1f%% %s' % (n_app, len(c), p, _cl_txt))
RES['5_incidence'] = dict(k=n_app, n=len(c), pct=p, lo=lo, hi=hi)
ev0 = pd.read_pickle('out/k3_events_%s.pkl' % kind)
cl6 = cl.reindex(ev0.sid).values if cl is not None else None
p, lo, hi = prop_ci((ev0.t_next <= 360).astype(int).values, cluster=cl6)
print('   6 h 复查率 %d/%d = %.1f%% (CI %.1f–%.1f)' % ((ev0.t_next <= 360).sum(), len(ev0), p, lo, hi))
RES['5_recheck6'] = dict(k=int((ev0.t_next <= 360).sum()), n=len(ev0), pct=p, lo=lo, hi=hi)
p, lo, hi = prop_ci(ev0.confirm.astype(int).values, cluster=cl6)
print('   下一次测量确认率 %d/%d = %.1f%% (CI %.1f–%.1f)' % (ev0.confirm.sum(), len(ev0), p, lo, hi))
RES['5_confirm'] = dict(k=int(ev0.confirm.sum()), n=len(ev0), pct=p, lo=lo, hi=hi)
p, lo, hi = prop_ci(ev0.sustained.astype(int).values, cluster=cl6)
print('   持续率（占表观）%d/%d = %.1f%% (CI %.1f–%.1f)' % (ev0.sustained.sum(), len(ev0), p, lo, hi))
RES['5_sustained'] = dict(k=int(ev0.sustained.sum()), n=len(ev0), pct=p, lo=lo, hi=hi)

# [6] E-value
lmk = c[c.los_hosp_min > H]
base_p = float(lmk[lmk.grp == 'no_event'].died_inhosp.mean())
print('\n=== [6] %s 72 h 参照风险 %.4f' % (DB, base_p))


def evalue(orv, p0):
    o = orv if orv >= 1 else 1 / orv
    rr = o / (1 - p0 + p0 * o)
    return round(rr + np.sqrt(rr * (rr - 1)), 2)


ev_res = {}
a0 = float(lmk[lmk.grp == 'no_event'].died_inhosp.sum()); b0 = len(lmk[lmk.grp == 'no_event']) - a0
for g in GROUPS:
    s = lmk[lmk.grp == g]
    if not len(s): continue
    a = float(s.died_inhosp.sum()); b = len(s) - a
    orv = (a * b0) / max(b * a0, 1e-9)
    ev_res[g] = dict(crude_or=round(orv, 2), evalue=evalue(orv, base_p))
    print('   %-14s 粗OR %.2f → E-value %.2f' % (g, orv, ev_res[g]['evalue']))
RES['6_evalue'] = ev_res
RES['6_base_risk'] = round(base_p, 4)
RES['6_base_risk'] = round(base_p, 4)

# [7] RRT
print('\n=== [7] %s RRT' % DB)
n_rrt = int(ev.tx_rrt.sum())
print('   记录到 RRT %d/%d (%.1f%%)' % (n_rrt, len(ev), 100 * ev.tx_rrt.mean()))
RES['7_rrt'] = dict(n=len(ev), k=n_rrt, pct=round(100 * float(ev.tx_rrt.mean()), 1))
base = c[c.los_hosp_min > H].copy()          # 含 no_event
rrt_sids = set(ev[ev.tx_rrt == 1].sid.astype(int))
noRT = base[(base.grp == 'no_event') | ((base.grp != 'unclassified') & (~base.sid.isin(rrt_sids)))]
assert (noRT.grp == 'no_event').sum() == (base.grp == 'no_event').sum(), '参照组被误删'
RES['7_excl_rrt'] = regress(noRT)
print('   排除 RRT 事件后 n=%d：%s' % (len(noRT), {k: (v['or_'], v['lo'], v['hi']) for k, v in RES['7_excl_rrt'].items()}))

# [8] 治疗分层
txm = ev[['sid'] + ['tn_' + x for x in ['insulin_glucose', 'binder', 'iv_calcium', 'bicarbonate', 'rrt']]].copy()
txm['treated'] = txm[[x for x in txm.columns if x.startswith('tn_')]].any(axis=1).astype(int)
ap2 = base.merge(txm[['sid', 'treated']], on='sid', how='left')
ap2['treated'] = ap2.treated.fillna(0).astype(int); ap2.loc[ap2.grp == 'no_event', 'treated'] = -1
print('\n=== [8] %s 按治疗分层' % DB)
for tv in (0, 1):
    s = ap2[(ap2.treated == tv) | (ap2.grp == 'no_event')]
    s = s[s.grp != 'unclassified']
    assert (s.grp == 'no_event').sum() == (base.grp == 'no_event').sum(), '参照组被误删'
    RES['8_treated%d' % tv] = regress(s)
    print('   %s 事件 n=%d（参照 no_event %d）：%s' % (
        '有治疗' if tv else '无治疗', int((s.grp != 'no_event').sum()), int((s.grp == 'no_event').sum()),
        {k: (v['or_'], v['lo'], v['hi']) for k, v in RES['8_treated%d' % tv].items()}))

json.dump(RES, open('out/k48b_%s.json' % W.lower(), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n写出 out/k48b_%s.json' % W.lower())
