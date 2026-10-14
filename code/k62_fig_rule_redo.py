# -*- coding: utf-8 -*-
"""单独重绘 Figure 6（复查规则收率）。原因：面板 B 的 2 h 数据标签（MIMIC 6.3）
在 ylim 上界 6 时会溢出坐标区、与面板标题重叠。此处把上界提到 7 并重出。
输出：out/figures_k3/FigK3_6_rule.png（600 dpi）
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json, os
plt.rcParams.update({'font.family': 'Arial', 'font.size': 7.5, 'axes.linewidth': 0.7,
                     'xtick.major.width': 0.7, 'ytick.major.width': 0.7, 'axes.spines.top': False,
                     'axes.spines.right': False, 'savefig.dpi': 600, 'figure.dpi': 600})
OUT = 'out/figures_k3'; os.makedirs(OUT, exist_ok=True)
CM = '#1f4e79'; CE = '#c0504d'
ph4 = json.load(open('out/k3_phase4.json', encoding='utf-8'))

fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.2, 2.6))
lab = ['2 h', '4 h', '6 h', '12 h', '24 h']
for nm, c in [('MIMIC-IV', CM), ('eICU-CRD', CE)]:
    cov = [r['coverage'] for r in ph4[nm]['rules']]
    nnr = [r['nnr'] for r in ph4[nm]['rules']]
    a1.plot(range(5), cov, marker='o', ms=4, color=c, label=nm)
    a2.plot(range(5), nnr, marker='o', ms=4, color=c, label=nm)
    for i, v in enumerate(cov):
        a1.text(i, v + 1.6, '%.0f' % v, ha='center', fontsize=5.8, color=c)
    for i, v in enumerate(nnr):
        a2.text(i, v + 0.10, '%.1f' % v, ha='center', fontsize=5.8, color=c)
a1.set_xticks(range(5)); a1.set_xticklabels(lab); a1.set_ylabel('Re-measured within window (%)')
a1.set_ylim(0, 95); a1.set_title('A  Current practice', fontsize=7.5, loc='left', fontweight='bold')
a1.legend(frameon=False, fontsize=6.5)
a2.set_xticks(range(5)); a2.set_xticklabels(lab); a2.set_ylabel('Repeat measurements per confirmed episode')
a2.set_ylim(0, 7); a2.set_title('B  Yield of the rule', fontsize=7.5, loc='left', fontweight='bold')
a2.legend(frameon=False, fontsize=6.5)
fig.tight_layout(); fig.savefig(OUT + '/FigK3_6_rule.png', bbox_inches='tight'); plt.close(fig)
print('写出', OUT + '/FigK3_6_rule.png',
      '| 2h nnr =', [r['nnr'] for r in ph4['MIMIC-IV']['rules']][0])
