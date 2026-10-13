# -*- coding: utf-8 -*-
"""
K3 阶段②c：回落到底是「测量误差」还是「真实短期波动」？——修正版定界 + 无模型转移矩阵
修正 ②a 的框架错误：RTM 的正确基线是**被选中的那次测量本身（k_idx）**，不是 24h 前的 k_prev
（k_prev 与 k_idx 间隔可达 24h 以上，"真值不变"的前提不成立，会把预期压到 0.5%）。
框架：
  · 若相邻差异纯属实验室分析误差（血钾 CV 1.5–3%，即 SD 0.06–0.13 mmol/L）
    → 下次测量应几乎必然仍 ≥5.5 → 与实际观察的 20–30% 严重不符 → 排除"单次值为误差"
  · 若把**观察到的短期变异**（SD 0.41，CV 9.7%）当作全部噪声（最宽松的"一切都是波动"假设）
    → 给出确认率的下界；观察值高于该下界，说明部分升高是真实的持续状态
另加：状态转移矩阵（无模型、经验）与索引值-确认率的连续关系
"""
import pandas as pd, numpy as np, json, warnings
from scipy.stats import norm
warnings.filterwarnings('ignore')
BASE = 1440
SER = {'MIMIC-IV': pd.read_pickle('out/k3_k_series_mimic.pkl'),
       'eICU-CRD': pd.read_pickle('out/k3_k_series_eicu.pkl')}
BANDS = [(0, 4.0, '<4.0'), (4.0, 4.5, '4.0–4.4'), (4.5, 5.0, '4.5–4.9'),
         (5.0, 5.5, '5.0–5.4'), (5.5, 6.0, '5.5–5.9'), (6.0, 20.0, '≥6.0')]
OUT = {}

for nm, d in SER.items():
    d = d.sort_values(['sid', 't']).reset_index(drop=True)
    print('\n' + '=' * 108); print(nm); print('=' * 108)
    dd = d.copy(); dd['dk'] = dd.groupby('sid').k.diff(); dd['dt'] = dd.groupby('sid').t.diff()
    pr = dd[(dd.dt > 0) & (dd.dt <= BASE)]
    sd_w = float(pr.dk.std() / np.sqrt(2)); kpop = float(d.k.mean())
    g = d.groupby('sid').k; n_i = g.size(); mean_i = g.mean()
    multi = n_i[n_i >= 3].index
    tau2 = max(float(mean_i[multi].var()) - float((sd_w ** 2 / n_i[multi]).mean()), 1e-6)

    # ---------- 状态转移矩阵（t>24h 之后的相邻对，间隔 ≤24h） ----------
    post = d[d.t > BASE].copy()
    post['kn'] = post.groupby('sid').k.shift(-1)
    post['tn'] = post.groupby('sid').t.shift(-1)
    post['dt'] = post.tn - post.t
    pp = post[(post.dt > 0) & (post.dt <= BASE) & post.kn.notna()]
    print('转移矩阵：%s 个相邻测量对（24h 后、间隔 ≤24h）；行=当前值，列示下次结果' % format(len(pp), ','))
    print('  %-10s %8s | %8s %8s | %9s %9s | %8s' % ('当前值', 'n', '下次≥5.5', '下次≥6.0', '下次中位', '下次-当前', '回升%'))
    trans = []
    for lo, hi, lab in BANDS:
        s = pp[(pp.k >= lo) & (pp.k < hi)]
        if len(s) < 50: continue
        r = dict(band=lab, n=int(len(s)),
                 p_next_55=round(100 * float((s.kn >= 5.5).mean()), 1),
                 p_next_60=round(100 * float((s.kn >= 6.0).mean()), 1),
                 med_next=round(float(s.kn.median()), 2),
                 med_delta=round(float((s.kn - s.k).median()), 2),
                 p_rise=round(100 * float((s.kn > s.k).mean()), 1))
        trans.append(r)
        print('  %-10s %8s | %7.1f%% %7.1f%% | %9.2f %+9.2f | %7.1f%%'
              % (lab, format(len(s), ','), r['p_next_55'], r['p_next_60'], r['med_next'], r['med_delta'], r['p_rise']))

    # ---------- 噪声定界 ----------
    ev = pd.read_pickle('out/k3_events_%s.pkl' % ('mimic' if nm == 'MIMIC-IV' else 'eicu'))
    rep = ev[ev.t_next.notna() & ev.k_prev.notna()]
    obs = float(rep.confirm.mean())
    print('\n噪声定界（阈值 5.5）：观察确认率 %.1f%%（%d/%d）' % (100 * obs, int(rep.confirm.sum()), len(rep)))
    print('  %-34s %8s %8s %10s' % ('假设的“噪声”来源', 'SD', 'λ', '预期确认率'))
    scen = []
    for lbl, sd in [('Analytical error, CV 1.5%', 0.015 * kpop),
                    ('Analytical error, CV 3.0%', 0.030 * kpop),
                    ('Analytical error, CV 5.0% (deliberately conservative)', 0.050 * kpop),
                    ('Observed short-term variability (includes genuine fluctuation)', sd_w)]:
        lam = tau2 / (tau2 + sd ** 2)
        mu = lam * rep.k_idx.values + (1 - lam) * kpop
        sd2 = sd * np.sqrt(1 + lam)
        p = float((1 - norm.cdf((5.5 - mu) / sd2)).mean())
        scen.append(dict(label=lbl, sd=round(sd, 3), lam=round(lam, 3), expected=round(100 * p, 2)))
        print('  %-34s %8.3f %8.3f %9.1f%%' % (lbl, sd, lam, 100 * p))
    print('  → “单次值只是误差”被排除：即使按 CV 5%% 计，下次也应 %.0f%% 仍 ≥5.5。'
          % scen[2]['expected'])

    # ---------- 索引值-确认率连续关系 ----------
    print('\n索引值与确认率（细分层）：')
    fine = []
    for lo, hi in [(5.5, 5.6), (5.6, 5.8), (5.8, 6.0), (6.0, 6.3), (6.3, 6.6), (6.6, 20)]:
        s = rep[(rep.k_idx >= lo) & (rep.k_idx < hi)]
        if len(s) < 20: continue
        fine.append(dict(lo=lo, hi=hi, n=int(len(s)), confirm=round(100 * float(s.confirm.mean()), 1),
                         med_next=round(float(s.k_next.median()), 2)))
        print('  %.1f–%.1f：n=%4d 确认 %5.1f%% 复查中位 %.2f' % (lo, hi, len(s), 100 * s.confirm.mean(), s.k_next.median()))

    OUT[nm] = dict(sd_within=round(sd_w, 3), cv_within=round(100 * sd_w / kpop, 2), tau2=round(tau2, 4),
                   kpop=round(kpop, 2), n_pairs_trans=int(len(pp)), trans=trans,
                   obs_confirm=round(100 * obs, 1), scenarios=scen, fine=fine)
json.dump(OUT, open('out/k3_phase2c.json', 'w'), ensure_ascii=False, indent=1)
print('\n写出 out/k3_phase2c.json')
