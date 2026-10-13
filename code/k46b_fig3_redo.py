# -*- coding: utf-8 -*-
"""K3 稿件 5 张主图（Arial，600 dpi，全英文标注；数据全部现算或读自已验证的结果文件）"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np, pandas as pd, json, os
plt.rcParams.update({'font.family': 'Arial', 'font.size': 7.5, 'axes.linewidth': 0.7,
                     'xtick.major.width': 0.7, 'ytick.major.width': 0.7, 'axes.spines.top': False,
                     'axes.spines.right': False, 'savefig.dpi': 600, 'figure.dpi': 600})
BASE = 1440
OUT = 'out/figures_k3'; os.makedirs(OUT, exist_ok=True)
SER = {'MIMIC-IV': 'out/k3_k_series_mimic.pkl', 'eICU-CRD': 'out/k3_k_series_eicu.pkl'}
CM = '#1f4e79'; CE = '#c0504d'; CG = '#7f7f7f'
ph1 = json.load(open('out/k3_phase1.json', encoding='utf-8'))
ph3b = json.load(open('out/k3_phase3b.json', encoding='utf-8'))
ph4 = json.load(open('out/k3_phase4.json', encoding='utf-8'))
ph2c = json.load(open('out/k3_phase2c.json', encoding='utf-8'))
# ---------------- Figure 3 ----------------
fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.5))
for ax, nm in zip(axes[:2], SER):
    d = pd.read_pickle(SER[nm]).sort_values(['sid', 't'])
    dk = d.copy(); dk['dk'] = dk.groupby('sid').k.diff(); dk['dt'] = dk.groupby('sid').t.diff()
    pr = dk[(dk.dt > 0) & (dk.dt <= BASE)]
    sd = pr.dk.std() / np.sqrt(2)
    ax.hist(pr.dk.clip(-2.5, 2.5), bins=60, color=CM if nm == 'MIMIC-IV' else CE, alpha=0.85)
    for v in (-1.96 * np.sqrt(2) * sd, 1.96 * np.sqrt(2) * sd):
        ax.axvline(v, color='k', ls='--', lw=0.8)
    ax.set_title(nm, fontsize=7.5, fontweight='bold')
    ax.set_xlabel('Difference between consecutive K$^+$ (mmol/L)')
    ax.set_ylabel('Pairs (≤24 h)')
    ax.text(0.03, 0.95, 'SD %.3f\nCV %.2f%%\nRCV$_{95}$ %.2f' % (sd, 100 * sd / d.k.mean(), 1.96 * np.sqrt(2) * sd),
            transform=ax.transAxes, va='top', fontsize=6.4)
ax = axes[2]
x = np.arange(2); w = 0.35
b1 = [ph2c['MIMIC-IV']['scenarios'][0]['expected'], ph2c['MIMIC-IV']['scenarios'][1]['expected'],
      ph2c['MIMIC-IV']['scenarios'][2]['expected'], ph2c['MIMIC-IV']['scenarios'][3]['expected'],
      ph2c['MIMIC-IV']['obs_confirm']]
b2 = [ph2c['eICU-CRD']['scenarios'][0]['expected'], ph2c['eICU-CRD']['scenarios'][1]['expected'],
      ph2c['eICU-CRD']['scenarios'][2]['expected'], ph2c['eICU-CRD']['scenarios'][3]['expected'],
      ph2c['eICU-CRD']['obs_confirm']]
xs = np.arange(5)
ax.bar(xs - 0.2, b1, 0.4, color=CM, label='MIMIC-IV')
ax.bar(xs + 0.2, b2, 0.4, color=CE, label='eICU-CRD')
ax.set_xticks(xs); ax.set_xticklabels(['CV\n1.5%', 'CV\n3%', 'CV\n5%', 'Observed\nvar.', 'Observed'], fontsize=6)
ax.set_ylabel('Expected confirmation (%)'); ax.set_ylim(0, 100)
ax.set_title('Source of variation assumed', fontsize=7.5)
ax.legend(frameon=False, fontsize=6.5)
for i, (a, b) in enumerate(zip(b1, b2)):
    ax.text(i - 0.2, a + 1.8, '%.0f' % a, ha='center', fontsize=5.6)
    ax.text(i + 0.2, b + 1.8, '%.0f' % b, ha='center', fontsize=5.6)
fig.tight_layout(); fig.savefig(OUT + '/FigK3_3_variability.png', bbox_inches='tight'); plt.close(fig)
print('FigK3_3 重绘完成')
