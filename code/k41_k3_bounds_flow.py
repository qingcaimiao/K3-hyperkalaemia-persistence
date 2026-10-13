# -*- coding: utf-8 -*-
"""K3 补充：五档定义下的未分类边界 + STROBE 队列流程图（FigK3_6）"""
import duckdb, pandas as pd, numpy as np, json, warnings
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
warnings.filterwarnings('ignore')
plt.rcParams['font.family'] = 'Arial'

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
       a.hospital_expire_flag AS died_inhosp
FROM co JOIN {T(M + '/hosp/admissions.csv')} a ON a.hadm_id=co.hadm_id"""
om = con.execute(qm).df()
qe = f"""SELECT patientunitstayid AS sid, TRY_CAST(hospitaldischargeoffset AS DOUBLE) AS los_hosp_min,
       CASE WHEN lower(coalesce(hospitaldischargestatus,'')) LIKE 'expired%' THEN 1 ELSE 0 END AS died_inhosp
       FROM {T(E + '/patient.csv')} WHERE {CIT}"""
oe = con.execute(qe).df()

bounds_rows, flow_rows = [], []
for nm, dpkl, oc in [('MIMIC-IV', 'out/k3_k_series_mimic.pkl', om),
                     ('eICU-CRD', 'out/k3_k_series_eicu.pkl', oe)]:
    d = pd.read_pickle(dpkl).sort_values(['sid', 't']).reset_index(drop=True)
    n_all = d.sid.nunique()
    # 流程分列
    pre = d[d.t <= BASE].groupby('sid').k.max()
    post24 = d[d.t > BASE].groupby('sid').size()
    has_pre = pre.index; no_baseline = n_all - len(has_pre)
    ge55 = int((pre >= 5.5).sum())
    valid = pre[pre < 5.5].index
    no_post = int(len([s for s in valid if s not in set(post24.index)]))
    coh_n = len(valid) - no_post
    assert n_all - no_baseline - ge55 - no_post == coh_n
    flow_rows.append(dict(db=nm, with_k=n_all, no_baseline=no_baseline, baseline_ge55=ge55,
                          no_post24=no_post, cohort=coh_n))
    print('%s: %s − %s − %s − %s = %s' % (nm, f'{n_all:,}', no_baseline, f'{ge55:,}', f'{no_post:,}', f'{coh_n:,}'))

    for H, lab in [(4320, '72 h'), (10080, '7 d')]:
        rr = []
        for sid, g in d.groupby('sid', sort=False):
            p = g[g.t <= BASE]
            if len(p) == 0 or float(p.k.max()) >= 5.5: continue
            po = g[(g.t > BASE) & (g.t <= H)]
            if len(po) == 0: continue
            pos = po[po.k >= 5.5]
            if len(pos) == 0: continue
            idx = pos.iloc[0]
            a = po[(po.t > idx.t) & (po.t <= idx.t + BASE)]
            if len(a) == 0: grp = 'unclassified'
            elif bool((a.k >= 5.5).all()): grp = 'sustained'
            elif bool((a.k >= 5.5).any()): grp = 'intermittent'
            else: grp = 'transient'
            rr.append(dict(sid=int(sid), grp=grp))
        lc = pd.DataFrame(rr).merge(oc, on='sid', how='left')
        lc = lc[lc.los_hosp_min > H]
        nu = int((lc.grp == 'unclassified').sum())
        n_t = int((lc.grp == 'transient').sum()); d_t = int(lc[lc.grp == 'transient'].died_inhosp.sum())
        n_s = int((lc.grp == 'sustained').sum()); d_s = int(lc[lc.grp == 'sustained'].died_inhosp.sum())
        b_t = round(100 * (d_t + nu) / max(n_t + nu, 1), 1)
        b_s = round(100 * (d_s + nu) / max(n_s + nu, 1), 1)
        print('   %s %-6s n=%s | unclassified %d | 全按一过性 %.1f%% | 全按持续 %.1f%%'
              % (nm, lab, f'{len(lc):,}', nu, b_t, b_s))
        bounds_rows.append(dict(db=nm, landmark=lab, n_landmark=len(lc), n_unclassified=nu,
                                bound_as_transient=b_t, bound_as_sustained=b_s))

pd.DataFrame(bounds_rows).to_csv('out/k41_bounds.csv', index=False, encoding='utf-8-sig')
pd.DataFrame(flow_rows).to_csv('out/k41_flow.csv', index=False, encoding='utf-8-sig')

# ---------------- STROBE 流程图 ----------------
fig, axes = plt.subplots(1, 2, figsize=(11.5, 7.2))
F = flow_rows
for ax, f, col in zip(axes, F, ['#2166ac', '#b2182b']):
    ax.set_xlim(0, 10); ax.set_ylim(0, 11); ax.axis('off')
    ax.set_title(f['db'], fontsize=13, fontweight='bold', color=col, pad=8)
    steps = [
        (10.0, '%s cardiac ICU admissions with\n≥1 potassium measurement' % f['{:,}'.format(f['with_k'])]),
        (8.2, 'Excluded: no potassium in\nthe ±24 h baseline window\n(%s)' % '{:,}'.format(f['no_baseline'])),
        (6.4, 'Excluded: baseline potassium\n≥5.5 mmol/L (%s)' % '{:,}'.format(f['baseline_ge55'])),
        (4.6, 'Excluded: no potassium\nmeasurement after hour 24 (%s)' % '{:,}'.format(f['no_post24'])),
        (2.8, 'Analysis cohort\n%s admissions' % '{:,}'.format(f['cohort'])),
    ]
    for y, txt in steps:
        box = FancyBboxPatch((1.2, y - 0.72), 7.6, 1.5, boxstyle="round,pad=0.02,rounding_size=0.12",
                             linewidth=1.3, edgecolor=col, facecolor='white')
        ax.add_patch(box)
        ax.text(5.0, y, txt, ha='center', va='center', fontsize=9.2, color='#1a1a1a')
    for y in [9.1, 7.3, 5.5, 3.7]:
        ax.annotate('', xy=(5.0, y - 0.05), xytext=(5.0, y + 0.15),
                    arrowprops=dict(arrowstyle='-|>', color=col, lw=1.4))
    # 右侧旁支箭头
    for y in [8.2, 6.4, 4.6]:
        ax.plot([1.2, 0.45], [y, y], color=col, lw=1.1, ls='--')
fig.suptitle('Figure 6. Study flow (STROBE)', fontsize=13.5, fontweight='bold', y=0.98)
fig.tight_layout(rect=[0, 0, 1, 0.955])
fig.savefig('out/figures_k3/FigK3_6_flow.png', dpi=400, facecolor='white')
print('\n写出 out/figures_k3/FigK3_6_flow.png / k41_bounds.csv / k41_flow.csv')
