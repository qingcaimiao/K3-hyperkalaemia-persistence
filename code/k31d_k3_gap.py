# -*- coding: utf-8 -*-
"""
K3 阶段②d：用「复查间隔」代替「治疗记录」作中介（治疗记录在两库不可比，见 k31b）
三条：
 A 两库按索引值分层的复查间隔分布（确认率依赖间隔，而间隔本身是监测行为的函数）
 B 在同一 (索引值 × 间隔) 格内比较两库确认率 → ≥6.5 层的库间差异是否由复查时机解释
 C 无复查者的结局（院内死亡）→ bounds 的方向性证据
"""
import duckdb, pandas as pd, numpy as np, json, os, warnings
warnings.filterwarnings('ignore')
M = 'D:/shujuku/mimic-iv-3.1'; E = 'D:/shujuku/EICU 2.0'
T = lambda p: "read_csv_auto('{}', strict_mode=false, ignore_errors=true)".format(p)
con = duckdb.connect(); con.execute('SET threads=6')
GAPS = [(0, 180, '≤3 h'), (180, 360, '3–6 h'), (360, 720, '6–12 h'), (720, 1441, '12–24 h')]
BANDS = [(5.5, 6.0, '5.5–5.9'), (6.0, 6.5, '6.0–6.4'), (6.5, 20.0, '≥6.5')]
OUT = {}

# ---------- 结局表 ----------
if not os.path.exists('out/k3_outcome_mimic.pkl'):
    q = f"""WITH icu AS (SELECT stay_id, hadm_id FROM {T(M + '/icu/icustays.csv')}
              WHERE regexp_matches(first_careunit,'CCU|CVICU'))
    SELECT icu.stay_id AS sid, a.hospital_expire_flag AS died_inhosp,
           DATE_DIFF('minute', a.admittime, a.dischtime) AS los_hosp
    FROM icu JOIN {T(M + '/hosp/admissions.csv')} a ON a.hadm_id = icu.hadm_id"""
    pd.to_pickle(con.execute(q).df(), 'out/k3_outcome_mimic.pkl')
if not os.path.exists('out/k3_outcome_eicu.pkl'):
    q = f"""SELECT patientunitstayid AS sid, hospitaldischargestatus AS status,
                   unitdischargeoffset, hospitaldischargeoffset
            FROM {T(E + '/patient.csv')}
            WHERE regexp_matches(unittype,'Cardiac ICU|CCU|CSICU|CTICU')"""
    pd.to_pickle(con.execute(q).df(), 'out/k3_outcome_eicu.pkl')

ev = {'MIMIC-IV': pd.read_pickle('out/k3_events_mimic.pkl'),
      'eICU-CRD': pd.read_pickle('out/k3_events_eicu.pkl')}
for nm, e in ev.items():
    print('\n' + '=' * 108); print(nm); print('=' * 108)
    rep = e[e.t_next.notna()].copy()
    print('--- A 复查间隔（小时）按索引值分层 ---')
    print('  %-8s %8s %10s %10s %10s' % ('索引值', 'n', '中位', 'P25', 'P75'))
    gapA = []
    for lo, hi, lab in BANDS:
        s = rep[(rep.k_idx >= lo) & (rep.k_idx < hi)]
        if not len(s): continue
        h = s.t_next / 60
        gapA.append(dict(band=lab, n=int(len(s)), med=round(float(h.median()), 1),
                         p25=round(float(h.quantile(.25)), 1), p75=round(float(h.quantile(.75)), 1)))
        print('  %-8s %8d %10.1f %10.1f %10.1f' % (lab, len(s), h.median(), h.quantile(.25), h.quantile(.75)))
    print('  全组中位复查间隔 %.1f h' % (rep.t_next.median() / 60))

    print('\n--- B 同一 (索引值 × 间隔) 格内的确认率 ---')
    grid = []
    for lo, hi, bl in BANDS:
        for glo, ghi, gl in GAPS:
            s = rep[(rep.k_idx >= lo) & (rep.k_idx < hi) & (rep.t_next > glo) & (rep.t_next <= ghi)]
            if len(s) < 15: continue
            grid.append(dict(band=bl, gap=gl, n=int(len(s)), confirm=round(100 * float(s.confirm.mean()), 1)))
            print('  %-8s %-8s n=%4d 确认 %5.1f%%' % (bl, gl, len(s), 100 * s.confirm.mean()))

    print('\n--- C 无复查者 vs 有复查者的结局 ---')
    if nm == 'MIMIC-IV':
        oc = pd.read_pickle('out/k3_outcome_mimic.pkl')
        e2 = e.merge(oc, on='sid', how='left')
        e2['norep'] = e2.t_next.isna()
        e2['died'] = (e2.died_inhosp == 1)
    else:
        oc = pd.read_pickle('out/k3_outcome_eicu.pkl')
        e2 = e.merge(oc, on='sid', how='left')
        e2['norep'] = e2.t_next.isna()
        e2['died'] = e2.status.astype(str).str.lower().str.startswith('expired')
        # eICU：24h 后至出院前离开 ICU 的时长
        e2['hos_after'] = (pd.to_numeric(e2.hospitaldischargeoffset, errors='coerce')
                           - pd.to_numeric(e2.unitdischargeoffset, errors='coerce'))
    t = e2.groupby('norep').agg(n=('sid', 'size'), k_idx=('k_idx', 'median'),
                                k_base=('k_base', 'median'), died=('died', 'mean'))
    for k, r in t.iterrows():
        print('  %-10s n=%4d | 索引值中位 %.2f | 基线中位 %.2f | 院内死亡 %.1f%%'
              % ('无复查' if k else '有复查', r.n, r.k_idx, r.k_base, 100 * r.died))
    d_nr = float(t.loc[True, 'died']) if True in t.index else np.nan
    d_rep = float(t.loc[False, 'died']) if False in t.index else np.nan
    OUT[nm] = dict(gap_by_band=gapA, med_gap=round(float(rep.t_next.median() / 60), 1),
                   grid=grid, n_norep=int(e2.norep.sum()), n_rep=int((~e2.norep).sum()),
                   died_norep=round(100 * d_nr, 1) if not np.isnan(d_nr) else None,
                   died_rep=round(100 * d_rep, 1) if not np.isnan(d_rep) else None)

# ---------- 库间差异是否被间隔解释：合并 logistic ----------
a = ev['MIMIC-IV'][ev['MIMIC-IV'].t_next.notna()].copy(); a['db'] = 0
b = ev['eICU-CRD'][ev['eICU-CRD'].t_next.notna()].copy(); b['db'] = 1
allr = pd.concat([a, b], ignore_index=True)
allr['loggap'] = np.log(allr.t_next.clip(lower=1))
allr['hi'] = (allr.k_idx >= 6.0).astype(int)
print('\n' + '=' * 108)
print('库间差异（eICU vs MIMIC）在 ≥6.0 层：是否被复查间隔解释')
try:
    from sklearn.linear_model import LogisticRegression
    for feats, lab in [(['db'], '仅数据库'),
                       (['db', 'k_idx'], '+ 索引值'),
                       (['db', 'k_idx', 'loggap'], '+ 复查间隔'),
                       (['db', 'k_idx', 'loggap', 'hi', 'db*hi'], '+ 间隔 + 索引≥6.0 及交互')]:
        X = allr[['db', 'k_idx', 'loggap', 'hi']].copy()
        X['db*hi'] = X.db * X.hi
        X = X[feats].astype(float).values
        m = LogisticRegression(max_iter=3000).fit(X, allr.confirm.astype(int).values)
        print('  %-40s OR(eICU) = %.2f' % (lab, np.exp(m.coef_[0][0])))
except Exception as ex:
    print('  回归不可用', str(ex)[:60])
json.dump(OUT, open('out/k3_phase2d.json', 'w'), ensure_ascii=False, indent=1)
print('\n写出 out/k3_phase2d.json')
