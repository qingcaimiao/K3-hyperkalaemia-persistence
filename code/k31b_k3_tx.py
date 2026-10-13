# -*- coding: utf-8 -*-
"""
K3 阶段②b：治疗中介 —— 索引高钾之后、复查之前的降钾治疗能否解释"低确认率"，
尤其是 MIMIC 在 ≥6.5 层确认率反常偏低（eICU 为最高的剂量梯度）。
治疗类别（两库同义）：
  1 insulin_glucose（胰岛素/葡萄糖）
  2 binder（钾结合剂：聚苯乙烯磺酸钠 / 环硅酸锆钠 / patiromer；eICU 的 kayexalate 标签）
  3 iv_calcium（静脉钙剂）
  4 bicarbonate（碳酸氢钠）
  5 rrt（肾脏替代治疗 / 透析）
窗口：[t_idx − 6h, t_next]（结果回报前后都可能已处理）；另报 [t_idx, t_next] 的窄口径
"""
import duckdb, pandas as pd, numpy as np, json, os, warnings
warnings.filterwarnings('ignore')
M = 'D:/shujuku/mimic-iv-3.1'; E = 'D:/shujuku/EICU 2.0'
T = lambda p: "read_csv_auto('{}', strict_mode=false, ignore_errors=true)".format(p)
con = duckdb.connect(); con.execute('SET threads=6')
B6 = 360

INS = (223257, 223258, 223259, 223260, 223261, 223262, 229299, 229619)
CAL = (221456, 228317, 229640, 229618)
BIC = (221211, 227533)
RRT_PROC = (225802, 225803, 225805, 225809, 225955, 225441)
RRT_CHART = (227290,)
RRT_INP = (227525, 227536, 230044)


def extract_mimic():
    if os.path.exists('out/k3_tx_mimic.pkl'):
        return pd.read_pickle('out/k3_tx_mimic.pkl')
    ICU = f"""WITH icu AS (SELECT stay_id, hadm_id, intime,
                   ROW_NUMBER() OVER (PARTITION BY hadm_id ORDER BY intime) AS rn
                 FROM {T(M + '/icu/icustays.csv')} WHERE regexp_matches(first_careunit,'CCU|CVICU')),
              co AS (SELECT * FROM icu WHERE rn = 1)"""
    parts = []
    for cat, ids, tbl in [('insulin_glucose', INS, 'inputevents'), ('iv_calcium', CAL, 'inputevents'),
                          ('bicarbonate', BIC, 'inputevents')]:
        q = f"""{ICU}
        SELECT co.stay_id AS sid, DATE_DIFF('minute', co.intime, x.starttime) AS off, '{cat}' AS cat
        FROM co JOIN {T(M + '/icu/' + tbl + '.csv')} x ON x.stay_id = co.stay_id
        WHERE x.itemid IN ({','.join(map(str, ids))})"""
        parts.append(con.execute(q).df())
    for cat, ids, tbl, col in [('rrt', RRT_PROC, 'procedureevents', 'starttime'),
                               ('rrt', RRT_CHART, 'chartevents', 'charttime')]:
        q = f"""{ICU}
        SELECT co.stay_id AS sid, DATE_DIFF('minute', co.intime, x.{col}) AS off, '{cat}' AS cat
        FROM co JOIN {T(M + '/icu/' + tbl + '.csv')} x ON x.stay_id = co.stay_id
        WHERE x.itemid IN ({','.join(map(str, ids))})"""
        parts.append(con.execute(q).df())
    q = f"""{ICU}
    SELECT co.stay_id AS sid, DATE_DIFF('minute', co.intime, x.starttime) AS off, 'rrt' AS cat
    FROM co JOIN {T(M + '/icu/inputevents.csv')} x ON x.stay_id = co.stay_id
    WHERE x.itemid IN ({','.join(map(str, RRT_INP))})"""
    parts.append(con.execute(q).df())
    q = f"""{ICU}
    SELECT co.stay_id AS sid, DATE_DIFF('minute', co.intime, p.starttime) AS off, 'binder' AS cat
    FROM co JOIN {T(M + '/hosp/prescriptions.csv')} p ON p.hadm_id = co.hadm_id
    WHERE regexp_matches(lower(coalesce(p.drug,'')), 'polystyrene|zirconium cyclosilicate|patiromer')"""
    parts.append(con.execute(q).df())
    q = f"""{ICU}
    SELECT co.stay_id AS sid, DATE_DIFF('minute', co.intime, p.starttime) AS off, 'insulin_glucose' AS cat
    FROM co JOIN {T(M + '/hosp/prescriptions.csv')} p ON p.hadm_id = co.hadm_id
    WHERE lower(coalesce(p.drug,'')) = 'insulin (regular) for hyperkalemia'"""
    parts.append(con.execute(q).df())
    tx = pd.concat(parts, ignore_index=True).dropna(subset=['off'])
    tx['off'] = tx.off.astype(float)
    pd.to_pickle(tx, 'out/k3_tx_mimic.pkl')
    return tx


def extract_eicu():
    if os.path.exists('out/k3_tx_eicu.pkl'):
        return pd.read_pickle('out/k3_tx_eicu.pkl')
    CO = f"""WITH co AS (SELECT patientunitstayid FROM {T(E + '/patient.csv')}
              WHERE regexp_matches(unittype,'Cardiac ICU|CCU|CSICU|CTICU'))"""
    q = f"""{CO}
    SELECT co.patientunitstayid AS sid, t.treatmentoffset AS off,
           CASE WHEN t.treatmentstring ILIKE '%treatment of hyperkalemia|insulin / glucose%' THEN 'insulin_glucose'
                WHEN t.treatmentstring ILIKE '%treatment of hyperkalemia|kayexalate%' THEN 'binder'
                WHEN t.treatmentstring ILIKE '%treatment of hyperkalemia|intravenous calcium%' THEN 'iv_calcium'
                WHEN t.treatmentstring ILIKE '%treatment of hyperkalemia|dialysis%' THEN 'rrt'
                WHEN t.treatmentstring ILIKE '%renal|medications|bicarbonate%' THEN 'bicarbonate'
           END AS cat
    FROM co JOIN {T(E + '/treatment.csv')} t ON t.patientunitstayid = co.patientunitstayid
    WHERE t.treatmentstring ILIKE '%treatment of hyperkalemia%'
       OR t.treatmentstring ILIKE '%renal|medications|bicarbonate%'"""
    tx = con.execute(q).df().dropna(subset=['cat'])
    q2 = f"""{CO}
    SELECT co.patientunitstayid AS sid, t.treatmentoffset AS off, 'rrt' AS cat
    FROM co JOIN {T(E + '/treatment.csv')} t ON t.patientunitstayid = co.patientunitstayid
    WHERE t.treatmentstring ILIKE 'renal|dialysis%'
      AND NOT regexp_matches(lower(t.treatmentstring),'insertion|catheter|access surgery|shunt|peritoneal dialysis|sled')"""
    tx = pd.concat([tx, con.execute(q2).df()], ignore_index=True).drop_duplicates()
    tx['off'] = tx.off.astype(float)
    pd.to_pickle(tx, 'out/k3_tx_eicu.pkl')
    return tx


CATS = ['insulin_glucose', 'binder', 'iv_calcium', 'bicarbonate', 'rrt']
OUT = {}
for nm, evf, txf, kind in [('MIMIC-IV', 'out/k3_events_mimic.pkl', 'out/k3_tx_mimic.pkl', 'm'),
                           ('eICU-CRD', 'out/k3_events_eicu.pkl', 'out/k3_tx_eicu.pkl', 'e')]:
    ev = pd.read_pickle(evf)
    tx = extract_mimic() if kind == 'm' else extract_eicu()
    print('\n' + '=' * 106); print(nm, '| 治疗记录', format(len(tx), ','), '条；覆盖住院',
          format(tx.sid.nunique(), ','), '例'); print('=' * 106)
    print('  各类治疗记录数与涉及住院数：')
    for c in CATS:
        s = tx[tx.cat == c]
        print('    %-16s %8s 条 / %7s 例' % (c, format(len(s), ','), format(s.sid.nunique(), ',')))

    ev = ev[ev.t_next.notna()].copy().reset_index(drop=True)   # 中介路径只在"确有复查"处可观察
    ev['win_hi'] = ev.t_idx + ev.t_next
    for c in CATS:
        sub = tx.loc[tx.cat == c, ['sid', 'off']]
        m = ev[['sid', 't_idx', 'win_hi']].merge(sub, on='sid', how='left')
        m['hit'] = (m.off >= m.t_idx - B6) & (m.off <= m.win_hi)
        m['nhit'] = (m.off >= m.t_idx) & (m.off <= m.win_hi)
        agg = m.groupby('sid').agg(tx=('hit', 'any'), tn=('nhit', 'any'))
        ev['tx_' + c] = ev.sid.map(agg['tx']).fillna(False).astype(bool)
        ev['tn_' + c] = ev.sid.map(agg['tn']).fillna(False).astype(bool)
    ev['tx_any'] = ev[['tx_' + c for c in CATS]].any(axis=1)
    ev['tx_n'] = ev[['tx_' + c for c in CATS]].sum(axis=1)
    print('\n  索引窗口 [t_idx−6h, t_idx+t_next] 内至少一项降钾治疗：%d 例（%.1f%%）'
          % (ev.tx_any.sum(), 100 * ev.tx_any.mean()))
    for c in CATS:
        print('    %-16s %6d 例（%4.1f%%）| 其中该治疗者确认率 %s%% vs 未用者 %s%%'
              % (c, ev['tx_' + c].sum(), 100 * ev['tx_' + c].mean(),
                 round(100 * float(ev.loc[ev['tx_' + c], 'confirm'].mean()), 1),
                 round(100 * float(ev.loc[~ev['tx_' + c], 'confirm'].mean()), 1)))

    print('\n--- 按索引值分层：确认率 无治疗 vs 有治疗（宽窗口）---')
    band_out = []
    for lo, hi, lab in [(5.5, 6.0, '5.5–5.9'), (6.0, 6.5, '6.0–6.4'), (6.5, 15.1, '≥6.5')]:
        s = ev[(ev.k_idx >= lo) & (ev.k_idx < hi)]
        r = dict(band=lab, n=int(len(s)),
                 conf_notx=round(100 * float(s.loc[~s.tx_any, 'confirm'].mean()), 1) if (~s.tx_any).sum() else None,
                 n_notx=int((~s.tx_any).sum()),
                 conf_tx=round(100 * float(s.loc[s.tx_any, 'confirm'].mean()), 1) if s.tx_any.sum() else None,
                 n_tx=int(s.tx_any.sum()),
                 conf_all=round(100 * float(s.confirm.mean()), 1))
        band_out.append(r)
        print('  %-8s n=%4d | 无治疗 %4d 例 确认 %5s%% | 有治疗 %4d 例 确认 %5s%% | 合计 %5s%%'
              % (lab, r['n'], r['n_notx'], r['conf_notx'], r['n_tx'], r['conf_tx'], r['conf_all']))

    print('\n--- 治疗强度（窗口内类别数）与确认率 ---')
    inten = []
    for k in range(0, int(ev.tx_n.max()) + 1):
        s = ev[ev.tx_n == k]
        if len(s) < 20: continue
        inten.append(dict(n_tx=k, n=int(len(s)), med_k_idx=round(float(s.k_idx.median()), 2),
                          confirm=round(100 * float(s.confirm.mean()), 1)))
        print('  %d 类治疗：n=%4d | 索引值中位 %.2f | 确认率 %5.1f%%' % (k, len(s), s.k_idx.median(), 100 * s.confirm.mean()))

    # 索引值分层内的治疗校正：logistic 回归 confirm ~ tx_any + k_idx（库内，bootstrap CI）
    try:
        from sklearn.linear_model import LogisticRegression
        X = ev[['tx_any', 'k_idx']].astype(float).values
        y = ev.confirm.astype(int).values
        lr = LogisticRegression(max_iter=3000).fit(X, y)
        b0 = float(lr.coef_[0][0])
        rng = np.random.default_rng(11)
        bs = []
        for _ in range(500):
            i = rng.integers(0, len(y), len(y))
            if len(np.unique(y[i])) < 2: continue
            try:
                bs.append(float(LogisticRegression(max_iter=3000).fit(X[i], y[i]).coef_[0][0]))
            except Exception:
                pass
        lo, hi = np.percentile(bs, [2.5, 97.5])
        print('\n  logistic：confirm ~ 治疗 + 索引值 → OR(有治疗) = %.2f (95%% bootstrap CI %.2f–%.2f)'
              % (np.exp(b0), np.exp(lo), np.exp(hi)))
        OUT[nm] = dict(n_report=len(ev), tx_share=round(100 * float(ev.tx_any.mean()), 1),
                       bands=band_out, intensity=inten,
                       or_tx=round(float(np.exp(b0)), 2),
                       or_tx_ci=[round(float(np.exp(lo)), 2), round(float(np.exp(hi)), 2)],
                       cat_shares={c: round(100 * float(ev['tx_' + c].mean()), 1) for c in CATS})
    except Exception as ex:
        print('  回归不可用：', str(ex)[:100])
        OUT[nm] = dict(n_report=len(ev), tx_share=round(100 * float(ev.tx_any.mean()), 1), bands=band_out,
                       intensity=inten, cat_shares={c: round(100 * float(ev['tx_' + c].mean()), 1) for c in CATS})
    ev.to_pickle('out/k3_events_tx_%s.pkl' % kind)

json.dump(OUT, open('out/k3_phase2b.json', 'w'), ensure_ascii=False, indent=1)
print('\n写出 out/k3_phase2b.json')
