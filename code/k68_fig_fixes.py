# -*- coding: utf-8 -*-
"""k68: repair Figure 1B and Figure 4, and remove the hard-coded numbers.

Root cause fixed here: k46_figs_redo.py carried the incidence values as literals
(mv = [5.82, 3.72, ...]), so the label for the MIMIC transient bar kept the old
value 3.72 after the manuscript and Table 2 were corrected to 3.73.  Both figures
are now drawn from numbers **recomputed from the source series**, and the script
asserts that the recomputed values equal the ones printed in Table 2 and Table 3.
If any assertion fails the script aborts instead of drawing a wrong figure.

Figure 1B  : whole-cohort incidence of the five states  (assert vs Table 2)
Figure 4   : state-transition matrix; a right-hand annotation column now gives the
             exact collapsed probability P(next >= 5.5) per row, which is the quantity
             Table 3 reports, so the reading no longer depends on summing rounded cells.
"""
import json, sys
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams.update({'font.family': 'Arial', 'font.size': 7.5, 'axes.linewidth': 0.7,
                     'xtick.major.width': 0.7, 'ytick.major.width': 0.7,
                     'axes.spines.top': False, 'axes.spines.right': False,
                     'savefig.dpi': 600, 'figure.dpi': 600})
OUT = 'out/figures_k3'
BASE = 1440
CM = '#1f4e79'; CE = '#c0504d'
SER = {'MIMIC-IV': 'out/k3_k_series_mimic.pkl', 'eICU-CRD': 'out/k3_k_series_eicu.pkl'}

# ---------------------------------------------------------------- Table 2 / Table 3 anchors
T2 = {  # counts printed in the manuscript (used only as assertions, never as source)
 'MIMIC-IV': dict(n_coh=20322, apparent=1182, transient=757, intermittent=189,
                  sustained=86, unclassified=150,
                  pct={'Apparent': 5.82, 'Transient': 3.73, 'Intermittent': 0.93,
                       'Sustained': 0.42, 'Unclassified': 0.74}),
 'eICU-CRD': dict(n_coh=28805, apparent=997, transient=493, intermittent=169,
                  sustained=100, unclassified=235,
                  pct={'Apparent': 3.46, 'Transient': 1.71, 'Intermittent': 0.59,
                       'Sustained': 0.35, 'Unclassified': 0.82}),
}
T3_collapsed = {'MIMIC-IV': [1.8, 10.0, 32.3, 39.0],     # rows 4.5-4.9, 5.0-5.4, 5.5-5.9, >=6.0
                'eICU-CRD': [1.9, 10.7, 33.9, 54.5]}

fails = []


def ck(name, stated, got, tol):
    ok = abs(stated - got) <= tol
    print('  %-46s stated %-8s recomputed %-8s %s'
          % (name, stated, round(got, 4), 'OK' if ok else '*** MISMATCH ***'))
    if not ok:
        fails.append(name)


print('=== 1. 重算全队列五档计数（分类规则同 k39）===')
counts = {}
for nm, f in SER.items():
    d = pd.read_pickle(f).sort_values(['sid', 't'])
    tab = {'no_event': 0, 'transient': 0, 'intermittent': 0, 'sustained': 0, 'unclassified': 0}
    for sid, g in d.groupby('sid', sort=False):
        pre = g[g.t <= BASE]
        if len(pre) == 0 or float(pre.k.max()) >= 5.5:
            continue
        post = g[g.t > BASE]
        if len(post) == 0:
            continue
        pos = post[post.k >= 5.5]
        if len(pos) == 0:
            tab['no_event'] += 1; continue
        idx = pos.iloc[0]
        a = post[(post.t > idx.t) & (post.t <= idx.t + BASE)]
        if len(a) == 0:
            tab['unclassified'] += 1
        elif bool((a.k >= 5.5).all()):
            tab['sustained'] += 1
        elif bool((a.k >= 5.5).any()):
            tab['intermittent'] += 1
        else:
            tab['transient'] += 1
    counts[nm] = tab
    n = sum(tab.values())
    print('  %s: n_coh=%d' % (nm, n))
    ck('%s n_coh' % nm, T2[nm]['n_coh'], n, 0)
    for g in ['transient', 'intermittent', 'sustained', 'unclassified']:
        ck('%s %s' % (nm, g), T2[nm][g], tab[g], 0)
    app = sum(tab[g] for g in ['transient', 'intermittent', 'sustained', 'unclassified'])
    ck('%s apparent' % nm, T2[nm]['apparent'], app, 0)

if fails:
    print('\nABORT - 图 1 数字与 Table 2 对不上:', fails); sys.exit(1)

# ---------------------------------------------------------------- Figure 1
print('\n=== 2. 重绘 Figure 1 ===')
labels = ['Apparent', 'Transient', 'Intermittent', 'Sustained', 'Unclassified']
keys = ['apparent', 'transient', 'intermittent', 'sustained', 'unclassified']
TIERS = ['transient', 'intermittent', 'sustained', 'unclassified']
mv, ev = [], []
for k in keys:
    for nm, bag in (('MIMIC-IV', mv), ('eICU-CRD', ev)):
        n = sum(counts[nm].values())
        if k == 'apparent':
            num = sum(counts[nm][g] for g in TIERS)
        else:
            num = counts[nm][k]
        bag.append(100 * num / n)
assert len(labels) == len(mv) == len(ev) == 5, (
    'labels/mv/ev 长度不一致: %d/%d/%d' % (len(labels), len(mv), len(ev)))
for nm, vals in (('MIMIC-IV', mv), ('eICU-CRD', ev)):
    assert len(labels) == len(vals), '%s: labels/vals 长度不一致' % nm
    for lab, v in zip(labels, vals):
        ck('%s %s pct' % (nm, lab), T2[nm]['pct'][lab], v, 0.005)
if fails:
    print('\nABORT - 百分比与 Table 2 对不上:', fails); sys.exit(1)

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
    ax0.add_patch(FancyArrowPatch((7.4, 6.5), (x1, 5.9), arrowstyle='-|>', mutation_scale=7, lw=0.6,
                                  color='#707070', connectionstyle='arc3,rad=0.0'))
ax0.add_patch(FancyArrowPatch((5.0, 9.75), (2.35, 7.8), arrowstyle='-|>', mutation_scale=7, lw=0.6, color='#707070'))
ax0.add_patch(FancyArrowPatch((5.0, 9.75), (7.4, 7.8), arrowstyle='-|>', mutation_scale=7, lw=0.6, color='#707070'))
ax0.text(0.15, 9.95, 'A', fontweight='bold', fontsize=9)

x = np.arange(5); w = 0.36
ax1.bar(x - w / 2, mv, w, color=CM, label='MIMIC-IV')
ax1.bar(x + w / 2, ev, w, color=CE, label='eICU-CRD')
for i, (a, b) in enumerate(zip(mv, ev)):
    ax1.text(i - w / 2, a + 0.12, '%.2f' % a, ha='center', fontsize=5.8)
    ax1.text(i + w / 2, b + 0.12, '%.2f' % b, ha='center', fontsize=5.8)
ax1.set_xticks(x); ax1.set_xticklabels(labels, fontsize=5.9, rotation=20, ha='right')
ax1.set_ylabel('Incidence (% of cohort)'); ax1.set_ylim(0, 6.9)
ax1.legend(frameon=False, fontsize=6.6)
ax1.text(-0.18, 1.07, 'B', transform=ax1.transAxes, fontweight='bold', fontsize=9)
import os as _os
if _os.environ.get('K3_ALLOW_STALE_FIG'):
    fig.tight_layout(); fig.savefig(OUT + '/FigK3_1_definition.png', bbox_inches='tight')
else:
    print('  [skip] Figure 1 现由 k78_fig1_redo.py 生成，本脚本默认不再写出（设 K3_ALLOW_STALE_FIG=1 可强制）')
plt.close(fig)
print('  (Figure 1 未写出；标签值 %.2f 仅供核对)' % mv[1])

# ---------------------------------------------------------------- Figure 4
print('\n=== 3. 重算转移矩阵并重绘 Figure 4 ===')
bands = [(0, 4.0, '<4.0'), (4.0, 4.5, '4.0–4.4'), (4.5, 5.0, '4.5–4.9'), (5.0, 5.5, '5.0–5.4'),
         (5.5, 6.0, '5.5–5.9'), (6.0, 20, '≥6.0')]
nb = [b[2] for b in bands]
MAT = {}
for nm, f in SER.items():
    d = pd.read_pickle(f).sort_values(['sid', 't'])
    pp = d[(d.t > BASE) & (d.t <= 10080)].copy()
    pp['kn'] = pp.groupby('sid').k.shift(-1); pp['tn'] = pp.groupby('sid').t.shift(-1)
    pp = pp[(pp.tn - pp.t > 0) & (pp.tn - pp.t <= BASE) & pp.kn.notna()]
    M = np.zeros((6, 6))
    for i, (lo, hi, _) in enumerate(bands):
        s = pp[(pp.k >= lo) & (pp.k < hi)]
        tot = len(s)
        for j, (lo2, hi2, _) in enumerate(bands):
            M[i, j] = 100 * len(s[(s.kn >= lo2) & (s.kn < hi2)]) / tot if tot else np.nan
    MAT[nm] = M

for nm in SER:
    coll = [MAT[nm][i, 4] + MAT[nm][i, 5] for i in (2, 3, 4, 5)]
    for lab, stated, got in zip(['4.5–4.9', '5.0–5.4', '5.5–5.9', '≥6.0'], T3_collapsed[nm], coll):
        ck('%s collapsed next≥5.5 @ %s' % (nm, lab), stated, got, 0.051)
if fails:
    print('\nABORT - 折叠列与 Table 3 对不上:', fails); sys.exit(1)

fig, axes = plt.subplots(1, 2, figsize=(7.9, 2.9), gridspec_kw={'wspace': 0.62})
for ax, nm in zip(axes, SER):
    im = ax.imshow(MAT[nm], cmap='YlOrRd', vmin=0, vmax=70, aspect='auto')
    ax.set_xticks(range(6)); ax.set_xticklabels(nb, rotation=45, ha='right', fontsize=6.2)
    ax.set_yticks(range(6)); ax.set_yticklabels(nb, fontsize=6.2)
    ax.set_xlabel('Next K$^+$ (mmol/L)', fontsize=7.2); ax.set_ylabel('Current K$^+$ (mmol/L)', fontsize=7.2)
    ax.set_title(nm, fontsize=8, fontweight='bold')
    for i in range(6):
        for j in range(6):
            v = MAT[nm][i, j]
            if not np.isnan(v) and v >= 0.5:
                ax.text(j, i, '%.0f' % v, ha='center', va='center', fontsize=5.6,
                        color='white' if v > 40 else 'black')
    # 右边缘：折叠概率的精确值（1 位小数），与 Table 3 一致
    ax.set_xlim(-0.5, 6.95)
    ax.axvline(5.5, color='#666666', lw=0.8, ls=':')
    for i in range(6):
        c = MAT[nm][i, 4] + MAT[nm][i, 5]
        if not np.isnan(c):
            ax.text(6.22, i, '%.1f' % c, ha='center', va='center', fontsize=5.8, fontweight='bold')
    ax.text(6.22, -0.92, 'Next\n≥5.5', ha='center', va='center', fontsize=5.6, fontweight='bold')
    ax.set_xticks(np.arange(-.5, 6, 1), minor=True); ax.set_yticks(np.arange(-.5, 6, 1), minor=True)
    ax.grid(which='minor', color='white', lw=0.6); ax.tick_params(which='minor', length=0)
    ax.tick_params(axis='both', which='major', length=0)
cb = fig.colorbar(im, ax=axes, fraction=0.022, pad=0.035)
cb.set_label('% of transitions', fontsize=6.5); cb.ax.tick_params(labelsize=6)
fig.savefig(OUT + '/FigK3_4_transition.png', bbox_inches='tight'); plt.close(fig)
print('  -> FigK3_4_transition.png  (collapsed column added)')
for nm in SER:
    print('     %s collapsed: %s' % (nm, ['%.1f' % (MAT[nm][i, 4] + MAT[nm][i, 5]) for i in range(6)]))

json.dump({nm: {k: int(v) for k, v in c.items()} for nm, c in counts.items()},
          open('out/k68_tier_counts.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump({nm: [[round(float(v), 4) for v in row] for row in MAT[nm]] for nm in SER},
          open('out/k68_transition_matrix.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n全部断言通过；已写 out/k68_tier_counts.json / out/k68_transition_matrix.json')
