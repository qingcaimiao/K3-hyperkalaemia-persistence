# -*- coding: utf-8 -*-
"""
K3 阶段③b：landmark 长度敏感性（72h vs 7d）+ unknown 组的边界分配敏感性
7 天 landmark 只保留 36% 队列（中位住院仅 3–4 天）→ 需检验梯度在更短 landmark 下是否稳健。
"""
import duckdb, pandas as pd, numpy as np, json, warnings
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


def classify(d, H):
    rows = []
    for sid, g in d.groupby('sid', sort=False):
        pre = g[g.t <= BASE]
        if len(pre) == 0 or float(pre.k.max()) >= 5.5: continue
        post = g[(g.t > BASE) & (g.t <= H)]
        if len(post) == 0: continue
        pos = post[post.k >= 5.5]
        if len(pos) == 0:
            rows.append(dict(sid=sid, grp='no_event', k_idx=np.nan)); continue
        idx = pos.iloc[0]
        a24 = post[(post.t > idx.t) & (post.t <= idx.t + BASE)]
        if len(a24) == 0: grp = 'unknown'
        elif float(a24.k.iloc[0]) < 5.5: grp = 'transient'
        elif bool((a24.k >= 5.5).all()): grp = 'sustained'
        else: grp = 'confirmed'
        rows.append(dict(sid=sid, grp=grp, k_idx=float(idx.k)))
    return pd.DataFrame(rows)


def regress(sub):
    from sklearn.linear_model import LogisticRegression
    sub = sub.copy()
    for g in ['transient', 'confirmed', 'sustained']:
        sub['g_' + g] = (sub.grp == g).astype(int)
    sub['k_idx_f'] = sub.k_idx.fillna(5.4)
    sub['age_f'] = pd.to_numeric(sub.age, errors='coerce').fillna(sub.age.median() if sub.age.notna().any() else 65)
    sub['sex_m'] = (sub.sex.astype(str).str.upper().str[0] == 'M').astype(int)
    F = ['g_transient', 'g_confirmed', 'g_sustained', 'k_idx_f', 'age_f', 'sex_m']
    X = sub[F].astype(float).values; y = sub.died_inhosp.astype(int).values
    if len(np.unique(y)) < 2: return {}
    m = LogisticRegression(max_iter=4000).fit(X, y)
    rng = np.random.default_rng(3); bs = []
    for _ in range(400):
        i = rng.integers(0, len(y), len(y))
        if len(np.unique(y[i])) < 2: continue
        try: bs.append(LogisticRegression(max_iter=4000).fit(X[i], y[i]).coef_[0])
        except Exception: pass
    bs = np.array(bs); out = {}
    for j, v in enumerate(['g_transient', 'g_confirmed', 'g_sustained']):
        ci = np.exp(np.percentile(bs[:, j], [2.5, 97.5])) if len(bs) > 50 else [np.nan, np.nan]
        out[v] = dict(or_=round(float(np.exp(m.coef_[0][j])), 2),
                      ci=[round(float(ci[0]), 2), round(float(ci[1]), 2)])
    return out


OUT = {}
for nm, d, oc in [('MIMIC-IV', pd.read_pickle('out/k3_k_series_mimic.pkl'), om),
                  ('eICU-CRD', pd.read_pickle('out/k3_k_series_eicu.pkl'), oe)]:
    print('\n' + '=' * 100); print(nm); print('=' * 100)
    d = d.sort_values(['sid', 't']).reset_index(drop=True)
    res = {}
    for H, lab in [(4320, '72 h'), (10080, '7 d')]:
        coh = classify(d, H).merge(oc, on='sid', how='left')
        lmk = coh[coh.los_hosp_min > H].copy()
        print('\n--- landmark %s：暴露窗 = 24h–%s，队列 = 住院/死亡 > %s ---'
              % (lab, lab, lab))
        print('  %-14s %7s %10s' % ('组', 'n', 'landmark后院内死亡%'))
        rows = []
        for g in ['no_event', 'transient', 'confirmed', 'sustained', 'unknown']:
            s = lmk[lmk.grp == g]
            if not len(s): continue
            rows.append(dict(grp=g, n=int(len(s)), died=round(100 * float(s.died_inhosp.mean()), 1)))
            print('  %-14s %7s %9.1f%%' % (g, format(len(s), ','), 100 * s.died_inhosp.mean()))
        rr = regress(lmk[lmk.grp != 'unknown'])
        print('  OR（校正索引值/年龄/性别，无事件为参照）：%s'
              % ' | '.join('%s %.2f (%.2f–%.2f)' % (k.replace('g_', ''),
                                                    v['or_'], v['ci'][0], v['ci'][1]) for k, v in rr.items()))
        res[lab] = dict(n_landmark=int(len(lmk)), rows=rows, or_=rr)

        # unknown 组边界分配敏感性（仅 7 d 版报一次）
        if lab == '7 d':
            n_t = int((lmk.grp == 'transient').sum()); n_c = int((lmk.grp == 'confirmed').sum())
            n_s = int((lmk.grp == 'sustained').sum()); n_u = int((lmk.grp == 'unknown').sum())
            base = float(lmk[lmk.grp == 'no_event'].died_inhosp.mean())
            for name, dt, dc, ds in [('unknown 全按一过性', n_u, 0, 0), ('unknown 全按持续', 0, 0, n_u)]:
                tt = int(lmk[lmk.grp == 'transient'].died_inhosp.sum()) + dt
                cc = int(lmk[lmk.grp == 'confirmed'].died_inhosp.sum()) + dc
                ss = int(lmk[lmk.grp == 'sustained'].died_inhosp.sum()) + ds
                print('      [%s] 一过性 %.1f%% | 已确认 %.1f%% | 持续 %.1f%%（无事件参照 %.1f%%）'
                      % (name, 100 * tt / max(n_t + dt, 1), 100 * cc / max(n_c + dc, 1),
                         100 * ss / max(n_s + ds, 1), 100 * base))
            res[lab]['unknown_bounds'] = dict(
                as_transient=[round(100 * (int(lmk[lmk.grp == 'transient'].died_inhosp.sum()) + n_u) / max(n_t + n_u, 1), 1)],
                as_sustained=[round(100 * (int(lmk[lmk.grp == 'sustained'].died_inhosp.sum()) + n_u) / max(n_s + n_u, 1), 1)])
    OUT[nm] = res
json.dump(OUT, open('out/k3_phase3b.json', 'w'), ensure_ascii=False, indent=1)
print('\n写出 out/k3_phase3b.json')
