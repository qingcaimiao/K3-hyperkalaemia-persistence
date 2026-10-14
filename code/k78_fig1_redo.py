# -*- coding: utf-8 -*-
"""k78: redraw Figure 1 only.

Why: in panel A all four state arrows were drawn from a single point at the bottom
of the APPARENT box, so the two outer arrows ran almost horizontally across the
tops of the INTERMITTENT and SUSTAINED boxes.  Panel A now uses a proper
three-level hierarchy: one short trunk leaves the APPARENT box, a single
distribution line spans the four state boxes, and four SHORT vertical arrows drop
into them.  No arrow crosses a box.

Numbers are still recomputed from the source series and asserted against Table 2,
so the figure cannot drift from the tables.
"""
import sys
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

T2 = {
 'MIMIC-IV': dict(n_coh=20322, apparent=1182, transient=757, intermittent=189,
                  sustained=86, unclassified=150,
                  pct={'Apparent': 5.82, 'Transient': 3.73, 'Intermittent': 0.93,
                       'Sustained': 0.42, 'Unclassified': 0.74}),
 'eICU-CRD': dict(n_coh=28805, apparent=997, transient=493, intermittent=169,
                  sustained=100, unclassified=235,
                  pct={'Apparent': 3.46, 'Transient': 1.71, 'Intermittent': 0.59,
                       'Sustained': 0.35, 'Unclassified': 0.82}),
}
fails = []


def ck(name, stated, got, tol):
    ok = abs(stated - got) <= tol
    print('  %-42s stated %-7s recomputed %-8s %s'
          % (name, stated, round(got, 4), 'OK' if ok else '*** MISMATCH ***'))
    if not ok:
        fails.append(name)


print('=== 1. 重算全队列五档计数 ===')
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
    ck('%s n_coh' % nm, T2[nm]['n_coh'], n, 0)
    for g in ['transient', 'intermittent', 'sustained', 'unclassified']:
        ck('%s %s' % (nm, g), T2[nm][g], tab[g], 0)

labels = ['Apparent', 'Transient', 'Intermittent', 'Sustained', 'Unclassified']
keys = ['apparent', 'transient', 'intermittent', 'sustained', 'unclassified']
TIERS = ['transient', 'intermittent', 'sustained', 'unclassified']
mv, ev = [], []
for k in keys:
    for nm, bag in (('MIMIC-IV', mv), ('eICU-CRD', ev)):
        n = sum(counts[nm].values())
        num = sum(counts[nm][g] for g in TIERS) if k == 'apparent' else counts[nm][k]
        bag.append(100 * num / n)
assert len(labels) == len(mv) == len(ev) == 5, (
    'labels/mv/ev 长度不一致: %d/%d/%d' % (len(labels), len(mv), len(ev)))
for nm, vals in (('MIMIC-IV', mv), ('eICU-CRD', ev)):
    assert len(labels) == len(vals), '%s: labels/vals 长度不一致' % nm
    for lab, v in zip(labels, vals):
        ck('%s %s pct' % (nm, lab), T2[nm]['pct'][lab], v, 0.005)

if fails:
    print('\nABORT - 图 1 与 Table 2 对不上:', fails); sys.exit(1)

# ---------------------------------------------------------------- Figure 1
print('\n=== 2. 重绘 Figure 1（panel A 改为层级式箭头）===')
fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(7.4, 3.25),
                               gridspec_kw={'width_ratios': [1.25, 1]})
ax0.axis('off'); ax0.set_xlim(0, 10); ax0.set_ylim(0, 10)

BOX = dict(boxstyle='round,pad=0.12', ec='#9a9a9a', lw=0.7)
AR = dict(arrowstyle='-|>', mutation_scale=7, lw=0.6, color='#707070')

# level 1 — admission
ax0.add_patch(FancyBboxPatch((0.2, 8.70), 9.4, 1.20, fc='#eef3f8', **BOX))
ax0.text(4.9, 9.30, 'Cardiac ICU admission\nbaseline K$^+$ < 5.5 mmol/L, measured after hour 24',
         ha='center', va='center', fontsize=6.4)

# level 2 — no episode | apparent episode
ax0.add_patch(FancyBboxPatch((0.2, 7.05), 4.3, 1.25, fc='#f2f2f2', **BOX))
ax0.text(2.35, 7.67, 'no episode\nK$^+$ stays < 5.5', ha='center', va='center', fontsize=6.4)
ax0.add_patch(FancyBboxPatch((5.2, 7.05), 4.4, 1.25, fc='#fdeceb', **BOX))
ax0.text(7.4, 7.67, 'APPARENT episode\nfirst K$^+$ ≥ 5.5 after hour 24',
         ha='center', va='center', fontsize=6.4)

# level 3 — the four states, all subdivisions of the apparent episode
sub = [(0.2, 'TRANSIENT', 'every value in\nthe next 24 h < 5.5', '#eaf2ea'),
       (2.62, 'INTERMITTENT', 'some but not all\nvalues ≥ 5.5', '#fdf5e6'),
       (5.04, 'SUSTAINED', 'every value in\nthe next 24 h ≥ 5.5', '#fbe9e7'),
       (7.46, 'UNCLASSIFIED', 'not re-measured\nwithin 24 h', '#f4f4f4')]
BOOL = dict(boxstyle='round,pad=0.12', ec='#9a9a9a', lw=0.7)
for x, t, s, c in sub:
    ax0.add_patch(FancyBboxPatch((x, 3.30), 2.32, 2.35, fc=c, **BOOL))
    ax0.text(x + 1.16, 4.95, t, ha='center', va='center', fontsize=6.1, fontweight='bold')
    ax0.text(x + 1.16, 4.10, s, ha='center', va='center', fontsize=5.9)

# short arrows from the admission box into the two second-level boxes
ax0.add_patch(FancyArrowPatch((4.9, 8.70), (2.35, 8.33), **AR))
ax0.add_patch(FancyArrowPatch((4.9, 8.70), (7.40, 8.33), **AR))

# hierarchy bus: one trunk from APPARENT, one distribution line, four short drops
XS = [1.36, 3.78, 6.20, 8.62]
TRUNK_TOP, BUS_Y, DROP_END = 7.05, 6.42, 5.80
ax0.plot([7.4, 7.4], [BUS_Y, TRUNK_TOP], color='#707070', lw=0.6, solid_capstyle='butt')
ax0.plot([min(XS), max(XS)], [BUS_Y, BUS_Y], color='#707070', lw=0.6, solid_capstyle='butt')
for x1 in XS:
    ax0.add_patch(FancyArrowPatch((x1, BUS_Y), (x1, DROP_END), **AR))

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

fig.tight_layout(); fig.savefig(OUT + '/FigK3_1_definition.png', bbox_inches='tight'); plt.close(fig)
print('  -> FigK3_1_definition.png  (MIMIC transient label = %.2f)' % mv[1])
print('\n全部断言通过 ✅')
