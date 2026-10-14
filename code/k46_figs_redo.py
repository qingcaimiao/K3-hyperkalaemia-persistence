# -*- coding: utf-8 -*-
"""K3 重绘 Figure 1（状态定义与发生率）与 Figure 4（森林图）——按五档口径。
数字全部读自已验证的 Table 2 / k39_or.json。
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch


import numpy as np, pandas as pd, json
plt.rcParams.update({'font.family': 'Arial', 'font.size': 7.5, 'axes.linewidth': 0.7,
                     'xtick.major.width': 0.7, 'ytick.major.width': 0.7, 'axes.spines.top': False,
                     'axes.spines.right': False, 'savefig.dpi': 600, 'figure.dpi': 600})
OUT = 'out/figures_k3'
CM = '#1f4e79'; CE = '#c0504d'
orj = json.load(open('out/k39_or.json', encoding='utf-8'))

# ---------------- Figure 1 ----------------
fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(7.4, 3.2), gridspec_kw={'width_ratios': [1.25, 1]})
ax0.axis('off'); ax0.set_xlim(0, 10); ax0.set_ylim(0, 10)
ax0.add_patch(FancyBboxPatch((0.2, 8.5), 9.4, 1.25, boxstyle='round,pad=0.15', fc='#eef3f8', ec='#9a9a9a', lw=0.7))
ax0.text(4.9, 9.12, 'Cardiac ICU admission\nbaseline K$^+$ < 5.5 mmol/L, measured after hour 24', ha='center', va='center', fontsize=6.4)
ax0.add_patch(FancyBboxPatch((0.2, 6.5), 4.3, 1.3, boxstyle='round,pad=0.15', fc='#f2f2f2', ec='#9a9a9a', lw=0.7))
ax0.text(2.35, 7.15, 'no episode\nK$^+$ stays < 5.5', ha='center', va='center', fontsize=6.4)
ax0.add_patch(FancyBboxPatch((5.2, 6.5), 4.4, 1.3, boxstyle='round,pad=0.15', fc='#fdeceb', ec='#9a9a9a', lw=0.7))
ax0.text(7.4, 7.15, 'APPARENT episode\nfirst K$^+$ ≥ 5.5 after hour 24', ha='center', va='center', fontsize=6.4)
sub = [(0.2, 'TRANSIENT', 'every value in\nthe next 24 h < 5.5', '#eaf2ea'),
       (2.62, 'INTERMITTENT', 'some but not all\nvalues ≥ 5.5', '#fdf5e6'),
       (5.04, 'SUSTAINED', 'every value in\nthe next 24 h ≥ 5.5', '#fbe9e7'),
       (7.46, 'UNCLASSIFIED', 'not re-measured\nwithin 24 h', '#f4f4f4')]
for x, t, s, c in sub:
    ax0.add_patch(FancyBboxPatch((x, 3.8), 2.32, 2.1, boxstyle='round,pad=0.12', fc=c, ec='#9a9a9a', lw=0.7))
    ax0.text(x + 1.16, 5.45, t, ha='center', va='center', fontsize=6.1, fontweight='bold')
    ax0.text(x + 1.16, 4.6, s, ha='center', va='center', fontsize=5.9)
for x1 in [1.36, 3.78, 6.20, 8.62]:
    ax0.add_patch(FancyArrowPatch((7.4, 6.5), (x1, 5.9), arrowstyle='-|>', mutation_scale=7,
                                  lw=0.6, color='#707070', connectionstyle='arc3,rad=0.0'))
ax0.add_patch(FancyArrowPatch((5.0, 9.75), (2.35, 7.8), arrowstyle='-|>', mutation_scale=7, lw=0.6, color='#707070'))
ax0.add_patch(FancyArrowPatch((5.0, 9.75), (7.4, 7.8), arrowstyle='-|>', mutation_scale=7, lw=0.6, color='#707070'))
ax0.text(0.15, 9.95, 'A', fontweight='bold', fontsize=9)

labels = ['Apparent', 'Transient', 'Intermittent', 'Sustained', 'Unclassified']
mv = [5.82, 3.72, 0.93, 0.42, 0.74]
ev = [3.46, 1.71, 0.59, 0.35, 0.82]
x = np.arange(5); w = 0.36
ax1.bar(x - w / 2, mv, w, color=CM, label='MIMIC-IV')
ax1.bar(x + w / 2, ev, w, color=CE, label='eICU-CRD')
assert len(mv) == len(ev), 'k46 MIMIC/eICU 柱数不一致: %d vs %d' % (len(mv), len(ev))
for i, (a, b) in enumerate(zip(mv, ev)):
    ax1.text(i - w / 2, a + 0.12, '%.2f' % a, ha='center', fontsize=5.8)
    ax1.text(i + w / 2, b + 0.12, '%.2f' % b, ha='center', fontsize=5.8)
ax1.set_xticks(x); ax1.set_xticklabels(labels, fontsize=5.9, rotation=20, ha='right')
ax1.set_ylabel('Incidence (% of cohort)'); ax1.set_ylim(0, 6.9)
ax1.legend(frameon=False, fontsize=6.6)
ax1.text(-0.18, 1.07, 'B', transform=ax1.transAxes, fontweight='bold', fontsize=9)
import os as _os
if not _os.environ.get('K3_ALLOW_STALE_FIG'):
    print('  [skip] Figure 1（含硬编码 3.72 的旧版） 现由 k78_fig1_redo.py 生成，本脚本默认不再写出（设 K3_ALLOW_STALE_FIG=1 可强制）')
else:
    fig.tight_layout(); fig.savefig(OUT + '/FigK3_1_definition.png', bbox_inches='tight')
plt.close(fig)

# ---------------- Figure 4 forest ----------------
fig, ax = plt.subplots(figsize=(5.6, 2.7))
rows = [('No episode', None), ('Transient', 'transient'), ('Intermittent', 'intermittent'), ('Sustained', 'sustained')]
for k, (nm, colc) in enumerate([('MIMIC-IV', CM), ('eICU-CRD', CE)]):
    mod = orj[nm + '|72 h']
    for i, (lab, key) in enumerate(rows):
        y = (3 - i) * 1.0 - 0.14 + 0.28 * k
        if key is None:
            ax.plot([1], [y], marker='s', ms=4, color=colc)
            ax.text(1.06, y, '1.00 (reference)', va='center', fontsize=6.0)
        else:
            d = mod[key]
            ax.plot([d['or_']], [y], marker='o', ms=4.5, color=colc)
            ax.plot([d['ci'][0], d['ci'][1]], [y, y], lw=1.1, color=colc)
            ax.text(24, y, '%.2f (%.2f–%.2f)' % (d['or_'], d['ci'][0], d['ci'][1]), va='center', fontsize=6.0)
ax.set_xscale('log'); ax.set_xlim(0.8, 24)
ax.set_xticks([1, 2, 5, 10]); ax.set_xticklabels(['1', '2', '5', '10'])
ax.set_yticks([3, 2, 1, 0]); ax.set_yticklabels([r[0] for r in rows], fontsize=7)
ax.axvline(1, color='#999999', lw=0.7, ls=':')
ax.set_xlabel('Adjusted odds ratio for in-hospital death (72-h landmark)')
h = [plt.Line2D([], [], color=CM, marker='o', ls='', ms=4, label='MIMIC-IV'),
     plt.Line2D([], [], color=CE, marker='o', ls='', ms=4, label='eICU-CRD')]
ax.legend(handles=h, frameon=False, fontsize=6.4, loc='lower center', bbox_to_anchor=(0.5, 1.005), ncol=2)
fig.tight_layout(); fig.savefig(OUT + '/FigK3_5_forest.png', bbox_inches='tight')   # 重编号后的新名; plt.close(fig)
print('写出 out/figures_k3/FigK3_5_forest.png（Figure 5，重编号后的新名）')
