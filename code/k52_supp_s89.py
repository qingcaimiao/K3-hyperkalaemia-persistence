# -*- coding: utf-8 -*-
"""生成补充材料表 S8（tau^2 敏感性）与 S9（各状态 E 值），追加到 K3_Supplementary_Tables.md

S9 的 OR 一律取自**主模型**（out/k39_or.json，与正文 Table 5 同源），
RR 与 E 值由该 OR 按 VanderWeele 转换现算，避免与正文出现两套 OR。
"""
import json, io, math

jm = json.load(open('out/k50_mimic.json', encoding='utf-8'))
je = json.load(open('out/k50_eicu.json', encoding='utf-8'))
ph = json.load(open('out/k3_phase2c.json', encoding='utf-8'))
prim = json.load(open('out/k39_or.json', encoding='utf-8'))          # 主模型（= Table 5）

obs = {'MIMIC-IV': round(float(ph['MIMIC-IV']['obs_confirm']), 1),
       'eICU-CRD': round(float(ph['eICU-CRD']['obs_confirm']), 1)}
tm = {r['mult']: r for r in jm['H_tau2']['table']}
te = {r['mult']: r for r in je['H_tau2']['table']}

L = []
L.append('\n## Table S8. Sensitivity of the expected confirmation rate to the between-patient variance of true potassium\n')
L.append('The expected confirmation rate under an assumed analytical coefficient of variation scenario, when \u03c4\u00b2 (the '
         'between-patient variance of true potassium) is varied from 0.25 to 4 times its fitted value. '
         'The other terms of the reliability formulation are unchanged. Values are percentages of apparent episodes '
         'with a repeat measurement within 24 hours. The observed confirmation rate is shown for reference.\n')
L.append('| \u03c4\u00b2 | MIMIC-IV (CV 3%) | MIMIC-IV (CV 5%) | eICU-CRD (CV 3%) | eICU-CRD (CV 5%) |')
L.append('|---|---|---|---|---|')
for m in [0.25, 0.5, 1.0, 2.0, 4.0]:
    lab = '**%.2f\u00d7 (fitted)**' % m if m == 1.0 else '%.2f\u00d7' % m
    L.append('| %s | %.1f | %.1f | %.1f | %.1f |' % (lab, tm[m]['cv3'], tm[m]['cv5'], te[m]['cv3'], te[m]['cv5']))
L.append('| **Observed** | \u2014 | **%.1f** | \u2014 | **%.1f** |' % (obs['MIMIC-IV'], obs['eICU-CRD']))
L.append('\nFitted \u03c4\u00b2: %.4f (MIMIC-IV, population mean %.2f mmol/L) and %.4f (eICU-CRD, population mean %.2f mmol/L); '
         'population SDs are 0.57 and 0.54 mmol/L. Note that the fitted scenario is not the one closest to the observed '
         'rate: under a 5%% CV the fitted \u03c4\u00b2 predicts 37.8%% and 46.5%% against observed rates of %.1f%% and %.1f%%, '
         'and it is only when \u03c4\u00b2 is lowered by half that the prediction approaches the observation (19.6%% and 24.9%%). '
         'The exclusion of an isolated assay artefact therefore does not depend on the fitted \u03c4\u00b2 being exactly right, '
         'but it does depend on \u03c4\u00b2 being of the right order.\n'
         % (jm['H_tau2']['tau2'], jm['H_tau2']['kpop'], je['H_tau2']['tau2'], je['H_tau2']['kpop'],
            obs['MIMIC-IV'], obs['eICU-CRD']))


def rr_of(or_, p0):
    """VanderWeele OR -> RR"""
    return or_ / (1.0 - p0 + p0 * or_)


def evalue(rr):
    return rr + math.sqrt(rr * (rr - 1.0))


E = []
E.append('\n## Table S9. E-values for each state against the no-episode group (72-hour landmark)\n')
E.append('Odds ratios are those of the primary model (Table 5); risk ratios are obtained from them by the conversion '
         'RR = OR / (1 \u2212 p0 + p0 \u00b7 OR), where p0 is the observed mortality in the no-episode group (%.3f in MIMIC-IV '
         'and %.3f in eICU-CRD). The E-value is the minimum strength of association, on the risk-ratio scale, that an '
         'unmeasured confounder would need with both the state and death to explain the association away.\n'
         % (jm['F_evalue']['base_risk'], je['F_evalue']['base_risk']))
E.append('| State | MIMIC-IV OR | MIMIC-IV RR | MIMIC-IV E-value | eICU-CRD OR | eICU-CRD RR | eICU-CRD E-value |')
E.append('|---|---|---|---|---|---|---|')

rows = {}
for k, lab in [('transient', 'Transient'), ('intermittent', 'Intermittent'), ('sustained', 'Sustained')]:
    om = float(prim['MIMIC-IV|72 h'][k]['or_'])
    oe = float(prim['eICU-CRD|72 h'][k]['or_'])
    rm = rr_of(om, jm['F_evalue']['base_risk'])
    re = rr_of(oe, je['F_evalue']['base_risk'])
    em = evalue(rm)
    ee = evalue(re)
    rows[k] = dict(or_m=om, rr_m=round(rm, 2), e_m=round(em, 1),
                   or_e=oe, rr_e=round(re, 2), e_e=round(ee, 1))
    E.append('| %s | %.2f | %.2f | **%.1f** | %.2f | %.2f | **%.1f** |'
             % (lab, om, rm, em, oe, re, ee))

E.append('\nE-values are reported for every state, not only for the persistent one. For the persistent state an unmeasured '
         'confounder would have to be associated with both persistence and death by a risk ratio of %.1f (MIMIC-IV) or '
         '%.1f (eICU-CRD) to explain the association away, which exceeds the observed association of any covariate examined '
         'here; for the intermittent state the corresponding values are %.1f and %.1f, and for the transient state %.1f and %.1f. '
         'The E-value is a sensitivity quantity and does not replace the conventional assessment of residual confounding.\n'
         % (rows['sustained']['e_m'], rows['sustained']['e_e'],
            rows['intermittent']['e_m'], rows['intermittent']['e_e'],
            rows['transient']['e_m'], rows['transient']['e_e']))

p = 'out/K3_Supplementary_Tables.md'
s = io.open(p, encoding='utf-8').read()
# 若已存在则截断到 S8 之前，避免重复追加
for marker in ['## Table S8.', '## Table S9.']:
    if marker in s:
        s = s[:s.index('\n' + marker)] if ('\n' + marker) in s else s
        break
s = s.rstrip('\n') + '\n' + '\n'.join(L) + '\n' + '\n'.join(E) + '\n'
io.open(p, 'w', encoding='utf-8').write(s)

json.dump(rows, open('out/k52_evalues.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('已写入 Table S8 与 S9')
for k, v in rows.items():
    print('  %-13s MIMIC OR %.2f RR %.2f E %.1f | eICU OR %.2f RR %.2f E %.1f'
          % (k, v['or_m'], v['rr_m'], v['e_m'], v['or_e'], v['rr_e'], v['e_e']))
