# -*- coding: utf-8 -*-
"""K3 STROBE 流程图（FigK3_6），数字取自 out/k41_flow.csv"""
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
plt.rcParams['font.family'] = 'Arial'

F = pd.read_csv('out/k41_flow.csv')
print(F.to_string(index=False))

fig, axes = plt.subplots(1, 2, figsize=(11.5, 7.4))
for ax, (_, f), col in zip(axes, F.iterrows(), ['#2166ac', '#b2182b']):
    ax.set_xlim(0, 10); ax.set_ylim(0, 11.2); ax.axis('off')
    ax.set_title(str(f['db']), fontsize=13, fontweight='bold', color=col, pad=10)
    steps = [
        (9.8, '%s cardiac ICU admissions with\nat least one potassium measurement' % '{:,}'.format(int(f['with_k']))),
        (7.9, 'Excluded: no potassium in the\n±24 h baseline window (%s)' % '{:,}'.format(int(f['no_baseline']))),
        (6.0, 'Excluded: baseline potassium\n≥5.5 mmol/L (%s)' % '{:,}'.format(int(f['baseline_ge55']))),
        (4.1, 'Excluded: no potassium measurement\nafter hour 24 (%s)' % '{:,}'.format(int(f['no_post24']))),
        (2.2, 'Analysis cohort\n%s admissions' % '{:,}'.format(int(f['cohort']))),
    ]
    for y, txt in steps:
        box = FancyBboxPatch((1.0, y - 0.78), 8.0, 1.56,
                             boxstyle="round,pad=0.02,rounding_size=0.12",
                             linewidth=1.4, edgecolor=col, facecolor='white')
        ax.add_patch(box)
        ax.text(5.0, y, txt, ha='center', va='center', fontsize=9.4, color='#1a1a1a')
    for y in [8.85, 6.95, 5.05, 3.15]:
        ax.annotate('', xy=(5.0, y - 0.22), xytext=(5.0, y + 0.22),
                    arrowprops=dict(arrowstyle='-|>', color=col, lw=1.5))
    for y in [7.9, 6.0, 4.1]:
        ax.plot([1.0, 0.30], [y, y], color=col, lw=1.0, ls='--')
fig.suptitle('Figure 6. Derivation of the analysis cohort (STROBE)', fontsize=13.5, fontweight='bold', y=0.975)
fig.tight_layout(rect=[0, 0, 1, 0.955])
fig.savefig('out/figures_k3/FigK3_6_flow.png', dpi=600, facecolor='white')
print('写出 out/figures_k3/FigK3_6_flow.png')
