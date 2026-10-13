# -*- coding: utf-8 -*-
"""
K3 阶段①：阈值定义的新发高钾，有多少是真的？（v2：缓存序列 + 向量化）
队列与 K2 一致；三档定义 apparent / confirmed / sustained
"""
import duckdb, pandas as pd, numpy as np, json, os, warnings
warnings.filterwarnings('ignore')
M = 'D:/shujuku/mimic-iv-3.1'; E = 'D:/shujuku/EICU 2.0'
T = lambda p: "read_csv_auto('{}', strict_mode=false, ignore_errors=true)".format(p)
con = duckdb.connect(); con.execute('SET threads=6')
KLO, KHI, BASE, HORIZON = 1.0, 15.0, 1440, 10080
CACHE = {'mimic': 'out/k3_k_series_mimic.pkl', 'eicu': 'out/k3_k_series_eicu.pkl'}


def extract():
    if all(os.path.exists(v) for v in CACHE.values()):
        print('使用缓存序列'); return {k: pd.read_pickle(v) for k, v in CACHE.items()}
    print('抽取 MIMIC-IV …')
    km = con.execute(f"""
    WITH icu AS (SELECT stay_id, subject_id, hadm_id, intime,
                        ROW_NUMBER() OVER (PARTITION BY hadm_id ORDER BY intime) AS rn
                 FROM {T(M + '/icu/icustays.csv')}
                 WHERE regexp_matches(first_careunit,'CCU|CVICU')),
    co AS (SELECT * FROM icu WHERE rn = 1)
    SELECT c.stay_id AS sid, l.valuenum AS k, DATE_DIFF('minute', c.intime, l.charttime) AS t
    FROM co c JOIN {T(M + '/hosp/labevents.csv')} l
      ON l.subject_id = c.subject_id AND l.hadm_id = c.hadm_id
    WHERE l.itemid = 50971 AND l.valuenum BETWEEN {KLO} AND {KHI}
      AND l.charttime >= c.intime - INTERVAL 24 HOUR AND l.charttime <= c.intime + INTERVAL 7 DAY
    """).df()
    print('抽取 eICU-CRD …')
    ke = con.execute(f"""
    WITH co AS (SELECT patientunitstayid FROM {T(E + '/patient.csv')}
                WHERE regexp_matches(unittype,'Cardiac ICU|CCU|CSICU|CTICU'))
    SELECT co.patientunitstayid AS sid, l.labresult AS k, l.labresultoffset AS t
    FROM co JOIN {T(E + '/lab.csv')} l USING (patientunitstayid)
    WHERE lower(l.labname) = 'potassium' AND l.labresult BETWEEN {KLO} AND {KHI}
      AND l.labresultoffset BETWEEN -{BASE} AND {HORIZON}
    """).df()
    pd.to_pickle(km, CACHE['mimic']); pd.to_pickle(ke, CACHE['eicu'])
    return {'mimic': km, 'eicu': ke}


SER = extract()
OUT = {}
for nm, d in [('MIMIC-IV', SER['mimic']), ('eICU-CRD', SER['eicu'])]:
    d = d.sort_values(['sid', 't']).reset_index(drop=True)
    print('\n' + '=' * 104); print(nm); print('=' * 104)
    base = d[d.t <= BASE].groupby('sid').k.max().rename('k_base')
    post_n = d[d.t > BASE].groupby('sid').size().rename('n_post')
    coh = pd.concat([base, post_n], axis=1)
    at_risk = coh[(coh.k_base < 5.5) & (coh.n_post > 0)]
    print('有血钾记录 %s 例；基线可达 %s 例；基线最高 <5.5 且 24h 后有测量 %s 例'
          % (format(d.sid.nunique(), ','), format(len(base.dropna()), ','), format(len(at_risk), ',')))

    # ---- 事件表（向量化）：首次 ≥5.5
    p = d[d.t > BASE]
    pos = p.index[p.k >= 5.5].to_numpy()
    if nm == 'MIMIC-IV':
        pass
    first_pos = p.iloc[np.where(p.k.values >= 5.5)[0]].groupby('sid').head(1).index  # 保序
    rows = []
    grp_all = {sid: g for sid, g in d.groupby('sid', sort=False)}
    for sid in p.loc[first_pos, 'sid'].values:
        g = grp_all[sid]; post = g[g.t > BASE]
        idx = post[post.k >= 5.5].iloc[0]
        after = post[post.t > idx.t]
        a24 = after[after.t <= idx.t + BASE]
        before = g[g.t < idx.t]
        rows.append(dict(sid=sid, k_idx=idx.k, t_idx=idx.t,
                         k_prev=before.k.iloc[-1] if len(before) else np.nan,
                         n_rep_24h=len(a24),
                         k_next=a24.k.iloc[0] if len(a24) else np.nan,
                         t_next=(a24.t.iloc[0] - idx.t) if len(a24) else np.nan,
                         confirm_24h=bool(len(a24) and a24.k.iloc[0] >= 5.5),
                         sustained=bool(len(a24) and (a24.k >= 5.5).all())))
    evd = pd.DataFrame(rows)
    evd = evd[evd.sid.isin(at_risk.index)].reset_index(drop=True)   # 必须限定在基线正常队列内
    n_coh, n_app = len(at_risk), len(evd)
    rep = evd[evd.n_rep_24h > 0]
    print('\n--- 三档发生率（分母 %s 例）---' % format(n_coh, ','))
    print('  apparent  首次 ≥5.5           %5d 例  %.2f%%' % (n_app, 100 * n_app / n_coh))
    print('  confirmed 24h 内复查仍 ≥5.5   %5d 例  %.2f%%   = apparent 的 %.1f%%'
          % (evd.confirm_24h.sum(), 100 * evd.confirm_24h.sum() / n_coh, 100 * evd.confirm_24h.sum() / n_app))
    print('  sustained 24h 内全部 ≥5.5     %5d 例  %.2f%%   = apparent 的 %.1f%%'
          % (evd.sustained.sum(), 100 * evd.sustained.sum() / n_coh, 100 * evd.sustained.sum() / n_app))
    print('  24h 内无复查                  %5d 例  = apparent 的 %.1f%%'
          % ((evd.n_rep_24h == 0).sum(), 100 * (evd.n_rep_24h == 0).sum() / n_app))
    if len(rep):
        rev = rep[~rep.confirm_24h]
        print('  一过性（复查 <5.5）           %5d 例  = 有复查者的 %.1f%%；复查血钾中位 %.2f'
              % (len(rev), 100 * len(rev) / len(rep), rev.k_next.median()))
    band_rows = []
    print('\n--- 按索引值分层 ---')
    for lo, hi, lab in [(5.5, 6.0, '5.5–5.9'), (6.0, 6.5, '6.0–6.4'), (6.5, 15.1, '≥6.5')]:
        s = evd[(evd.k_idx >= lo) & (evd.k_idx < hi)]; sr = s[s.n_rep_24h > 0]
        r = dict(band=lab, n=int(len(s)), share=round(100 * len(s) / n_app, 1), rechecked=int(len(sr)),
                 confirm=round(100 * float(sr.confirm_24h.mean()), 1) if len(sr) else None,
                 sustained=round(100 * float(sr.sustained.mean()), 1) if len(sr) else None)
        band_rows.append(r)
        print('  %-10s n=%5d (%4.1f%%) | 复查 %5d | 确认 %s%% | 持续 %s%%'
              % (lab, r['n'], r['share'], r['rechecked'], r['confirm'], r['sustained']))
    gap_rows = []
    print('\n--- 按复查间隔分层 ---')
    for lo, hi, lab in [(0, 360, '≤6 h'), (360, 720, '6–12 h'), (720, BASE, '12–24 h')]:
        s = rep[(rep.t_next > lo) & (rep.t_next <= hi)]
        r = dict(gap=lab, n=int(len(s)), confirm=round(100 * float(s.confirm_24h.mean()), 1) if len(s) else None,
                 med_next=round(float(s.k_next.median()), 2) if len(s) else None)
        gap_rows.append(r)
        print('  %-8s n=%5d | 确认 %s%% | 复查血钾中位 %s' % (lab, r['n'], r['confirm'], r['med_next']))

    dd = d.copy(); dd['dk'] = dd.groupby('sid').k.diff(); dd['dt'] = dd.groupby('sid').t.diff()
    pr = dd[(dd.dt > 0) & (dd.dt <= BASE)]
    sd_w = float(pr.dk.std() / np.sqrt(2)); m_w = float(pr.k.mean())
    cv_w = 100 * sd_w / m_w; rcv = 1.96 * np.sqrt(2) * cv_w / 100 * m_w
    med = d.groupby('sid').k.median().rename('k_med')
    e2 = evd.join(med, on='sid')
    beyond = float(100 * ((e2.k_idx - e2.k_med) > rcv).mean())
    dkp = (evd.k_idx - evd.k_prev).dropna()
    print('\n--- 噪声框架 ---')
    print('  ≤24h 相邻配对 %s 对 | within-patient SD %.3f mmol/L | CV %.2f%% | RCV(95%%) %.2f mmol/L'
          % (format(len(pr), ','), sd_w, cv_w, rcv))
    print('  apparent 中索引值 > 本人中位数 + RCV 者仅 %.1f%%' % beyond)
    print('  索引值 − 上一次值：中位 %+.2f mmol/L；≤RCV 者 %.1f%%' % (dkp.median(), 100 * (dkp <= rcv).mean()))
    OUT[nm] = dict(n_units=int(d.sid.nunique()), n_base=int(len(base.dropna())), n_coh=n_coh,
                   apparent=n_app, confirmed=int(evd.confirm_24h.sum()), sustained=int(evd.sustained.sum()),
                   apparent_pct=round(100 * n_app / n_coh, 2),
                   confirmed_pct=round(100 * int(evd.confirm_24h.sum()) / n_coh, 2),
                   sustained_pct=round(100 * int(evd.sustained.sum()) / n_coh, 2),
                   confirm_share=round(100 * int(evd.confirm_24h.sum()) / n_app, 1),
                   sustained_share=round(100 * int(evd.sustained.sum()) / n_app, 1),
                   no_rep=int((evd.n_rep_24h == 0).sum()),
                   revert_share_of_rechecked=round(100 * float((~rep.confirm_24h).mean()), 1) if len(rep) else None,
                   bands=band_rows, gaps=gap_rows, sd_within=round(sd_w, 3), cv_within=round(cv_w, 2),
                   rcv=round(rcv, 2), beyond_pct=round(beyond, 1),
                   dkp_median=round(float(dkp.median()), 2),
                   dkp_within_rcv_pct=round(float(100 * (dkp <= rcv).mean()), 1))
json.dump(OUT, open('out/k3_phase1.json', 'w'), ensure_ascii=False, indent=1)
print('\n写出 out/k3_phase1.json')
