# -*- coding: utf-8 -*-
"""K3 稿件 Table 1 所需的描述性统计（全部现算）"""
import duckdb, pandas as pd, numpy as np, json, warnings
warnings.filterwarnings('ignore')
M = 'D:/shujuku/mimic-iv-3.1'; EICU = 'D:/shujuku/EICU 2.0'
T = lambda p: "read_csv_auto('{}', strict_mode=false, ignore_errors=true)".format(p)
con = duckdb.connect(); con.execute('SET threads=6')
BASE = 1440
qm = f"""WITH icu AS (SELECT stay_id, subject_id, hadm_id, intime,
      ROW_NUMBER() OVER (PARTITION BY hadm_id ORDER BY intime) AS rn
      FROM {T(M + '/icu/icustays.csv')} WHERE regexp_matches(first_careunit,'CCU|CVICU')), co AS (SELECT * FROM icu WHERE rn=1)
SELECT co.stay_id AS sid, p.gender AS sex,
      TRY_CAST(p.anchor_age AS DOUBLE)+GREATEST(TRY_CAST(EXTRACT(YEAR FROM co.intime) AS INT)-p.anchor_year,0) AS age
FROM co JOIN {T(M + '/hosp/patients.csv')} p ON p.subject_id=co.subject_id"""
OM = con.execute(qm).df()
QE = f"""SELECT patientunitstayid AS sid, gender AS sex, TRY_CAST(age AS DOUBLE) AS age,
      TRY_CAST(unitdischargeoffset AS DOUBLE) AS ud, TRY_CAST(hospitaldischargeoffset AS DOUBLE) AS hd
FROM {T(EICU + '/patient.csv')} WHERE regexp_matches(unittype,'Cardiac ICU|CCU|CSICU|CTICU')"""
OE = con.execute(QE).df()
OUT = {}
for nm, pklf, oc in [('MIMIC-IV', 'out/k3_k_series_mimic.pkl', OM), ('eICU-CRD', 'out/k3_k_series_eicu.pkl', OE)]:
    d = pd.read_pickle(pklf).sort_values(['sid', 't'])
    kb = d[d.t <= BASE].groupby('sid').k.max()
    n_all = d.sid.nunique(); nm_per = d.groupby('sid').size()
    post = d[d.t > BASE]
    atr = kb[(kb < 5.5) & kb.index.isin(post.groupby('sid').size().index)].index
    post = post[post.sid.isin(atr)]
    f = post[post.k >= 5.5].groupby('sid', sort=False).head(1).set_index('sid')
    m = post.merge(f[['t']].rename(columns={'t': 't_idx'}).reset_index(), on='sid', how='inner')
    a = m[(m.t > m.t_idx) & (m.t <= m.t_idx + BASE)].sort_values('t')
    nx = a.groupby('sid').first()
    grp = pd.Series('no_event', index=atr)
    grp.loc[nx.index] = np.where(nx.k >= 5.5, 'confirmed', 'transient')
    sus = a.assign(ok=lambda x: x.k >= 5.5).groupby('sid').ok.all()
    grp.loc[sus[sus].index] = 'sustained'
    norep = atr.difference(nx.index).intersection(f.index)
    grp.loc[norep] = 'unknown'
    coh = grp.rename('grp').reset_index().rename(columns={'index': 'sid'}).merge(oc, on='sid', how='left')
    coh['k_base'] = coh.sid.map(kb)
    coh['n_k'] = coh.sid.map(nm_per)
    if 'ud' in coh.columns:
        coh['icu_days'] = coh.ud / 1440.0
    print('\n' + '=' * 100); print(nm); print('=' * 100)
    print('有血钾记录 %s 例；队列 %s 例；每例测量次数中位 %.0f（IQR %.0f–%.0f，最大 %d）'
          % (format(n_all, ','), format(len(atr), ','), nm_per.median(), nm_per.quantile(.25), nm_per.quantile(.75), nm_per.max()))
    print('  %-12s %7s %9s %10s %12s %10s' % ('组', 'n', '年龄中位', '男性%', '基线K中位', '测量数中位'))
    rows = []
    for g in ['no_event', 'transient', 'confirmed', 'sustained', 'unknown']:
        s = coh[coh.grp == g]
        if not len(s): continue
        r = dict(grp=g, n=int(len(s)), age=round(float(s.age.median()), 1),
                 male=round(100 * float((s.sex.astype(str).str.upper().str[0] == 'M').mean()), 1),
                 kbase=round(float(s.k_base.median()), 2), nk=round(float(s.n_k.median()), 1))
        rows.append(r)
        print('  %-12s %7d %9.1f %9.1f%% %12.2f %10.1f' % (r['grp'], r['n'], r['age'], r['male'], r['kbase'], r['nk']))
    allr = dict(n=len(atr), age=round(float(coh.age.median()), 1),
                male=round(100 * float((coh.sex.astype(str).str.upper().str[0] == 'M').mean()), 1),
                kbase=round(float(coh.k_base.median()), 2), nk=round(float(coh.n_k.median()), 1))
    print('  %-12s %7d %9.1f %9.1f%% %12.2f %10.1f' % ('全队列', allr['n'], allr['age'], allr['male'], allr['kbase'], allr['nk']))
    OUT[nm] = dict(n_all=n_all, n_coh=len(atr), nk_med=round(float(nm_per.median()), 1),
                   nk_max=int(nm_per.max()), rows=rows, all=allr)
json.dump(OUT, open('out/k3_desc.json', 'w'), ensure_ascii=False, indent=1)
print('\n写出 out/k3_desc.json')
