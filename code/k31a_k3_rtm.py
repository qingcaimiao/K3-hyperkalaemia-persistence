# -*- coding: utf-8 -*-
"""
K3 阶段②a：把"低确认率"拆成 噪声/回归均值（RTM） 与 真实回落 两部分
- 事件表重建并落盘（供 k31b 使用）
- 假阈值对照（negative control）：4.5 / 4.8 / 5.0 / 5.2 / 5.5 / 6.0 六档同法计算确认率
  · 低阈值（4.5/4.8）不构成治疗指征 → 其确认率反映"纯测量+生物学噪声"能解释的部分
  · 若 5.5 的确认率 < 低阈值确认率 → 差额即阈值触发的真实回落/治疗效应
- 参数化 RTM 模拟：σ(单次) 由相邻配对估；τ²(个体间真值方差) 由多测者估计；λ=τ²/(τ²+σ²)
- 复查选择的 bounds：无复查者按 0 / 全确认两种极端
"""
import pandas as pd, numpy as np, json, os, warnings
from scipy.stats import norm
warnings.filterwarnings('ignore')

BASE = 1440
THRS = [4.5, 4.8, 5.0, 5.2, 5.5, 6.0]
SER = {'MIMIC-IV': pd.read_pickle('out/k3_k_series_mimic.pkl'),
       'eICU-CRD': pd.read_pickle('out/k3_k_series_eicu.pkl')}
OUT = {}


def build_events(d, thr, base=BASE, gb=None):
    """对单一阈值：基线最高 < thr 的住院中，首次 ≥thr 及其 24h 内复查"""
    if gb is None:
        d = d.sort_values(['sid', 't'])
        gb = {sid: g for sid, g in d.groupby('sid', sort=False)}
    kb = d[d.t <= base].groupby('sid').k.max()
    coh = kb[kb < thr].index
    rows = []
    for sid in coh:
        g = gb[sid]
        post = g[g.t > base]
        if len(post) == 0:
            continue
        pos = post[post.k >= thr]
        if len(pos) == 0:
            continue
        r = pos.iloc[0]
        after = post[post.t > r.t]
        a24 = after[after.t <= r.t + base]
        before = g[g.t < r.t]
        rows.append(dict(sid=sid, k_base=float(kb[sid]), k_idx=float(r.k), t_idx=float(r.t),
                         k_prev=float(before.k.iloc[-1]) if len(before) else np.nan,
                         t_prev=float(before.t.iloc[-1]) if len(before) else np.nan,
                         k_next=float(a24.k.iloc[0]) if len(a24) else np.nan,
                         t_next=float(a24.t.iloc[0] - r.t) if len(a24) else np.nan,
                         confirm=bool(len(a24) and a24.k.iloc[0] >= thr),
                         sustained=bool(len(a24) and (a24.k >= thr).all())))
    return pd.DataFrame(rows), int(len(coh)), len(rows)


for nm, d in SER.items():
    print('\n' + '=' * 106); print(nm); print('=' * 106)
    d = d.sort_values(['sid', 't']).reset_index(drop=True)
    GB = {sid: g for sid, g in d.groupby('sid', sort=False)}

    # ---------- 噪声参数 ----------
    dd = d.copy()
    dd['dk'] = dd.groupby('sid').k.diff(); dd['dt'] = dd.groupby('sid').t.diff()
    pr = dd[(dd.dt > 0) & (dd.dt <= BASE)]
    sd_diff = float(pr.dk.std()); sd_single = sd_diff / np.sqrt(2)
    kpop = float(d.k.mean())
    g = d.groupby('sid').k
    n_i = g.size(); mean_i = g.mean(); var_i = g.var()
    multi = n_i[n_i >= 3].index
    var_between_obs = float(mean_i[multi].var())          # Var(患者均值)
    correction = float((sd_single ** 2 / n_i[multi]).mean())
    tau2 = max(var_between_obs - correction, 1e-6)
    lam = tau2 / (tau2 + sd_single ** 2)
    print('噪声参数：within 差值 SD %.3f → 单次 SD %.3f（CV %.2f%%）| τ² %.4f | λ=τ²/(τ²+σ²)=%.3f'
          % (sd_diff, sd_single, 100 * sd_single / kpop, tau2, lam))
    print('          人群血钾均值 %.2f mmol/L；RCV(95%%) = %.2f mmol/L'
          % (kpop, 1.96 * np.sqrt(2) * sd_single))

    # ---------- 假阈值对照 ----------
    print('\n--- 假阈值对照（同法计算；低阈值不构成治疗指征，故其确认率 = 噪声+RTM 的地板）---')
    print('  %-8s %8s %8s %8s %9s %9s %9s %8s' %
          ('阈值', '队列', 'apparent', '发生率%', '有复查', '确认%', '一过性%', '无复查%'))
    thr_rows = {}
    for thr in THRS:
        e, n_coh, n_app = build_events(d, thr, gb=GB)
        if len(e) == 0:
            print('  %-8s %8d %8d %8s' % (thr, n_coh, 0, '-')); continue
        rep = e[e.t_next.notna()]
        conf = 100 * rep.confirm.mean() if len(rep) else np.nan
        norep = 100 * e.t_next.isna().mean()
        thr_rows[thr] = dict(n_coh=n_coh, apparent=n_app, inc=round(100 * n_app / n_coh, 2),
                             rechecked=len(rep), confirm_pct=round(float(conf), 1),
                             revert_pct=round(100 - float(conf), 1), norep_pct=round(float(norep), 1),
                             med_k_idx=round(float(e.k_idx.median()), 2),
                             med_next=round(float(rep.k_next.median()), 2) if len(rep) else None)
        if thr == 5.5:
            e.to_pickle('out/k3_events_%s.pkl' % ('mimic' if nm == 'MIMIC-IV' else 'eicu'))
        print('  %-8s %8s %8s %8s %9s %9s %9s %8s'
              % (thr, format(n_coh, ','), format(n_app, ','), thr_rows[thr]['inc'],
                 format(len(rep), ','), thr_rows[thr]['confirm_pct'], thr_rows[thr]['revert_pct'],
                 thr_rows[thr]['norep_pct']))

    # ---------- RTM 参数化模拟（仅 5.5） ----------
    e55 = pd.read_pickle('out/k3_events_%s.pkl' % ('mimic' if nm == 'MIMIC-IV' else 'eicu'))
    rep = e55[e55.t_next.notna() & e55.k_prev.notna()].copy()
    obs_conf = float(rep.confirm.mean())
    print('\n--- RTM 分解（阈值 5.5；用 k_prev 作真值的含噪先验）---')
    print('  观察：有复查 %s 例，确认 %s 例 = %.1f%%' % (format(len(rep), ','), format(int(rep.confirm.sum()), ','), 100 * obs_conf))
    mu_hat = lam * rep.k_prev.values + (1 - lam) * kpop
    p_conf = 1 - norm.cdf((5.5 - mu_hat) / sd_single)
    exp_conf = float(p_conf.mean())
    print('  纯 RTM 预期确认率（λ=%.3f）：%.1f%%' % (lam, 100 * exp_conf))
    for lbl, l in [('λ=1（上次值当真值，不收缩）', 1.0), ('λ=0（完全回归人群均值）', 0.0)]:
        mh = l * rep.k_prev.values + (1 - l) * kpop
        print('    敏感性 %-30s 预期确认 %.1f%%' % (lbl, 100 * float((1 - norm.cdf((5.5 - mh) / sd_single)).mean())))
    # 蒙特卡洛（与解析式互校）
    rng = np.random.default_rng(7)
    sim = (rng.normal(mu_hat[:, None], sd_single, size=(len(mu_hat), 400)) >= 5.5).mean(axis=0)
    print('  蒙特卡洛（400 次重抽）预期确认率 %.1f%%（95%% 区间 %.1f–%.1f%%）'
          % (100 * sim.mean(), 100 * np.percentile(sim, 2.5), 100 * np.percentile(sim, 97.5)))
    # 观察值的 bootstrap 区间
    bs = [(rep.confirm.sample(len(rep), replace=True, random_state=i).mean()) for i in range(400)]
    print('  观察确认率 bootstrap 95%% 区间 %.1f–%.1f%%' % (100 * np.percentile(bs, 2.5), 100 * np.percentile(bs, 97.5)))

    # ---------- 复查选择的 bounds ----------
    n_app = len(e55); n_rep = int(e55.t_next.notna().sum()); C = int(e55.confirm.sum()); n_nr = n_app - n_rep
    lo = 100 * C / n_app
    hi = 100 * (C + n_nr) / n_app
    print('\n--- 复查选择的 bounds（阈值 5.5）---')
    print('  apparent %s | 有复查 %s（%.1f%%）| 无复查 %s（%.1f%%）'
          % (format(n_app, ','), format(n_rep, ','), 100 * n_rep / n_app, format(n_nr, ','), 100 * n_nr / n_app))
    print('  confirmed 占 apparent：观察 %.1f%%（%s 例）；下界 %.1f%%（无复查者全不确认）；上界 %.1f%%（无复查者全确认）'
          % (100 * C / n_app, format(C, ','), lo, hi))
    cmpa = e55.assign(nr=e55.t_next.isna()).groupby('nr').agg(n=('sid', 'size'), k_idx=('k_idx', 'median'),
                                                             k_base=('k_base', 'median'), k_prev=('k_prev', 'median'))
    print('  无复查者 vs 有复查者：%s' % {bool(k): v for k, v in zip(cmpa.index, cmpa.to_dict('records'))})

    OUT[nm] = dict(sd_single=round(sd_single, 3), cv=round(100 * sd_single / kpop, 2), tau2=round(tau2, 4),
                   lam=round(lam, 3), rcv=round(1.96 * np.sqrt(2) * sd_single, 2), kpop=round(kpop, 2),
                   thrs={str(k): v for k, v in thr_rows.items()},
                   obs_confirm=round(100 * obs_conf, 1), rtm_confirm=round(100 * exp_conf, 1),
                   rtm_lam1=round(100 * float((1 - norm.cdf((5.5 - rep.k_prev.values) / sd_single)).mean()), 1),
                   rtm_lam0=round(100 * float((1 - norm.cdf((5.5 - kpop) / sd_single)).mean()), 1),
                   obs_ci=[round(100 * float(np.percentile(bs, 2.5)), 1), round(100 * float(np.percentile(bs, 97.5)), 1)],
                   n_app=n_app, n_rep=n_rep, n_nr=n_nr, confirmed=C,
                   confirmed_lower=round(lo, 1), confirmed_upper=round(hi, 1))
json.dump(OUT, open('out/k3_phase2a.json', 'w'), ensure_ascii=False, indent=1)
print('\n写出 out/k3_phase2a.json 与 out/k3_events_{mimic,eicu}.pkl')
