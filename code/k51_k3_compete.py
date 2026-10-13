# -*- coding: utf-8 -*-
"""K3 第三轮补充（二）：
[D] 竞争风险：出院 alive 作为竞争事件，Aalen-Johansen 累积死亡发生率（按状态）
[G2] OR 的医院聚类 bootstrap 提高到 1000 次（eICU）
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
SELECT co.stay_id AS sid, CAST(NULL AS BIGINT) AS hosp,
       DATE_DIFF('minute', co.intime, a.dischtime) AS los_hosp_min,
       a.hospital_expire_flag AS died_inhosp, p.gender AS sex,
       TRY_CAST(p.anchor_age AS DOUBLE)+GREATEST(TRY_CAST(EXTRACT(YEAR FROM co.intime) AS INT)-p.anchor_year,0) AS age
FROM co JOIN {T(M + '/hosp/admissions.csv')} a ON a.hadm_id=co.hadm_id
        JOIN {T(M + '/hosp/patients.csv')} p ON p.subject_id=co.subject_id"""
    ser = 'out/k3_k_series_mimic.pkl'
else:
    q = f"""SELECT patientunitstayid AS sid, hospitalid AS hosp,
       TRY_CAST(hospitaldischargeoffset AS DOUBLE) AS los_hosp_min,
       CASE WHEN lower(coalesce(hospitaldischargestatus,'')) LIKE 'expired%' THEN 1 ELSE 0 END AS died_inhosp,
       gender AS sex, TRY_CAST(age AS DOUBLE) AS age FROM {T(E + '/patient.csv')} WHERE {CIT}"""
    ser = 'out/k3_k_series_eicu.pkl'
oc = con.execute(q).df()
d = pd.read_pickle(ser).sort_values(['sid', 't']).reset_index(drop=True)
med = d.groupby('sid').k.median()
GROUPS = ['transient', 'intermittent', 'sustained']
ORD = ['no_event', 'transient', 'intermittent', 'sustained', 'unclassified']
RES = {}


def build(landmark=H):
    rows = []
    for sid, g in d.groupby('sid', sort=False):
        pre = g[g.t <= BASE]
        if len(pre) == 0 or float(pre.k.max()) >= 5.5:
            continue
        post = g[(g.t > BASE) & (g.t <= landmark)]
        if len(post) == 0:
            continue
        pos = post[post.k >= 5.5]
        if len(pos) == 0:
            rows.append(dict(sid=int(sid), grp='no_event', k_idx=np.nan,
                             k_med=float(med.get(sid, np.nan)))); continue
        idx = pos.iloc[0]
        a = post[(post.t > idx.t) & (post.t <= idx.t + BASE)]
        n = len(a); nge = int((a.k >= 5.5).sum())
        grp = ('unclassified' if n == 0 else
               ('sustained' if nge == n else ('intermittent' if nge > 0 else 'transient')))
        rows.append(dict(sid=int(sid), grp=grp, k_idx=float(idx.k),
                         k_med=float(med.get(sid, np.nan))))
    return pd.DataFrame(rows)


print('========== %s ==========' % DB)
c = build(H).merge(oc, on='sid', how='left')
c = c[pd.to_numeric(c.los_hosp_min, errors='coerce').notna()].copy()
c['los_hosp_min'] = pd.to_numeric(c.los_hosp_min, errors='coerce')

# ---------------- [D] Aalen-Johansen 竞争风险 ----------------
print('\n[D] 竞争风险（出院 alive 为竞争事件）')
surv_c = c[c.los_hosp_min > H].copy()
surv_c['t_d'] = (surv_c.los_hosp_min - H) / 1440.0        # landmark 后天数
surv_c['ev'] = np.where(surv_c.died_inhosp == 1, 1, 2)     # 1=死亡 2=存活出院
print('   landmark 后仍在院 %d；其中死亡 %d，存活出院 %d'
      % (len(surv_c), int((surv_c.ev == 1).sum()), int((surv_c.ev == 2).sum())))


def cif(times, events, grid):
    t = np.asarray(times, float); e = np.asarray(events, int)
    o = np.argsort(t); t = t[o]; e = e[o]
    surv = 1.0; cum = 0.0; res = []
    for u in np.unique(t):
        ar = int((t >= u).sum())
        if ar <= 0:
            continue
        d1 = int(((t == u) & (e == 1)).sum()); d2 = int(((t == u) & (e == 2)).sum())
        cum += surv * d1 / ar
        surv *= (1 - (d1 + d2) / ar)
        res.append((u, cum))
    return [round(100 * max([cu for u, cu in res if u <= g] or [0.0]), 2) for g in grid]


GRID = [7, 14, 30]
D = {}
for g in ORD:
    s = surv_c[surv_c.grp == g]
    if len(s) < 10:
        continue
    D[g] = dict(n=int(len(s)), died=int((s.ev == 1).sum()),
                cif7=cif(s.t_d, s.ev, [7])[0], cif14=cif(s.t_d, s.ev, [14])[0], cif30=cif(s.t_d, s.ev, [30])[0],
                crude30=round(100 * float((s.ev == 1).mean()), 2))
    print('   %-14s n=%-6d 死亡 %-5d | AJ-CIF 7d %.2f%% 14d %.2f%% 30d %.2f%% | 粗死亡 %.2f%%'
          % (g, D[g]['n'], D[g]['died'], D[g]['cif7'], D[g]['cif14'], D[g]['cif30'], D[g]['crude30']))
RES['D_cif'] = D

# ---------------- [G2] OR 的医院聚类 bootstrap（1000 次，仅 eICU） ----------------
if W == 'eICU':
    print('\n[G2] 医院聚类 bootstrap（1000 次）')
    sub = c[(c.los_hosp_min > H) & (c.grp != 'unclassified')].copy()   # 必须与表 5 的 72h landmark 口径一致
    sub['k_idx_f'] = pd.to_numeric(sub.k_idx, errors='coerce').fillna(5.4)
    sub['age_f'] = pd.to_numeric(sub.age, errors='coerce').fillna(pd.to_numeric(sub.age, errors='coerce').median())
    sub['sex_m'] = (sub.sex.astype(str).str.upper().str[0] == 'M').astype(int)
    for g in GROUPS:
        sub['g_' + g] = (sub.grp == g).astype(int)
    feats = ['g_' + g for g in GROUPS] + ['k_idx_f', 'age_f', 'sex_m']
    h = sub.hosp.astype(str).values
    uniq = np.unique(h)
    rng = np.random.default_rng(11)
    bs = []
    for _ in range(1000):
        pick = rng.choice(uniq, len(uniq), replace=True)
        idx = np.concatenate([np.where(h == p)[0] for p in pick])
        y = sub.died_inhosp.astype(int).values[idx]
        if len(np.unique(y)) < 2:
            continue
        try:
            bs.append(LogisticRegression(max_iter=4000).fit(
                sub[feats].astype(float).values[idx], y).coef_[0])
        except Exception:
            pass
    bs = np.array(bs)
    G = {}
    for j, g in enumerate(GROUPS):
        ci = np.exp(np.percentile(bs[:, j], [2.5, 97.5]))
        G[g] = dict(lo=round(float(ci[0]), 2), hi=round(float(ci[1]), 2))
        print('   %-14s 聚类 95%% CI %.2f–%.2f（%d 次成功重抽样）' % (g, ci[0], ci[1], len(bs)))
    RES['G2_cluster_or'] = dict(n_resample=int(len(bs)), rows=G)

json.dump(RES, open('out/k51_%s.json' % W.lower(), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('\n已写入 out/k51_%s.json' % W.lower())
