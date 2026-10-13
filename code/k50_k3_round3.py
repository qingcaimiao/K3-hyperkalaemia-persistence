# -*- coding: utf-8 -*-
"""K3 第三轮补充分析（口径已对齐：全队列=表2；72h landmark=表5）：
[A] sustained 内部：仅 1 次复测 vs >=2 次复测（核心质疑，全队列口径）
[B] 要求 >=2 次复测才能判 state 的口径（72h landmark 口径）
[C] 固定 24-48h 窗会漏掉多少事件
[E] 测量密度分层敏感性
[F] 各状态 E 值（含 intermittent）+ OR->RR 转换
[H] tau^2 敏感性表
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
    ser = 'out/k3_k_series_mimic.pkl'
else:
    q = f"""SELECT patientunitstayid AS sid, TRY_CAST(hospitaldischargeoffset AS DOUBLE) AS los_hosp_min,
       CASE WHEN lower(coalesce(hospitaldischargestatus,'')) LIKE 'expired%' THEN 1 ELSE 0 END AS died_inhosp,
       gender AS sex, TRY_CAST(age AS DOUBLE) AS age FROM {T(E + '/patient.csv')} WHERE {CIT}"""
    ser = 'out/k3_k_series_eicu.pkl'
oc = con.execute(q).df()
d = pd.read_pickle(ser).sort_values(['sid', 't']).reset_index(drop=True)
med = d.groupby('sid').k.median()
npost = d[d.t > BASE].groupby('sid').size()
GROUPS = ['transient', 'intermittent', 'sustained']
RES = {}


def build(full=False, landmark=H):
    """full=True -> 事件搜索不限时间（= 表 2 全队列）；否则 (BASE, landmark]。"""
    rows = []
    for sid, g in d.groupby('sid', sort=False):
        pre = g[g.t <= BASE]
        if len(pre) == 0 or float(pre.k.max()) >= 5.5:
            continue
        post = g[g.t > BASE] if full else g[(g.t > BASE) & (g.t <= landmark)]
        if len(post) == 0:
            continue
        pos = post[post.k >= 5.5]
        base = dict(sid=int(sid), k_med=float(med.get(sid, np.nan)),
                    npost=int(npost.get(sid, 0)))
        if len(pos) == 0:
            rows.append(dict(base, grp='no_event', k_idx=np.nan, n_after=0,
                             n_ge=0, idx_t=np.nan, complete=-1)); continue
        idx = pos.iloc[0]
        a = post[(post.t > idx.t) & (post.t <= idx.t + BASE)]
        n = len(a); nge = int((a.k >= 5.5).sum())
        grp = ('unclassified' if n == 0 else
               ('sustained' if nge == n else ('intermittent' if nge > 0 else 'transient')))
        rows.append(dict(base, grp=grp, k_idx=float(idx.k), n_after=int(n), n_ge=nge,
                         idx_t=float(idx.t), complete=int(idx.t + BASE <= landmark)))
    return pd.DataFrame(rows)


def regress(sub, seed=3, nb=400):
    sub = sub.copy(); names = ['g_' + g for g in GROUPS]
    _n0 = int((sub.grp == 'no_event').sum())
    assert _n0 >= 50, '回归缺少参照组（no_event 仅 %d 例）' % _n0
    for g, c in zip(GROUPS, names):
        sub[c] = (sub.grp == g).astype(int)
    sub['k_idx_f'] = pd.to_numeric(sub.k_idx, errors='coerce').fillna(5.4)
    sub['age_f'] = pd.to_numeric(sub.age, errors='coerce').fillna(sub.age.median())
    sub['sex_m'] = (sub.sex.astype(str).str.upper().str[0] == 'M').astype(int)
    feats = names + ['k_idx_f', 'age_f', 'sex_m']
    X = sub[feats].astype(float).values; y = sub.died_inhosp.astype(int).values
    if len(np.unique(y)) < 2 or len(sub) < 60:
        return {}
    m = LogisticRegression(max_iter=4000).fit(X, y); coef = m.coef_[0]
    assert len(feats) == len(coef)
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
        ci = (np.exp(np.percentile(bs[:, j], [2.5, 97.5])) if len(bs) > 50
              else np.array([np.nan, np.nan]))
        out[nm] = dict(or_=round(float(np.exp(coef[j])), 2),
                       lo=round(float(ci[0]), 2), hi=round(float(ci[1]), 2))
    return out


def show(tag, r):
    print('   %-28s %s' % (tag, {k: (v['or_'], v['lo'], v['hi']) for k, v in r.items()}))


print('========== %s ==========' % DB)
call = build(full=True).merge(oc, on='sid', how='left')          # 全队列（表 2）
cl = build(full=False).merge(oc, on='sid', how='left')
cl['los_hosp_min'] = pd.to_numeric(cl.los_hosp_min, errors='coerce')
cl = cl[cl.los_hosp_min > H].copy()                               # 72h landmark（表 5）
print('全队列 %d 分布 %s' % (len(call), dict(call.grp.value_counts())))
print('72h landmark %d 分布 %s' % (len(cl), dict(cl.grp.value_counts())))

# ---------------- [A] sustained 内部（全队列口径） ----------------
sus = call[call.grp == 'sustained'].copy()
A = {}
for lab, s in [('sustained_all', sus), ('sustained_1recheck', sus[sus.n_after == 1]),
               ('sustained_ge2recheck', sus[sus.n_after >= 2])]:
    A[lab] = dict(n=int(len(s)),
                  died_pct=round(100 * float(s.died_inhosp.mean()), 1) if len(s) else None,
                  age_med=round(float(pd.to_numeric(s.age, errors='coerce').median()), 1) if len(s) else None,
                  k_idx_med=round(float(pd.to_numeric(s.k_idx, errors='coerce').median()), 2) if len(s) else None)
print('\n[A] sustained 构成（全队列）：')
for k, v in A.items():
    print('   %-24s n=%-4s 院内死亡 %-7s 年龄中位 %-6s index 中位 %s'
          % (k, v['n'], ('%.1f%%' % v['died_pct']) if v['died_pct'] is not None else '-',
             v['age_med'], v['k_idx_med']))
for g in ['transient', 'intermittent']:
    s1 = call[(call.grp == g) & (call.n_after == 1)]
    s2 = call[(call.grp == g) & (call.n_after >= 2)]
    if len(s1):
        print('   [对照] %-12s 1 次复测 n=%-4d 死亡 %.1f%% | >=2 次 n=%-4d 死亡 %.1f%%'
              % (g, len(s1), 100 * s1.died_inhosp.mean(), len(s2),
                 (100 * s2.died_inhosp.mean()) if len(s2) else float('nan')))
RES['A_sustained_split'] = A

# ---------------- [B] >=2 次复测口径（72h landmark） ----------------
c2 = cl.copy()
c2['grp'] = np.where((c2.grp.isin(['transient', 'intermittent', 'sustained'])) &
                     (c2.n_after < 2), 'unclassified', c2.grp)
print('\n[B] >=2 次复测（72h landmark）分布 %s' % dict(c2.grp.value_counts()))
RES['B_ge2'] = regress(c2); show('>=2 次复测', RES['B_ge2'])
lim = cl[(cl.grp.isin(['transient', 'sustained'])) & (cl.n_after == 1)]
RES['B_limited'] = dict(n=int(len(lim)),
                        died_pct=round(100 * float(lim.died_inhosp.mean()), 1) if len(lim) else None)
print('   [B] 仅 1 次复测单列 n=%s 死亡 %s' % (RES['B_limited']['n'], RES['B_limited']['died_pct']))

# ---------------- [C] 固定窗会漏掉的事件 ----------------
nev = int((cl.grp != 'no_event').sum())
late = int(((cl.grp != 'no_event') & (cl.idx_t > 2 * BASE)).sum())
RES['C_fixed_window'] = dict(events=nev, late=late, late_pct=round(100 * late / max(nev, 1), 1))
print('\n[C] 72h landmark 事件 %d；其中 48h 后才首次升高（固定 24-48h 窗将漏掉）%d (%.1f%%)'
      % (nev, late, 100 * late / max(nev, 1)))

# ---------------- [E] 测量密度分层 ----------------
med_post = float(np.nanmedian(cl.npost.values))
for lab, cond in [('density_ge_median', cl.npost >= med_post),
                  ('density_top_quartile', cl.npost >= np.nanpercentile(cl.npost, 75))]:
    s = cl[(cl.grp == 'no_event') | cond].copy()
    s = s[s.grp != 'unclassified']
    RES['E_' + lab] = regress(s); show(lab, RES['E_' + lab])

# ---------------- [F] E 值（含 intermittent） ----------------
def evalue_rr(rr):
    return None if (rr is None or rr <= 1) else round(rr + np.sqrt(rr * (rr - 1)), 1)


def or2rr(or_, p0):
    return or_ / (1 - p0 + p0 * or_)


base_p = float(cl[cl.grp == 'no_event'].died_inhosp.mean())
rb = regress(cl[cl.grp != 'unclassified'])
EV = {'base_risk': round(base_p, 4), 'rows': {}}
for g, v in rb.items():
    rr = or2rr(v['or_'], base_p)
    EV['rows'][g] = dict(or_=v['or_'], rr=round(rr, 2), evalue=evalue_rr(rr))
    print('   [F] %-14s OR %.2f  RR~%.2f  E-value %s' % (g, v['or_'], rr, EV['rows'][g]['evalue']))
RES['F_evalue'] = EV

# ---------------- [H] tau^2 敏感性 ----------------
from scipy.stats import norm
ph = json.load(open('out/k3_phase2c.json', encoding='utf-8'))
ev = pd.read_pickle('out/k3_events_mimic.pkl' if W == 'MIMIC' else 'out/k3_events_eicu.pkl')
rep = ev[ev.t_next.notna() & ev.k_prev.notna()]
kpop = ph[DB]['kpop']; tau2 = ph[DB]['tau2']
TH = []
for mult in [0.25, 0.5, 1.0, 2.0, 4.0]:
    row = dict(mult=mult)
    for lbl, sd in [('cv3', 0.03 * kpop), ('cv5', 0.05 * kpop)]:
        t2 = tau2 * mult; lam = t2 / (t2 + sd ** 2)
        mu = lam * rep.k_idx.values + (1 - lam) * kpop
        s2 = sd * np.sqrt(1 + lam)
        row[lbl] = round(100 * float((1 - norm.cdf((5.5 - mu) / s2)).mean()), 1)
    TH.append(row)
    print('   [H] tau2 x%.2f : CV3%% %.1f%% | CV5%% %.1f%%' % (mult, row['cv3'], row['cv5']))
RES['H_tau2'] = dict(kpop=round(kpop, 3), tau2=round(tau2, 4),
                     observed=round(100 * float(ph[DB]['obs_confirm']), 1), table=TH)

json.dump(RES, open('out/k50_%s.json' % W.lower(), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('\n已写入 out/k50_%s.json' % W.lower())
