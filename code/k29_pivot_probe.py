# -*- coding: utf-8 -*-
"""
k29: 换方向可行性探针 —— 「血钾阈值单次测量的可靠性/错误分类」能否成立
只用一个 CTE 重新抽取两库 CICU 住院的全部血钾序列（-24h ~ +7d），不做任何新数据获取。
输出：测量密度、短期配对变异、RCV 超限比例、5.5 阈值首crossing 的"确认率"
"""
import duckdb, pandas as pd, numpy as np, json, warnings
warnings.filterwarnings('ignore')
M = 'D:/shujuku/mimic-iv-3.1'; E = 'D:/shujuku/EICU 2.0'
T = lambda p: "read_csv_auto('{}', strict_mode=false, ignore_errors=true)".format(p)
con = duckdb.connect(); con.execute('SET threads=6')

print('抽取 MIMIC-IV 血钾序列 ...')
q1 = f"""
WITH icu AS (SELECT stay_id, subject_id, hadm_id, intime,
                    ROW_NUMBER() OVER (PARTITION BY hadm_id ORDER BY intime) AS rn
             FROM {T(M + '/icu/icustays.csv')}
             WHERE regexp_matches(first_careunit,'CCU|CVICU')),
co AS (SELECT * FROM icu WHERE rn = 1)
SELECT c.stay_id, l.valuenum AS k,
       DATE_DIFF('minute', c.intime, l.charttime) AS off_min
FROM co c JOIN {T(M + '/hosp/labevents.csv')} l
  ON l.subject_id = c.subject_id AND l.hadm_id = c.hadm_id
WHERE l.itemid = 50971 AND l.valuenum IS NOT NULL AND l.valuenum > 0
  AND l.charttime >= c.intime - INTERVAL 24 HOUR AND l.charttime <= c.intime + INTERVAL 7 DAY
"""
km = con.execute(q1).df()

print('抽取 eICU-CRD 血钾序列 ...')
q2 = f"""
WITH co AS (SELECT patientunitstayid FROM {T(E + '/patient.csv')}
            WHERE regexp_matches(unittype,'Cardiac ICU|CCU|CSICU|CTICU'))
SELECT co.patientunitstayid AS stay_id, l.labresult AS k, l.labresultoffset AS off_min
FROM co JOIN {T(E + '/lab.csv')} l USING (patientunitstayid)
WHERE lower(l.labname) = 'potassium' AND l.labresult IS NOT NULL AND l.labresult > 0
  AND l.labresultoffset BETWEEN -1440 AND 10080
"""
ke = con.execute(q2).df()

OUT = {}
for nm, d, idc in [('MIMIC-IV', km, 'stay_id'), ('eICU-CRD', ke, 'stay_id')]:
    d = d.sort_values([idc, 'off_min'])
    g = d.groupby(idc)
    nk = g.size()
    print('\n' + '=' * 100); print(nm, '：', len(nk), '例，血钾记录', len(d), '条')
    print('  每例测量次数：中位 %d（IQR %d–%d，最多 %d）；≥2 次 %.1f%%，≥3 次 %.1f%%'
          % (nk.median(), nk.quantile(.25), nk.quantile(.75), nk.max(),
             100 * (nk >= 2).mean(), 100 * (nk >= 3).mean()))
    # 相邻配对（同一次住院内）
    d['prev_k'] = g['k'].shift(1); d['prev_t'] = g['off_min'].shift(1)
    d['dt_h'] = (d.off_min - d.prev_t) / 60.0; d['dk'] = d.k - d.prev_k
    p = d.dropna(subset=['dk'])
    res = {}
    for win in [6, 12, 24]:
        s = p[(p.dt_h > 0) & (p.dt_h <= win)]
        if len(s) < 100: continue
        sd = s.dk.std(); m = s[['k', 'prev_k']].mean(axis=1).mean()
        cv = 100 * sd / (np.sqrt(2) * m)      # 单次测量 CV（差值 SD / √2 / 均值）
        rcv = 1.96 * np.sqrt(2) * sd / np.sqrt(2)   # RCV = 1.96·√2·CV_analytic（此处用差值 SD）
        res[win] = dict(pairs=int(len(s)), sd_diff=round(float(sd), 3), mean_k=round(float(m), 2),
                        cv_pct=round(float(cv), 2), frac_exceed_rcv=round(float((s.dk.abs() > rcv).mean() * 100), 1),
                        frac_exceed_05=round(float((s.dk.abs() > 0.5).mean() * 100), 1))
        print('  相邻配对 ≤%dh：%s 对 | 差值 SD %.3f mmol/L | 推得单次 CV %.2f%% | 超过 RCV 的比例 %.1f%% | |ΔK|>0.5 的比例 %.1f%%'
              % (win, format(len(s), ','), sd, cv, res[win]['frac_exceed_rcv'], res[win]['frac_exceed_05']))
    # 5.5 阈值首 crossing 的确认率（24h 后起算，取首次 ≥5.5）
    ev = d[(d.off_min > 1440) & (d.k >= 5.5)]
    first = ev.groupby(idc).first()
    nxt = {}
    for sid, row in first.iterrows():
        sub = d[(d[idc] == sid) & (d.off_min > row.off_min)]
        if len(sub) == 0: nxt[sid] = np.nan; continue
        r = sub.iloc[0]
        dt = (r.off_min - row.off_min) / 60
        nxt[sid] = r.k if dt <= 24 else np.nan
    nr = pd.Series(nxt)
    ok = nr.dropna()
    print('  ≥5.5 首 crossing：%d 例；其中 24h 内有复查者 %d 例' % (len(first), len(ok)))
    if len(ok):
        print('     复查仍 ≥5.5（确认）%.1f%% | 复查 <5.5（一过性）%.1f%%；确认者复查血钾中位 %.2f，一过性者 %.2f'
              % (100 * (ok >= 5.5).mean(), 100 * (ok < 5.5).mean(),
                 ok[ok >= 5.5].median(), ok[ok < 5.5].median()))
    OUT[nm] = dict(n_patients=int(len(nk)), n_records=int(len(d)), med_meas=float(nk.median()),
                   pct_ge2=round(100 * float((nk >= 2).mean()), 1), pct_ge3=round(100 * float((nk >= 3).mean()), 1),
                   pairs=res, n_first_crossing=int(len(first)), n_rechecked=int(len(ok)),
                   pct_confirmed=round(100 * float((ok >= 5.5).mean()), 1) if len(ok) else None)
json.dump(OUT, open('out/k29_pivot.json', 'w'), ensure_ascii=False, indent=1)
print('\n写出 out/k29_pivot.json')
