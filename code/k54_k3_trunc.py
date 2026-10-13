# -*- coding: utf-8 -*-
"""补算并落盘：被截断分类窗 vs 完整分类窗 事件的院内死亡率（正文 §3.6 引用值）"""
import duckdb, pandas as pd, numpy as np, sys, warnings
warnings.filterwarnings('ignore')
W = sys.argv[1] if len(sys.argv) > 1 else 'MIMIC'
DB = 'MIMIC-IV' if W == 'MIMIC' else 'eICU-CRD'
M='D:/shujuku/mimic-iv-3.1'; E='D:/shujuku/EICU 2.0'
T=lambda p:"read_csv_auto('{}', strict_mode=false, ignore_errors=true)".format(p)
con=duckdb.connect(); con.execute('SET threads=4')
BASE=1440; H=4320
CIC="regexp_matches(first_careunit,'CCU|CVICU')"
CIT="regexp_matches(unittype,'Cardiac ICU|CCU|CSICU|CTICU')"
if W=='MIMIC':
    q=f"""WITH icu AS (SELECT stay_id, subject_id, hadm_id, intime,
         ROW_NUMBER() OVER (PARTITION BY hadm_id ORDER BY intime) AS rn
         FROM {T(M+'/icu/icustays.csv')} WHERE {CIC}), co AS (SELECT * FROM icu WHERE rn=1)
SELECT co.stay_id AS sid, DATE_DIFF('minute', co.intime, a.dischtime) AS los_hosp_min,
       a.hospital_expire_flag AS died_inhosp FROM co
JOIN {T(M+'/hosp/admissions.csv')} a ON a.hadm_id=co.hadm_id"""
    ser='out/k3_k_series_mimic.pkl'
else:
    q=f"""SELECT patientunitstayid AS sid, TRY_CAST(hospitaldischargeoffset AS DOUBLE) AS los_hosp_min,
       CASE WHEN lower(coalesce(hospitaldischargestatus,'')) LIKE 'expired%' THEN 1 ELSE 0 END AS died_inhosp
       FROM {T(E+'/patient.csv')} WHERE {CIT}"""
    ser='out/k3_k_series_eicu.pkl'
oc=con.execute(q).df()
d=pd.read_pickle(ser).sort_values(['sid','t']).reset_index(drop=True)
med=d.groupby('sid').k.median()
rows=[]
for sid,g in d.groupby('sid',sort=False):
    pre=g[g.t<=BASE]
    if len(pre)==0 or float(pre.k.max())>=5.5: continue
    post=g[(g.t>BASE)&(g.t<=H)]
    if len(post)==0: continue
    pos=post[post.k>=5.5]
    if len(pos)==0: continue
    idx=pos.iloc[0]
    rows.append(dict(sid=int(sid), idx_t=float(idx.t), complete=int(idx.t+BASE<=H)))
ev=pd.DataFrame(rows).merge(oc,on='sid',how='left')
ev['los_hosp_min']=pd.to_numeric(ev.los_hosp_min,errors='coerce')
ev=ev[ev.los_hosp_min>H]
a=ev[ev.complete==1]; b=ev[ev.complete==0]
out=pd.DataFrame([dict(db=DB, group='complete_window', n=len(a), died=int(a.died_inhosp.sum()),
                       mort_pct=round(100*float(a.died_inhosp.mean()),1)),
                  dict(db=DB, group='truncated_window', n=len(b), died=int(b.died_inhosp.sum()),
                       mort_pct=round(100*float(b.died_inhosp.mean()),1))])
print(out.to_string(index=False))
out.to_csv('out/k54_trunc_%s.csv'%W.lower(), index=False)
print('已写 out/k54_trunc_%s.csv'%W.lower())
