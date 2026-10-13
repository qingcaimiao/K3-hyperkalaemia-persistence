# -*- coding: utf-8 -*-
"""
K3 审计补充：① 比例的 95% CI（bootstrap）② OR 与 CI 独立重算 ③ eICU ICU>24h 敏感性
④ unclassified 边界分配 ⑤ CV 的两种分母口径
"""
import duckdb, pandas as pd, numpy as np, json, warnings
warnings.filterwarnings('ignore')
from sklearn.linear_model import LogisticRegression

M = 'D:/shujuku/mimic-iv-3.1'; E = 'D:/shujuku/EICU 2.0'
T = lambda p: "read_csv_auto('{}', strict_mode=false, ignore_errors=true)".format(p)
con = duckdb.connect(); con.execute('SET threads=6')
BASE = 1440; THR = 5.5
CIC = "regexp_matches(first_careunit,'CCU|CVICU')"
CIT = "regexp_matches(unittype,'Cardiac ICU|CCU|CSICU|CTICU')"

qm = f"""
WITH icu AS (SELECT stay_id, subject_id, hadm_id, intime,
      ROW_NUMBER() OVER (PARTITION BY hadm_id ORDER BY intime) AS rn
      FROM {T(M + '/icu/icustays.csv')} WHERE {CIC}), co AS (SELECT * FROM icu WHERE rn=1)
SELECT co.stay_id AS sid, DATE_DIFF('minute', co.intime, a.dischtime) AS los_hosp_min,
       a.hospital_expire_flag AS died_inhosp, p.gender AS sex,
       TRY_CAST(p.anchor_age AS DOUBLE)+GREATEST(TRY_CAST(EXTRACT(YEAR FROM co.intime) AS INT)-p.anchor_year,0) AS age
FROM co JOIN {T(M + '/hosp/admissions.csv')} a ON a.hadm_id=co.hadm_id
        JOIN {T(M + '/hosp/patients.csv')} p ON p.subject_id=co.subject_id"""
om = con.execute(qm).df()
qe = f"""SELECT patientunitstayid AS sid, TRY_CAST(hospitaldischargeoffset AS DOUBLE) AS los_hosp_min,
       TRY_CAST(unitdischargeoffset AS DOUBLE) AS icu_min,
       CASE WHEN lower(coalesce(hospitaldischargestatus,'')) LIKE 'expired%' THEN 1 ELSE 0 END AS died_inhosp,
       gender AS sex, TRY_CAST(age AS DOUBLE) AS age FROM {T(E + '/patient.csv')} WHERE {CIT}"""
oe = con.execute(qe).df()
RES = []


def add(item, db, value, note=''):
    RES.append(dict(item=item, db=db, value=value, note=note))
    print('  %-52s %-10s %s  %s' % (item, db, value, note))


for nm, f, oc in [('MIMIC-IV', 'out/k3_k_series_mimic.pkl', om),
                  ('eICU-CRD', 'out/k3_k_series_eicu.pkl', oe)]:
    d = pd.read_pickle(f).sort_values(['sid', 't']).reset_index(drop=True)
    print('\n' + '=' * 100); print(nm); print('=' * 100)

    # ---------- ① 比例 CI ----------
    rows = []
    for sid, g in d.groupby('sid', sort=False):
        pre = g[g.t <= BASE]
        if len(pre) == 0 or float(pre.k.max()) >= THR: continue
        post = g[g.t > BASE]
        if len(post) == 0: continue
        pos = post[post.k >= THR]
        if len(pos) == 0:
            rows.append(dict(sid=sid, grp='no_event', k_idx=np.nan)); continue
        idx = pos.iloc[0]
        a24 = post[(post.t > idx.t) & (post.t <= idx.t + BASE)]
        if len(a24) == 0: grp = 'unknown'
        elif float(a24.k.iloc[0]) < THR: grp = 'transient'
        elif bool((a24.k >= THR).all()): grp = 'sustained'
        else: grp = 'confirmed'
        rows.append(dict(sid=sid, grp=grp, k_idx=float(idx.k)))
    coh = pd.DataFrame(rows)
    # ICU>24h 敏感性（仅 eICU 有 icu_min；MIMIC 用住院记录故不受影响）
    if 'icu_min' in oc.columns:
        keep = set(oc.loc[oc.icu_min > BASE, 'sid'])
        c2 = coh[coh.sid.isin(keep)]
        n2 = len(c2); a2 = int((c2.grp != 'no_event').sum())
        cf2 = int(c2.grp.isin(['confirmed', 'sustained']).sum()); su2 = int((c2.grp == 'sustained').sum())
        add('敏感性:ICU停留>24h 队列n', nm, n2)
        add('敏感性:ICU停留>24h apparent', nm, a2)
        add('敏感性:ICU停留>24h apparent%', nm, round(100 * a2 / n2, 2))
        add('敏感性:ICU停留>24h confirmed', nm, cf2)
        add('敏感性:ICU停留>24h confirmed/apparent%', nm, round(100 * cf2 / a2, 1))
        add('敏感性:ICU停留>24h sustained', nm, su2)
        add('敏感性:ICU停留>24h sustained/apparent%', nm, round(100 * su2 / a2, 1))
    n_coh = len(coh); n_app = int((coh.grp != 'no_event').sum())
    rng = np.random.default_rng(11)
    flag = (coh.grp != 'no_event').values.astype(float)
    bs = np.array([flag[rng.integers(0, n_coh, n_coh)].mean() for _ in range(4000)])
    add('apparent n / 队列 n', nm, '%d / %d' % (n_app, n_coh))
    add('apparent %', nm, round(100 * n_app / n_coh, 2))
    add('apparent% 95%CI(bootstrap 4000)', nm, '%.2f–%.2f' % (100 * np.percentile(bs, 2.5), 100 * np.percentile(bs, 97.5)))
    p = n_app / n_coh; se = np.sqrt(p * (1 - p) / n_coh)
    add('apparent% 95%CI(Wald)', nm, '%.2f–%.2f' % (100 * (p - 1.96 * se), 100 * (p + 1.96 * se)))
    # ---------- ⑤ CV 两种分母 ----------
    dd = d.copy(); dd['dk'] = dd.groupby('sid').k.diff(); dd['dt'] = dd.groupby('sid').t.diff()
    pr = dd[(dd.dt > 0) & (dd.dt <= BASE)]
    sd_w = float(pr.dk.std() / np.sqrt(2))
    add('CV 分母=全部测量均值', nm, round(100 * sd_w / float(d.k.mean()), 2))
    add('CV 分母=配对样本均值(k30口径)', nm, round(100 * sd_w / float(pr.k.mean()), 2))

    # ---------- ②/④ landmark ----------
    for H, lab in [(4320, '72h'), (10080, '7d')]:
        r2 = []
        for sid, g in d.groupby('sid', sort=False):
            pre = g[g.t <= BASE]
            if len(pre) == 0 or float(pre.k.max()) >= THR: continue
            post = g[(g.t > BASE) & (g.t <= H)]
            if len(post) == 0: continue
            pos = post[post.k >= THR]
            if len(pos) == 0:
                r2.append(dict(sid=sid, grp='no_event', k_idx=np.nan)); continue
            idx = pos.iloc[0]
            a24 = post[(post.t > idx.t) & (post.t <= idx.t + BASE)]
            if len(a24) == 0: grp = 'unknown'
            elif float(a24.k.iloc[0]) < THR: grp = 'transient'
            elif bool((a24.k >= THR).all()): grp = 'sustained'
            else: grp = 'confirmed'
            r2.append(dict(sid=sid, grp=grp, k_idx=float(idx.k)))
        c3 = pd.DataFrame(r2).merge(oc, on='sid', how='left')
        lm = c3[c3.los_hosp_min > H].copy()
        sub = lm[lm.grp != 'unknown'].copy()
        for g in ['transient', 'confirmed', 'sustained']:
            sub['g_' + g] = (sub.grp == g).astype(int)
        sub['k_idx_f'] = sub.k_idx.fillna(5.4)
        sub['age_f'] = pd.to_numeric(sub.age, errors='coerce').fillna(sub.age.median() if sub.age.notna().any() else 65)
        sub['sex_m'] = (sub.sex.astype(str).str.upper().str[0] == 'M').astype(int)
        F = ['g_transient', 'g_confirmed', 'g_sustained', 'k_idx_f', 'age_f', 'sex_m']
        X = sub[F].astype(float).values; y = sub.died_inhosp.astype(int).values
        m = LogisticRegression(max_iter=4000).fit(X, y)
        rng2 = np.random.default_rng(3); bsc = []
        for _ in range(400):
            i = rng2.integers(0, len(y), len(y))
            if len(np.unique(y[i])) < 2: continue
            try:
                bsc.append(LogisticRegression(max_iter=4000).fit(X[i], y[i]).coef_[0])
            except Exception: pass
        bsc = np.array(bsc)
        for j, v in enumerate(['transient', 'confirmed', 'sustained']):
            orv = float(np.exp(m.coef_[0][j]))
            ci = np.exp(np.percentile(bsc[:, j], [2.5, 97.5]))
            add('OR %s (landmark %s)' % (v, lab), nm, '%.2f (%.2f–%.2f)' % (orv, ci[0], ci[1]))
        # unknown 边界：全部按"已死亡"计入该组
        n_u = int((lm.grp == 'unknown').sum())
        for g in ['transient', 'sustained']:
            s = lm[lm.grp == g]; n_g = len(s); dd_ = int(s.died_inhosp.sum())
            add('上界:unknown全计为死亡并归%s (%s)' % (g, lab), nm,
                round(100 * (dd_ + n_u) / (n_g + n_u), 1), 'n_%s=%d died=%d n_u=%d' % (g, n_g, dd_, n_u))
            add('下界:unknown按该组死亡率归%s (%s)' % (g, lab), nm,
                round(100 * dd_ / n_g, 1), '（不改变原估计）')
        add('参照 no_event 死亡率 %s' % lab, nm, round(100 * float(lm[lm.grp == 'no_event'].died_inhosp.mean()), 1))

pd.DataFrame(RES).to_csv('out/k3_audit_numbers2.csv', index=False, encoding='utf-8-sig')
print('\n写出 out/k3_audit_numbers2.csv')
