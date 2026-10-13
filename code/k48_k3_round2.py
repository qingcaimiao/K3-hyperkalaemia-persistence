# -*- coding: utf-8 -*-
"""K3 第二轮外审：截断敏感性 · index>median+RCV · 测量次数分布 · 竞争事件 · 聚类比例CI · E-value · 透析 · 治疗分层
用法：python k48_k3_round2.py <MIMIC|eICU>
纪律：并行列表一律 assert len(a)==len(b)；所有数字现算落盘。
"""
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
    ser = 'out/k3_k_series_mimic.pkl'; txp = 'out/k3_events_tx_m.pkl'
else:
    q = f"""SELECT patientunitstayid AS sid, hospitalid AS hosp,
       TRY_CAST(hospitaldischargeoffset AS DOUBLE) AS los_hosp_min,
       CASE WHEN lower(coalesce(hospitaldischargestatus,'')) LIKE 'expired%' THEN 1 ELSE 0 END AS died_inhosp,
       gender AS sex, TRY_CAST(age AS DOUBLE) AS age FROM {T(E + '/patient.csv')} WHERE {CIT}"""
    ser = 'out/k3_k_series_eicu.pkl'; txp = 'out/k3_events_tx_e.pkl'
oc = con.execute(q).df()
d = pd.read_pickle(ser).sort_values(['sid', 't']).reset_index(drop=True)
ev = pd.read_pickle(txp)
med = d.groupby('sid').k.median().rename('k_med')
GROUPS = ['transient', 'intermittent', 'sustained']
RES = {}


def classify(H):
    """五档 + 分类窗完整性 + index 是否超过本人 median+RCV。RCV 取各自库全样本值。"""
    rows = []
    for sid, g in d.groupby('sid', sort=False):
        pre = g[g.t <= BASE]
        if len(pre) == 0 or float(pre.k.max()) >= 5.5: continue
        post = g[(g.t > BASE) & (g.t <= H)]
        if len(post) == 0: continue
        pos = post[post.k >= 5.5]
        if len(pos) == 0:
            rows.append(dict(sid=int(sid), grp='no_event', k_idx=np.nan, n_after=0,
                             complete=np.nan, beyond=np.nan)); continue
        idx = pos.iloc[0]
        a = post[(post.t > idx.t) & (post.t <= idx.t + BASE)]
        n = len(a)
        if n == 0: grp = 'unclassified'
        elif bool((a.k >= 5.5).all()): grp = 'sustained'
        elif bool((a.k >= 5.5).any()): grp = 'intermittent'
        else: grp = 'transient'
        rows.append(dict(sid=int(sid), grp=grp, k_idx=float(idx.k), n_after=int(n),
                         complete=int(idx.t + BASE <= H), beyond=np.nan))
    return pd.DataFrame(rows)


def regress(sub, groups=GROUPS, seed=3, nb=400, cluster=None):
    sub = sub.copy()
    names = ['g_' + g for g in groups]
    assert len(groups) == len(names)
    for g, c in zip(groups, names):
        sub[c] = (sub.grp == g).astype(int)
    sub['k_idx_f'] = pd.to_numeric(sub.k_idx, errors='coerce').fillna(5.4)
    sub['age_f'] = pd.to_numeric(sub.age, errors='coerce').fillna(sub.age.median())
    sub['sex_m'] = (sub.sex.astype(str).str.upper().str[0] == 'M').astype(int)
    feats = names + ['k_idx_f', 'age_f', 'sex_m']
    X = sub[feats].astype(float).values; y = sub.died_inhosp.astype(int).values
    if len(np.unique(y)) < 2 or len(sub) < 60: return {}
    m = LogisticRegression(max_iter=4000).fit(X, y); coef = m.coef_[0]
    assert len(feats) == len(coef), 'feats/coef 长度不一致'
    rng = np.random.default_rng(seed); bs = []
    if cluster is None:
        for _ in range(nb):
            i = rng.integers(0, len(y), len(y))
            if len(np.unique(y[i])) < 2: continue
            try:
                b = LogisticRegression(max_iter=4000).fit(X[i], y[i]).coef_[0]
                assert len(b) == len(feats); bs.append(b)
            except Exception: pass
    else:
        cl = np.asarray(cluster); uniq = np.unique(cl)
        for _ in range(nb):
            pk = rng.choice(uniq, len(uniq), replace=True)
            ix = np.concatenate([np.where(cl == c)[0] for c in pk])
            if len(np.unique(y[ix])) < 2: continue
            try:
                b = LogisticRegression(max_iter=4000).fit(X[ix], y[ix]).coef_[0]
                assert len(b) == len(feats); bs.append(b)
            except Exception: pass
    bs = np.array(bs); out = {}
    for j, nm_ in enumerate(names):
        ci = np.exp(np.percentile(bs[:, j], [2.5, 97.5])) if len(bs) > 50 else [np.nan, np.nan]
        out[nm_[2:]] = dict(or_=round(float(np.exp(coef[j])), 2), lo=round(float(ci[0]), 2),
                            hi=round(float(ci[1]), 2), n=int(len(sub)),
                            n_event=int(y.sum()))
    return out


def evalue(orv, p0):
    """E-value for an odds ratio, converting to an approximate RR (Rothman)."""
    if not np.isfinite(orv) or orv <= 0: return np.nan
    o = orv if orv >= 1 else 1 / orv
    rr = o / (1 - p0 + p0 * o)
    return round(rr + np.sqrt(rr * (rr - 1)), 2)


def prop_ci(x, n, cluster=None, seed=3, nb=1000):
    p = x / n if n else np.nan
    if cluster is not None and len(cluster) > 50:
        rng = np.random.default_rng(seed); cl = np.asarray(cluster); uniq = np.unique(cl)
        bs = []
        for _ in range(nb):
            pk = rng.choice(uniq, len(uniq), replace=True)
            ix = np.concatenate([np.where(cl == c)[0] for c in pk])
            bs.append(float(np.mean(np.asarray(x)[ix])) if len(ix) else np.nan)
        lo, hi = np.nanpercentile(bs, [2.5, 97.5])
    else:
        lo = hi = np.nan
    return round(100 * p, 1), round(100 * lo, 1), round(100 * hi, 1)


# ---------------- 1) 截断分层 ----------------
for H, lab in [(4320, '72 h'), (10080, '7 d')]:
    c = classify(H).merge(oc, on='sid', how='left')
    lmk = c[c.los_hosp_min > H].copy()
    ev_ = lmk[lmk.grp != 'no_event']
    comp = ev_[ev_.complete == 1]; trunc = ev_[ev_.complete == 0]
    print('\n=== [1] %s %s 事件 %d：分类窗完整 %d / 被截断 %d' % (DB, lab, len(ev_), len(comp), len(trunc)))
    key = '1_trunc|%s' % lab
    RES[key] = dict(n_event=len(ev_), n_complete=int(len(comp)), n_truncated=int(len(trunc)))
    for g in GROUPS + ['unclassified']:
        print('   %-14s 完整 n=%4d 持续占比 %.1f%% | 截断 n=%4d 持续占比 %.1f%%' % (
            g, int((comp.grp == g).sum()), 100 * float((comp.grp == g).mean()) if len(comp) else 0,
            int((trunc.grp == g).sum()), 100 * float((trunc.grp == g).mean()) if len(trunc) else 0))
        RES[key]['complete_' + g] = int((comp.grp == g).sum())
        RES[key]['trunc_' + g] = int((trunc.grp == g).sum())
    RES[key]['median_k_idx_complete'] = round(float(pd.to_numeric(comp.k_idx, errors='coerce').median()), 2)
    RES[key]['median_k_idx_trunc'] = round(float(pd.to_numeric(trunc.k_idx, errors='coerce').median()), 2)
    RES[key]['mort_complete'] = round(100 * float(comp.died_inhosp.mean()), 1)
    RES[key]['mort_trunc'] = round(100 * float(trunc.died_inhosp.mean()), 1)
    print('   基线K中位 完整 %.2f / 截断 %.2f；死亡率 完整 %.1f%% / 截断 %.1f%%' % (
        RES[key]['median_k_idx_complete'], RES[key]['median_k_idx_trunc'],
        RES[key]['mort_complete'], RES[key]['mort_trunc']))
    # (a) 仅完整窗
    # no_event 无分类窗，属天然"完整"；必须保留为参照组
    sub = lmk[(lmk.grp == 'no_event') | ((lmk.grp != 'unclassified') & (lmk.complete == 1))]
    assert (sub.grp == 'no_event').sum() == (lmk.grp == 'no_event').sum(), '参照组被误删'
    RES['1_comp_only|%s' % lab] = regress(sub, cluster=(sub.hosp.values if W == 'eICU' else None))
    # (b) 截断者归入 unclassified
    l2 = lmk.copy(); l2.loc[l2.complete == 0, 'grp'] = 'unclassified'
    sub2 = l2[l2.grp != 'unclassified']
    RES['1_trunc_as_unc|%s' % lab] = regress(sub2, cluster=(sub2.hosp.values if W == 'eICU' else None))
    print('   仅完整窗 OR:', {k: (v['or_'], v['lo'], v['hi']) for k, v in RES['1_comp_only|%s' % lab].items()})
    print('   截断归未分类 OR:', {k: (v['or_'], v['lo'], v['hi']) for k, v in RES['1_trunc_as_unc|%s' % lab].items()})

# ---------------- 2) index > 本人 median + RCV ----------------
RCV = 1.14 if W == 'MIMIC' else 1.07
c72 = classify(4320).merge(oc, on='sid', how='left')
c72 = c72.merge(med, on='sid', how='left')
app = c72[(c72.los_hosp_min > 4320) & (c72.grp != 'no_event')].copy()
app['beyond'] = (pd.to_numeric(app.k_idx, errors='coerce') > app.k_med + RCV).astype(int)
print('\n=== [2] %s 72 h：index 超过本人中位+RCV 的事件 %d / %d (%.1f%%)' % (
    DB, int(app.beyond.sum()), len(app), 100 * app.beyond.mean()))
RES['2_beyond_share'] = dict(n=int(len(app)), beyond=int(app.beyond.sum()),
                             pct=round(100 * float(app.beyond.mean()), 1))
RES['2_beyond_only'] = regress(app[(app.beyond == 1) & (app.grp != 'unclassified')],
                               cluster=(app[(app.beyond == 1) & (app.grp != 'unclassified')].hosp.values if W == 'eICU' else None))
print('   仅限该亚组 OR:', {k: (v['or_'], v['lo'], v['hi'], v['n']) for k, v in RES['2_beyond_only'].items()})

# ---------------- 3) 各状态的复测次数分布 ----------------
c_whole = classify(10080).merge(oc, on='sid', how='left')
print('\n=== [3] %s 各状态 24 h 内复测次数分布（全队列）' % DB)
dist = {}
for g in ['transient', 'intermittent', 'sustained']:
    s = c_whole[c_whole.grp == g]
    if not len(s): continue
    one = int((s.n_after == 1).sum())
    dist[g] = dict(n=int(len(s)), median=float(s.n_after.median()),
                   q1=float(s.n_after.quantile(.25)), q3=float(s.n_after.quantile(.75)),
                   n_one=int(one), pct_one=round(100 * one / len(s), 1))
    print('   %-14s n=%4d 中位 %.1f (IQR %.0f–%.0f) | 仅 1 次复测 %d (%.1f%%)' % (
        g, dist[g]['n'], dist[g]['median'], dist[g]['q1'], dist[g]['q3'], one, dist[g]['pct_one']))
RES['3_dist'] = dist

# ---------------- 4) 竞争事件（landmark 后出院 vs 死亡） ----------------
print('\n=== [4] %s 72 h landmark：竞争事件检查' % DB)
lmk = c72[c72.los_hosp_min > 4320]
died = int(lmk.died_inhosp.sum()); alive = len(lmk) - died
print('   landmark 后院内死亡 %d / 存活出院 %d（%.1f%% / %.1f%%）' % (
    died, alive, 100 * died / len(lmk), 100 * alive / len(lmk)))
RES['4_compete'] = dict(n=len(lmk), died=died, discharged_alive=alive)
# 敏感性：排除 landmark 后 48 h 内出院的患者（这些人出院后死亡不可见）
late = lmk[lmk.los_hosp_min > 4320 + 2880]
sub = late[late.grp != 'unclassified']
RES['4_excl_48h_discharge'] = regress(sub, cluster=(sub.hosp.values if W == 'eICU' else None))
print('   排除 landmark 后 48 h 内出院者后 n=%d：OR %s' % (
    len(sub), {k: (v['or_'], v['lo'], v['hi']) for k, v in RES['4_excl_48h_discharge'].items()}))

# ---------------- 5) 聚类比例 CI（eICU 医院层） ----------------
print('\n=== [5] %s 比例与聚类 CI' % DB)
cl_coh = None
if W == 'eICU':
    m = oc.set_index('sid').hosp
    cl_coh = m.reindex(c_whole.sid).values
n_coh = len(c_whole); n_app = int((c_whole.grp != 'no_event').sum())
p, lo, hi = prop_ci(n_app, n_coh, cluster=cl_coh)
print('   发病率 %d/%d = %.1f%% (聚类 CI %.1f–%.1f)' % (n_app, n_coh, p, lo, hi))
RES['5_incidence'] = dict(n=n_coh, k=n_app, pct=p, lo=lo, hi=hi)
ev0 = pd.read_pickle('out/k3_events_%s.pkl' % ('mimic' if W == 'MIMIC' else 'eicu'))
w6 = (ev0.t_next <= 360).astype(int).values
cl6 = oc.set_index('sid').hosp.reindex(ev0.sid).values if W == 'eICU' else None
p, lo, hi = prop_ci(w6, len(ev0), cluster=cl6)
print('   6 h 复查率 %d/%d = %.1f%% (聚类 CI %.1f–%.1f)' % (w6.sum(), len(ev0), p, lo, hi))
RES['5_recheck6'] = dict(n=len(ev0), k=int(w6.sum()), pct=p, lo=lo, hi=hi)
cf = ev0.confirm.astype(int).values
p, lo, hi = prop_ci(cf, len(ev0), cluster=cl6)
print('   下一次测量确认率 %d/%d = %.1f%% (聚类 CI %.1f–%.1f)' % (cf.sum(), len(ev0), p, lo, hi))
RES['5_confirm'] = dict(n=len(ev0), k=int(cf.sum()), pct=p, lo=lo, hi=hi)

# ---------------- 6) E-value ----------------
base_p = float(lmk[lmk.grp == 'no_event'].died_inhosp.mean())
print('\n=== [6] %s 72 h 参照组风险 %.4f' % (DB, base_p))
ev_res = {}
for g in GROUPS:
    s = lmk[lmk.grp == g]
    if not len(s) or not len(lmk[lmk.grp == 'no_event']): continue
    a = float(s.died_inhosp.sum()); b = len(s) - a
    c0 = float(lmk[lmk.grp == 'no_event'].died_inhosp.sum()); d0 = len(lmk[lmk.grp == 'no_event']) - c0
    orv = (a * d0) / max(b * c0, 1e-9)
    e = evalue(orv, base_p)
    ev_res[g] = dict(crude_or=round(orv, 2), evalue=e)
    print('   %-14s 粗 OR %.2f → E-value %.2f' % (g, orv, e))
RES['6_evalue'] = ev_res

# ---------------- 7) 透析 / RRT ----------------
print('\n=== [7] %s RRT（肾脏替代治疗）比例' % DB)
n_rrt = int(ev.tx_rrt.sum())
print('   事件中记录到 RRT %d / %d (%.1f%%)' % (n_rrt, len(ev), 100 * ev.tx_rrt.mean()))
RES['7_rrt'] = dict(n=len(ev), n_rrt=n_rrt, pct=round(100 * float(ev.tx_rrt.mean()), 1))
noRT = app[(app.grp != 'unclassified') & (~app.sid.isin(ev[ev.tx_rrt == 1].sid.astype(app.sid.dtype)))]
RES['7_excl_rrt'] = regress(noRT, cluster=(noRT.hosp.values if W == 'eICU' else None))
print('   排除 RRT 事件后 n=%d：OR %s' % (
    len(noRT), {k: (v['or_'], v['lo'], v['hi']) for k, v in RES['7_excl_rrt'].items()}))

# ---------------- 8) 按治疗状态分层（完整 OR） ----------------
print('\n=== [8] %s 按是否记录到治疗分层（窄窗口）' % DB)
txm = ev[['sid'] + ['tn_' + c for c in ['insulin_glucose', 'binder', 'iv_calcium', 'bicarbonate', 'rrt']]].copy()
txm['treated'] = txm[[c for c in txm.columns if c.startswith('tn_')]].any(axis=1).astype(int)
ap2 = app.merge(txm[['sid', 'treated']], on='sid', how='left'); ap2['treated'] = ap2.treated.fillna(0).astype(int)
for tv in (0, 1):
    s = ap2[(ap2.treated == tv) & (ap2.grp != 'unclassified')]
    RES['8_treated%d' % tv] = regress(s, cluster=(s.hosp.values if W == 'eICU' else None))
    print('   %s n=%d：OR %s' % ('有治疗' if tv else '无治疗', len(s),
                                {k: (v['or_'], v['lo'], v['hi']) for k, v in RES['8_treated%d' % tv].items()}))

json.dump(RES, open('out/k48_round2_%s.json' % W.lower(), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1, default=str)
print('\n写出 out/k48_round2_%s.json' % W.lower())
