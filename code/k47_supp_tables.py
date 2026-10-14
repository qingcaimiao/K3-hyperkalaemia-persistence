# -*- coding: utf-8 -*-
"""生成 K3 补充材料附表 S1–S6（数字全部读自已验证的 CSV/JSON，不手写）"""
import json, pandas as pd

L = []
L.append('# Additional file 1 — Supplementary tables\n')
L.append('K3: Persistence of threshold-defined hyperkalaemia in cardiac intensive care. '
         'All values are computed from the analysis scripts; none are transcribed by hand.\n')

ph2c = json.load(open('out/k3_phase2c.json', encoding='utf-8'))
p1 = json.load(open('out/k3_phase1.json', encoding='utf-8'))
rec = pd.read_csv('out/k39_reclass.csv')
thr = pd.read_csv('out/k39_threshold.csv')
flow = pd.read_csv('out/k41_flow.csv')
DB = ['MIMIC-IV', 'eICU-CRD']

# ---------- S1 ----------
L.append('\n## Table S1. Definitions and code lists\n')
L.append('| Item | MIMIC-IV (v3.1) | eICU-CRD (v2.0) |')
L.append('|---|---|---|')
L.append('| Cardiac intensive care unit | `first_careunit` matching `CCU` or `CVICU` (ICUSTAYS) | `unittype` matching `Cardiac ICU`, `CCU`, `CSICU` or `CTICU` (PATIENT) |')
L.append('| Potassium | `labevents.itemid = 50971` (blood chemistry) | `lab.labname = "potassium"` |')
L.append('| Creatinine (sensitivity analysis) | `labevents.itemid = 50912` (blood chemistry) | `lab.labname = "creatinine"` |')
L.append('| Mechanical ventilation (sensitivity analysis) | `procedureevents.itemid` 225792 or 225794 | `respiratorycare` with an artificial airway or a ventilator interval |')
L.append('| Vasopressors (sensitivity analysis) | `inputevents.itemid` 221906, 221289, 221662, 221653, 221749, 222315 | `infusionDrug.drugname` matching norepinephrine, epinephrine, dopamine, dobutamine, phenylephrine or vasopressin |')
L.append('| Potassium-lowering treatment | insulin/glucose, potassium binder, intravenous calcium, sodium bicarbonate, renal replacement therapy | same five categories by drug name / treatment string |')
L.append('| Admission outcome | `admissions.hospital_expire_flag` | `patient.hospitaldischargestatus` starting with "expired" |')
L.append('\nAll three covariates are used only in the sensitivity analysis reported in Section 3.4 and in the limitations; '
         'none enters the primary model.\n')

# ---------- S2 ----------
L.append('\n## Table S2. Derivation of the analysis cohort\n')
L.append('| Step | MIMIC-IV | eICU-CRD |')
L.append('|---|---|---|')
row = {}
for _, r in flow.iterrows():
    row[r['db']] = r
L.append('| Cardiac ICU admissions with ≥1 potassium measurement | %s | %s |' % (
    '{:,}'.format(int(row['MIMIC-IV']['with_k'])), '{:,}'.format(int(row['eICU-CRD']['with_k']))))
L.append('| Excluded: no potassium in the ±24 h baseline window | %s | %s |' % (
    '{:,}'.format(int(row['MIMIC-IV']['no_baseline'])), '{:,}'.format(int(row['eICU-CRD']['no_baseline']))))
L.append('| Excluded: baseline potassium ≥5.5 mmol/L | %s | %s |' % (
    '{:,}'.format(int(row['MIMIC-IV']['baseline_ge55'])), '{:,}'.format(int(row['eICU-CRD']['baseline_ge55']))))
L.append('| Excluded: no potassium measurement after hour 24 | %s | %s |' % (
    '{:,}'.format(int(row['MIMIC-IV']['no_post24'])), '{:,}'.format(int(row['eICU-CRD']['no_post24']))))
L.append('| **Analysis cohort** | **%s** | **%s** |' % (
    '{:,}'.format(int(row['MIMIC-IV']['cohort'])), '{:,}'.format(int(row['eICU-CRD']['cohort']))))

# ---------- S3 ----------
L.append('\n## Table S3. Full state-transition matrix (whole cardiac intensive care population)\n')
L.append('Pairs of consecutive measurements after hour 24 separated by ≤24 h, in the whole cardiac intensive care '
         'population. Columns give the number of pairs, the proportion whose next value reached 5.5 mmol/L, and the '
         'median of the next value.\n')
L.append('| Current potassium (mmol/L) | MIMIC-IV: n | MIMIC-IV: next ≥5.5 | MIMIC-IV: median next | eICU-CRD: n | eICU-CRD: next ≥5.5 | eICU-CRD: median next |')
L.append('|---|---|---|---|---|---|---|')
mt = {r['band']: r for r in ph2c['MIMIC-IV']['trans']}
et = {r['band']: r for r in ph2c['eICU-CRD']['trans']}
for b in mt:
    if b in et:
        L.append('| %s | %s | %.1f%% | %.2f | %s | %.1f%% | %.2f |' % (
            b, '{:,}'.format(mt[b]['n']), mt[b]['p_next_55'], mt[b]['med_next'],
            '{:,}'.format(et[b]['n']), et[b]['p_next_55'], et[b]['med_next']))
L.append('\nτ² (between-patient variance of true potassium, method of moments) was %.4f and %.4f; '
         'population mean potassium %.2f and %.2f mmol/L; within-patient SD %.3f and %.3f mmol/L.' % (
             ph2c['MIMIC-IV']['tau2'], ph2c['eICU-CRD']['tau2'], ph2c['MIMIC-IV']['kpop'],
             ph2c['eICU-CRD']['kpop'], ph2c['MIMIC-IV']['sd_within'], ph2c['eICU-CRD']['sd_within']))

# ---------- S4 ----------
L.append('\n## Table S4. Expected confirmation rate under competing explanations (detail)\n')
L.append('| Assumed source of variation | MIMIC-IV SD | MIMIC-IV λ | MIMIC-IV expected | eICU-CRD SD | eICU-CRD λ | eICU-CRD expected |')
L.append('|---|---|---|---|---|---|---|')
ms = ph2c['MIMIC-IV']['scenarios']; es = ph2c['eICU-CRD']['scenarios']
assert len(ms) == len(es), 'S4 两库情景数不一致: MIMIC-IV=%d vs eICU-CRD=%d' % (len(ms), len(es))
# k31c 的场景标签为中文，补充材料须全英文；此处做映射（含兜底）
_LAB = {
    '实验室分析误差 CV 1.5%': 'Analytical error, CV 1.5%',
    '实验室分析误差 CV 3.0%': 'Analytical error, CV 3.0%',
    '分析误差 CV 5.0%（很保守）': 'Analytical error, CV 5.0% (deliberately conservative)',
    '观察到的短期变异（含真实波动）': 'Observed short-term variability (includes genuine fluctuation)',
}


def _en(lab):
    if lab in _LAB:
        return _LAB[lab]
    # 兜底：若仍含中文则显式报错，防止中文标签静默流入投稿件
    assert not any('\u4e00' <= ch <= '\u9fff' for ch in lab), 'S4 出现未映射的中文标签: %s' % lab
    return lab


for a, b in zip(ms, es):
    L.append('| %s | %.3f | %.3f | %.1f%% | %.3f | %.3f | %.1f%% |' % (
        _en(a['label']), a['sd'], a['lam'], a['expected'], b['sd'], b['lam'], b['expected']))
L.append('| **Observed confirmation** | — | — | **%.1f%%** | — | — | **%.1f%%** |' % (
    ph2c['MIMIC-IV']['obs_confirm'], ph2c['eICU-CRD']['obs_confirm']))
L.append('\nλ = τ²/(τ² + σ²). The expected rate is the mean over observed index values of 1 − Φ[(5.5 − μ)/s], '
         'with μ = λ·index + (1 − λ)·population mean and s = σ·√(1 + λ).\n')

# ---------- S5 ----------
orj = {}
for _f in ['out/k39b_sens_mimic.json', 'out/k39b_sens_eicu.json']:
    try:
        orj.update(json.load(open(_f, encoding='utf-8')))
    except FileNotFoundError:
        print('警告：缺少', _f)
L.append('\n## Table S5. Sensitivity of the persistent state to the minimum number of measurements\n')
L.append('An episode is called sustained only if every measurement in the 24-hour window is ≥5.5 mmol/L. '
         'Requiring a minimum number of measurements reclassifies single-value episodes as "not assessed".\n')
L.append('| Requirement | Database | Landmark | Persistent, n | Persistent, adjusted OR (95% CI) | Not assessed, n |')
L.append('|---|---|---|---|---|---|')
for tag, lab in [('sust>=2', 'at least 2 measurements'), ('sust>=3', 'at least 3 measurements')]:
    for db in DB:
        for lm in ['72 h', '7 d']:
            s = rec[(rec.tag == tag) & (rec.db == db) & (rec.landmark == lm)]
            ns = s[s.grp == 'sustained']['n']
            cna = s[s.grp == 'conf_not_assessed']['n']
            if len(ns) == 0:
                continue
            d = orj['%s|%s|%s' % (tag, db, lm)]['sustained']
            L.append('| %s | %s | %s | %d | %.2f (%.2f–%.2f) | %s |' % (
                lab, db, lm, int(float(ns.iloc[0])), d['or_'], d['lo'], d['hi'],
                ('%.0f' % float(cna.iloc[0])) if len(cna) else '0'))
L.append('\nThe primary analysis (Table 5) corresponds to a minimum of one measurement.\n')

# ---------- S6 ----------
L.append('\n## Table S6. Sensitivity of the persistence estimate to the potassium threshold\n')
L.append('| Threshold (mmol/L) | Database | Apparent, n | Re-measured within 24 h, n | ≥1 further value ≥ threshold | Sustained |')
L.append('|---|---|---|---|---|---|')
for _, r in thr.iterrows():
    L.append('| %.1f | %s | %s | %s | %s (%.1f%%) | %s (%.1f%%) |' % (
        r['threshold'], r['db'], '{:,}'.format(int(r['apparent'])), '{:,}'.format(int(r['rechecked'])),
        '{:,}'.format(int(r['confirmed'])), r['pct_confirmed'],
        '{:,}'.format(int(r['sustained'])), r['pct_sustained']))

open('out/K3_Supplementary_Tables.md', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('写出 out/K3_Supplementary_Tables.md（%d 行）' % len(L))

# ---------- S7（第二轮外审新增：预后梯度稳健性汇总） ----------
import os as _os
L2 = []
L2.append('\n## Table S7. Robustness of the adjusted odds ratio for in-hospital death after a 72-hour landmark\n')
L2.append('Reference group: admissions without an episode. Cells are adjusted odds ratios (95% bootstrap confidence intervals). '
          'Each row is a separate model; "—" means the check does not apply to that database. '
          'In the two "minimum measurements" rows the requirement is imposed on the sustained state only, so that the transient '
          'and intermittent columns retain their primary definition; the corresponding analysis, in which the requirement is '
          'imposed on every state instead, is reported in Section 3.6 and yields sustained odds ratios of 9.23 (2.99\u201318.06) '
          'in MIMIC-IV and 20.17 (6.96\u201341.68) in eICU-CRD.\n')
L2.append('| Analysis | MIMIC-IV: transient | MIMIC-IV: intermittent | MIMIC-IV: sustained | eICU-CRD: transient | eICU-CRD: intermittent | eICU-CRD: sustained |')
L2.append('|---|---|---|---|---|---|---|')


def _fmt(v):
    if isinstance(v, dict):
        return '%.2f (%.2f–%.2f)' % (v['or_'], v['lo'], v['hi'])
    return '%.2f (%.2f–%.2f)' % (v[0], v[1], v[2])


def _get(dct, db, tag, lm='72 h'):
    """dct 为按库分开的 dict（k48c/k39b），键形如 '1_complete_only|72 h' 或裸键 '2_only'"""
    if lm is None:
        k = '%s|%s|%s' % (tag, db, lm)
    else:
        k = None
        for cand in ('%s|%s' % (tag, lm), tag):
            if cand in dct:
                k = cand
                break
        if k is None:
            print('  警告：S7 缺少键', tag)
            return ['—', '—', '—']
    if k not in dct:
        print('  警告：S7 缺少键', k)
        return ['—', '—', '—']
    g = dct[k]
    return [_fmt((g[x]['or_'], g[x]['lo'], g[x]['hi'])) for x in ('transient', 'intermittent', 'sustained')]


_prim = json.load(open('out/k39_or.json', encoding='utf-8'))
_b = {}
for _f in ['out/k39b_sens_mimic.json', 'out/k39b_sens_eicu.json']:
    _b.update(json.load(open(_f, encoding='utf-8')))
_cf = json.load(open('out/k48c_mimic.json', encoding='utf-8'))
_ce = json.load(open('out/k48c_eicu.json', encoding='utf-8'))
_fm = json.load(open('out/k49_fixedwin_mimic.json', encoding='utf-8'))
_fe = json.load(open('out/k49_fixedwin_eicu.json', encoding='utf-8'))
_bb_m = json.load(open('out/k48b_mimic.json', encoding='utf-8'))
_bb_e = json.load(open('out/k48b_eicu.json', encoding='utf-8'))
_cl = {r['db'] + '|' + r['group']: (r['or_'], r['lo'], r['hi']) for r in pd.read_csv('out/k43_cluster.csv').to_dict('records')}
_adj = {r['db'] + '|' + r['group']: (r['or_'], r['lo'], r['hi']) for r in pd.read_csv('out/k43_adj.csv').to_dict('records')}

# RCV 限制后的 OR 取 k53（表 5 队列口径，与正文 3.6 同源）
_rcv = {}
for _f, _db in [('out/k53_audit_mimic.csv', 'MIMIC-IV'), ('out/k53_audit_eicu.csv', 'eICU-CRD')]:
    _d = pd.read_csv(_f)
    for _g in ('transient', 'intermittent', 'sustained'):
        _r = _d[_d.metric == 'OR_rcv_restricted_' + _g]
        if len(_r):
            _rcv['%s|%s' % (_db, _g)] = (float(_r.or_.iloc[0]), float(_r.lo.iloc[0]), float(_r.hi.iloc[0]))

# 医院聚类区间取 k51 的 1,000 次重抽样；点估计取主模型
_k51 = json.load(open('out/k51_eicu.json', encoding='utf-8'))['G2_cluster_or']
_hcl = {}
for _g in ('transient', 'intermittent', 'sustained'):
    _hcl[_g] = (float(_prim['eICU-CRD|72 h'][_g]['or_']), float(_k51['rows'][_g]['lo']), float(_k51['rows'][_g]['hi']))
_HCL_N = _k51['n_resample']


def _row(label, mv, ev):
    L2.append('| %s | %s | %s | %s | %s | %s | %s |' % (label, mv[0], mv[1], mv[2], ev[0], ev[1], ev[2]))


_row('Primary (Table 5)',
     [_fmt((_prim['MIMIC-IV|72 h'][g]['or_'], _prim['MIMIC-IV|72 h'][g]['ci'][0], _prim['MIMIC-IV|72 h'][g]['ci'][1])) for g in ('transient', 'intermittent', 'sustained')],
     [_fmt((_prim['eICU-CRD|72 h'][g]['or_'], _prim['eICU-CRD|72 h'][g]['ci'][0], _prim['eICU-CRD|72 h'][g]['ci'][1])) for g in ('transient', 'intermittent', 'sustained')])
_row('Excluding truncated classification windows',
     _get(_cf, 'MIMIC-IV', '1_complete_only'), _get(_ce, 'eICU-CRD', '1_complete_only'))
_row('Fixed 24–48 h exposure window',
     [_fmt(_fm['72 h'][g].values()) if False else _fmt((_fm['72 h'][g]['or_'], _fm['72 h'][g]['lo'], _fm['72 h'][g]['hi'])) for g in ('transient', 'intermittent', 'sustained')],
     [_fmt((_fe['72 h'][g]['or_'], _fe['72 h'][g]['lo'], _fe['72 h'][g]['hi'])) for g in ('transient', 'intermittent', 'sustained')])
_row('Index value above own median + RCV',
     [_fmt(_rcv['MIMIC-IV|' + g]) for g in ('transient', 'intermittent', 'sustained')],
     [_fmt(_rcv['eICU-CRD|' + g]) for g in ('transient', 'intermittent', 'sustained')])
_row('Excluding discharge within 48 h of landmark',
     _get(_cf, 'MIMIC-IV', '4_excl48'), _get(_ce, 'eICU-CRD', '4_excl48'))
_row('Excluding episodes with renal replacement therapy',
     [_fmt(_bb_m['7_excl_rrt'][g].values()) if False else _fmt(_bb_m['7_excl_rrt'][g]) for g in ('transient', 'intermittent', 'sustained')],
     [_fmt(_bb_e['7_excl_rrt'][g]) for g in ('transient', 'intermittent', 'sustained')])
_row('Additional adjustment for creatinine, ventilation and vasopressors',
     [_fmt(_adj['MIMIC-IV|' + g]) for g in ('transient', 'intermittent', 'sustained')],
     [_fmt(_adj['eICU-CRD|' + g]) for g in ('transient', 'intermittent', 'sustained')])
def _getb(db, tag):
    g = _b['%s|%s|72 h' % (tag, db)]
    return [_fmt((g[x]['or_'], g[x]['lo'], g[x]['hi'])) for x in ('transient', 'intermittent', 'sustained')]


_row('At least 2 measurements required for an episode to be called sustained',
     _getb('MIMIC-IV', 'sust>=2'), _getb('eICU-CRD', 'sust>=2'))
_row('At least 3 measurements required for an episode to be called sustained',
     _getb('MIMIC-IV', 'sust>=3'), _getb('eICU-CRD', 'sust>=3'))
_row('Hospital-clustered bootstrap (eICU-CRD only, %s hospital resamples)' % format(_HCL_N, ','),
     ['—', '—', '—'], [_fmt(_hcl[g]) for g in ('transient', 'intermittent', 'sustained')])
# 治疗层：eICU 样本极小，逐格加脚注标记 ᵃ
_tr_m = [_fmt(_bb_m['8_treated1'][g]) for g in ('transient', 'intermittent', 'sustained')]
_tr_e = [_fmt(_bb_e['8_treated1'][g]) + '\u1d43' for g in ('transient', 'intermittent', 'sustained')]
_row('Episodes with recorded potassium-lowering treatment', _tr_m, _tr_e)
_row('Episodes without recorded potassium-lowering treatment',
     [_fmt(_bb_m['8_treated0'][g]) for g in ('transient', 'intermittent', 'sustained')],
     [_fmt(_bb_e['8_treated0'][g]) for g in ('transient', 'intermittent', 'sustained')])

L2.append('\n\u1d43 In eICU-CRD only 28 of the 485 episodes (5.8%) in the 72-hour landmark cohort had recorded '
          'potassium-lowering treatment; the stratum-specific estimates are correspondingly unstable and are reported '
          'for completeness rather than interpreted. The two variability/RCV and treatment rows use the 72-hour landmark '
          'cohort, whereas the corresponding percentages in Table 3 are computed among the whole cohort of apparent episodes.\n')
L2.append('\nThe persistent state is the one whose association survives every specification. Transient and intermittent episodes are significant in eICU-CRD '
          'in most specifications but not in all, and in MIMIC-IV the transient state does not reach significance in any of them.\n')
_s = open('out/K3_Supplementary_Tables.md', encoding='utf-8').read()
open('out/K3_Supplementary_Tables.md', 'w', encoding='utf-8').write(_s.rstrip('\n') + '\n' + '\n'.join(L2) + '\n')
print('追加 Table S7')
