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


def groups(df):
    kb = df[df.t <= BASE].groupby('sid').k.max(); post = df[df.t > BASE]
    atr = kb[(kb < 5.5) & kb.index.isin(post.groupby('sid').size().index)].index
    post = post[post.sid.isin(atr)]
    f = post[post.k >= 5.5].groupby('sid', sort=False).head(1)
    m = post.merge(f[['sid', 't']].rename(columns={'t': 't_idx'}), on='sid', how='inner')
    a = m[(m.t > m.t_idx) & (m.t <= m.t_idx + BASE)].sort_values('t')
    nx = a.groupby('sid').first()
    return len(atr), len(f), len(nx), int((nx.k >= 5.5).sum())


# ---------------- Figure 1 ----------------
fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(7.2, 2.9), gridspec_kw={'width_ratios': [1.15, 1]})
ax0.axis('off'); ax0.set_xlim(0, 10); ax0.set_ylim(0, 10)
boxes = [(0.2, 8.4, 9.4, 1.3, 'Cardiac ICU admission\nbaseline K$^+$ < 5.5 mmol/L, measured after hour 24', '#eef3f8'),
         (0.2, 6.3, 4.3, 1.4, 'no episode\nK$^+$ stays < 5.5', '#f2f2f2'),
         (5.2, 6.3, 4.4, 1.4, 'APPARENT episode\nfirst K$^+$ ≥ 5.5 after hour 24', '#fdeceb')]
for x, y, w, h, t, c in boxes:
    ax0.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.15', fc=c, ec='#9a9a9a', lw=0.7))
    ax0.text(x + w / 2, y + h / 2, t, ha='center', va='center', fontsize=6.6)
for x, y, w, h, t in [(0.2, 3.1, 3.0, 1.9, 'TRANSIENT\nnext K$^+$ < 5.5'), (3.4, 3.1, 3.1, 1.9, 'CONFIRMED\nnext K$^+$ ≥ 5.5'),
                      (6.7, 3.1, 2.9, 1.9, 'UNCLASSIFIED\nnot re-measured')]:
    ax0.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.15', fc='#f7f7f7', ec='#9a9a9a', lw=0.7))
    ax0.text(x + w / 2, y + h / 2, t, ha='center', va='center', fontsize=6.6)
ax0.add_patch(FancyBboxPatch((3.4, 0.5), 3.1, 1.9, boxstyle='round,pad=0.15', fc='#e8f0e8', ec='#5f7a5f', lw=0.8))
ax0.text(4.95, 1.45, 'SUSTAINED\nall K$^+$ ≥ 5.5\nover 24 h', ha='center', va='center', fontsize=6.6)
for (x0, y0, x1, y1) in [(5.0, 8.4, 2.4, 7.7), (5.0, 8.4, 7.4, 7.7), (7.4, 6.3, 1.7, 5.0), (7.4, 6.3, 4.95, 5.0),
                         (7.4, 6.3, 8.15, 5.0), (4.95, 3.1, 4.95, 2.4)]:
    ax0.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle='-|>', mutation_scale=7, lw=0.6, color='#707070'))
ax0.text(0.2, 9.85, 'A', fontweight='bold', fontsize=9)
ax1.text(-0.16, 1.06, 'B', transform=ax1.transAxes, fontweight='bold', fontsize=9)
labels = ['Apparent', 'Confirmed', 'Sustained', 'Unclassified']
mv = [ph1['MIMIC-IV']['apparent_pct'], ph1['MIMIC-IV']['confirmed_pct'], ph1['MIMIC-IV']['sustained_pct'],
      100 * 150 / 20322]
ev = [ph1['eICU-CRD']['apparent_pct'], ph1['eICU-CRD']['confirmed_pct'], ph1['eICU-CRD']['sustained_pct'],
      100 * 235 / 28805]
x = np.arange(4); w = 0.36
ax1.bar(x - w / 2, mv, w, color=CM, label='MIMIC-IV')
ax1.bar(x + w / 2, ev, w, color=CE, label='eICU-CRD')
for i, (a, b) in enumerate(zip(mv, ev)):
    ax1.text(i - w / 2, a + 0.12, '%.2f' % a, ha='center', fontsize=5.9)
    ax1.text(i + w / 2, b + 0.12, '%.2f' % b, ha='center', fontsize=5.9)
ax1.set_xticks(x); ax1.set_xticklabels(labels, fontsize=6.4); ax1.set_ylabel('Incidence (% of cohort)')
ax1.set_ylim(0, 6.9); ax1.legend(frameon=False, fontsize=7)
fig.tight_layout(); fig.savefig(OUT + '/FigK3_1_definition.png', bbox_inches='tight'); plt.close(fig)

# ---------------- Figure 2 ----------------
bands = [(0, 4.0, '<4.0'), (4.0, 4.5, '4.0–4.4'), (4.5, 5.0, '4.5–4.9'), (5.0, 5.5, '5.0–5.4'),
         (5.5, 6.0, '5.5–5.9'), (6.0, 20, '≥6.0')]
nb = ['<4.0', '4.0–4.4', '4.5–4.9', '5.0–5.4', '5.5–5.9', '≥6.0']
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
fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.2))
for ax, nm in zip(axes, SER):
    im = ax.imshow(MAT[nm], cmap='YlOrRd', vmin=0, vmax=70, aspect='auto')
    ax.set_xticks(range(6)); ax.set_xticklabels(nb, rotation=45, ha='right', fontsize=6.2)
    ax.set_yticks(range(6)); ax.set_yticklabels(nb, fontsize=6.2)
    ax.set_xlabel('Next K$^+$ (mmol/L)'); ax.set_ylabel('Current K$^+$ (mmol/L)')
    ax.set_title(nm, fontsize=8, fontweight='bold')
    for i in range(6):
        for j in range(6):
            v = MAT[nm][i, j]
            if not np.isnan(v) and v >= 0.5:
                ax.text(j, i, '%.0f' % v, ha='center', va='center', fontsize=5.6,
                        color='white' if v > 40 else 'black')
    ax.set_xticks(np.arange(-.5, 6, 1), minor=True); ax.set_yticks(np.arange(-.5, 6, 1), minor=True)
    ax.grid(which='minor', color='white', lw=0.6); ax.tick_params(which='minor', length=0)
cb = fig.colorbar(im, ax=axes, fraction=0.024, pad=0.02); cb.set_label('% of transitions', fontsize=6.5)
cb.ax.tick_params(labelsize=6)
fig.savefig(OUT + '/FigK3_2_transition.png', bbox_inches='tight'); plt.close(fig)

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

# ---------------- Figure 4 forest ----------------
fig, ax = plt.subplots(figsize=(5.4, 2.6))
rows = [('No episode', None, None), ('Transient', 'g_transient', 'transient'),
        ('Confirmed', 'g_confirmed', 'confirmed'), ('Sustained', 'g_sustained', 'sustained')]
for k, (nm, colc) in enumerate([('MIMIC-IV', CM), ('eICU-CRD', CE)]):
    ybase = 0
    for i, (lab, key, keyb) in enumerate(rows):
        y = (3 - i) * 1.0 + (0.22 if k == 1 else -0.0) - 0.11 * k
        if key is None:
            ax.plot([1], [y], marker='s', ms=4, color=colc)
            ax.text(1.06, y, '1.00 (reference)' + ('   ' if k == 0 else ''), va='center', fontsize=6.2)
        else:
            d = ph3b[nm]['72 h']['or_'][key]
            ax.plot([d['or_']], [y], marker='o', ms=4.5, color=colc)
            ax.plot([d['ci'][0], d['ci'][1]], [y, y], lw=1.1, color=colc)
            ax.text(22, y, '%.2f (%.2f–%.2f)' % (d['or_'], d['ci'][0], d['ci'][1]), va='center', fontsize=6.2)
ax.set_xscale('log'); ax.set_xlim(0.8, 22)
ax.set_xticks([1, 2, 5, 10]); ax.set_xticklabels(['1', '2', '5', '10'])
ax.set_yticks([3, 2, 1, 0]); ax.set_yticklabels([r[0] for r in rows], fontsize=7)
ax.axvline(1, color='#999999', lw=0.7, ls=':')
ax.set_xlabel('Adjusted odds ratio for in-hospital death (72-h landmark)')
h = [plt.Line2D([], [], color=CM, marker='o', ls='', ms=4, label='MIMIC-IV'),
     plt.Line2D([], [], color=CE, marker='o', ls='', ms=4, label='eICU-CRD')]
ax.legend(handles=h, frameon=False, fontsize=6.5, loc='lower right')
fig.tight_layout(); fig.savefig(OUT + '/FigK3_4_forest.png', bbox_inches='tight'); plt.close(fig)

# ---------------- Figure 5 rule yield ----------------
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
        a2.text(i, v + 0.08, '%.1f' % v, ha='center', fontsize=5.8, color=c)
a1.set_xticks(range(5)); a1.set_xticklabels(lab); a1.set_ylabel('Re-measured within window (%)')
a1.set_ylim(0, 95); a1.set_title('A  Current practice', fontsize=7.5, loc='left', fontweight='bold')
a1.legend(frameon=False, fontsize=6.5)
a2.set_xticks(range(5)); a2.set_xticklabels(lab); a2.set_ylabel('Repeat measurements per confirmed episode')
a2.set_ylim(0, 6); a2.set_title('B  Yield of the rule', fontsize=7.5, loc='left', fontweight='bold')
a2.legend(frameon=False, fontsize=6.5)
fig.tight_layout(); fig.savefig(OUT + '/FigK3_5_rule.png', bbox_inches='tight'); plt.close(fig)
print('生成：')
for f in sorted(os.listdir(OUT)):
    print('  ', f, os.path.getsize(OUT + '/' + f))
