# -*- coding: utf-8 -*-
"""k70: redraw Figure 3.

Two defects fixed:
  * the third panel's x tick labels ("Observed var." / "Observed") collided after the
    export, so the panel width is increased;
  * nothing else is changed, but every number drawn is asserted against Table 3
    (within-patient SD, CV and RCV) and Table 4 (expected and observed confirmation),
    so the figure cannot drift from the tables again.
"""
import io, json, sys
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update({'font.family': 'Arial', 'font.size': 7.5, 'axes.linewidth': 0.7,
                     'xtick.major.width': 0.7, 'ytick.major.width': 0.7,
                     'axes.spines.top': False, 'axes.spines.right': False,
                     'savefig.dpi': 600, 'figure.dpi': 600})
OUT = 'out/figures_k3'
BASE = 1440
CM = '#1f4e79'; CE = '#c0504d'
SER = {'MIMIC-IV': 'out/k3_k_series_mimic.pkl', 'eICU-CRD': 'out/k3_k_series_eicu.pkl'}
ph2c = json.load(open('out/k3_phase2c.json', encoding='utf-8'))

# anchors printed in the manuscript
T3 = {'MIMIC-IV': dict(sd=0.410, cv=9.71, rcv=1.14), 'eICU-CRD': dict(sd=0.386, cv=9.40, rcv=1.07)}
T4 = {'MIMIC-IV': dict(cv15=78.8, cv30=60.1, cv50=37.8, obsvar=14.7, obs=21.7),
      'eICU-CRD': dict(cv15=82.8, cv30=67.7, cv50=46.5, obsvar=19.2, obs=30.7)}
fails = []


def ck(name, stated, got, tol=0.051):
    ok = abs(stated - got) <= tol
    print('  %-34s stated %-7s recomputed %-8s %s' % (name, stated, round(float(got), 4),
                                                     'OK' if ok else '*** MISMATCH ***'))
    if not ok:
        fails.append(name)


STAT = {}
for nm, f in SER.items():
    d = pd.read_pickle(f).sort_values(['sid', 't'])
    dk = d.copy(); dk['dk'] = dk.groupby('sid').k.diff(); dk['dt'] = dk.groupby('sid').t.diff()
    pr = dk[(dk.dt > 0) & (dk.dt <= BASE)]
    sd = pr.dk.std() / np.sqrt(2)
    cv = 100 * sd / d.k.mean()
    rcv = 1.96 * np.sqrt(2) * sd
    STAT[nm] = dict(pr=pr, sd=sd, cv=cv, rcv=rcv, mean=d.k.mean())
    print('%s' % nm)
    ck('%s SD' % nm, T3[nm]['sd'], sd, 0.0005)
    ck('%s CV' % nm, T3[nm]['cv'], cv, 0.005)
    ck('%s RCV95' % nm, T3[nm]['rcv'], rcv, 0.005)
    sc = ph2c[nm]['scenarios']
    ck('%s expected CV1.5%%' % nm, T4[nm]['cv15'], sc[0]['expected'], 0.05)
    ck('%s expected CV3.0%%' % nm, T4[nm]['cv30'], sc[1]['expected'], 0.05)
    ck('%s expected CV5.0%%' % nm, T4[nm]['cv50'], sc[2]['expected'], 0.05)
    ck('%s expected observed-var' % nm, T4[nm]['obsvar'], sc[3]['expected'], 0.05)
    ck('%s observed confirmation' % nm, T4[nm]['obs'], ph2c[nm]['obs_confirm'], 0.05)

if fails:
    print('\nABORT:', fails); sys.exit(1)

fig, axes = plt.subplots(1, 3, figsize=(7.9, 2.5))
for ax, nm in zip(axes[:2], SER):
    st = STAT[nm]
    ax.hist(st['pr'].dk.clip(-2.5, 2.5), bins=60, color=CM if nm == 'MIMIC-IV' else CE, alpha=0.85)
    for v in (-1.96 * np.sqrt(2) * st['sd'], 1.96 * np.sqrt(2) * st['sd']):
        ax.axvline(v, color='k', ls='--', lw=0.8)
    ax.set_title(nm, fontsize=7.5, fontweight='bold')
    ax.set_xlabel('Difference between consecutive K$^+$ (mmol/L)')
    ax.set_ylabel('Pairs (≤24 h)')
    ax.text(0.03, 0.95, 'SD %.3f\nCV %.2f%%\nRCV$_{95}$ %.2f' % (st['sd'], st['cv'], st['rcv']),
            transform=ax.transAxes, va='top', fontsize=6.4)

ax = axes[2]
xs = np.arange(5)
b1 = [ph2c['MIMIC-IV']['scenarios'][i]['expected'] for i in range(4)] + [ph2c['MIMIC-IV']['obs_confirm']]
b2 = [ph2c['eICU-CRD']['scenarios'][i]['expected'] for i in range(4)] + [ph2c['eICU-CRD']['obs_confirm']]
ax.bar(xs - 0.2, b1, 0.4, color=CM, label='MIMIC-IV')
ax.bar(xs + 0.2, b2, 0.4, color=CE, label='eICU-CRD')
for i, (a, b) in enumerate(zip(b1, b2)):
    ax.text(i - 0.2, a + 1.6, '%.0f' % a, ha='center', fontsize=5.6)
    ax.text(i + 0.2, b + 1.6, '%.0f' % b, ha='center', fontsize=5.6)
ax.set_xticks(xs)
ax.set_xticklabels(['CV\n1.5%', 'CV\n3%', 'CV\n5%', 'Observed\nvariability', 'Observed\nrate'],
                   fontsize=5.7)
ax.set_xlim(-0.55, 4.55)
ax.set_ylabel('Expected confirmation (%)'); ax.set_ylim(0, 100)
ax.set_title('Source of variation assumed', fontsize=7.5)
ax.legend(frameon=False, fontsize=6.5)
fig.tight_layout(); fig.savefig(OUT + '/FigK3_3_variability.png', bbox_inches='tight'); plt.close(fig)
print('\n-> FigK3_3_variability.png redrawn (width 7.9 in, labels separated)')
