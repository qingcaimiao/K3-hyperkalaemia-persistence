# -*- coding: utf-8 -*-
"""
K3 阶段④：规则工具评估 —— 「首次血钾 ≥5.5 后 W 小时内复查」
只做可观测、可辩护的操作性度量（不假设早复查的因果效应，因为"重的患者被早查"是双向的）：
  1 现状依从性：首次越线后 W 小时内复查的比例（= coverage）
  2 规则可确认率：在全部 apparent 中，能在 W 内被确认持续的比例
  3 效率：NNR（每确认 1 例持续/确认高钾需要多少次复查）
  4 分层必要性：若规则只施加于更高索引值层，节省多少检测量、损失多少确认例数
  5 时间到确认：已确认事件的实际复查间隔分布
"""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings('ignore')
WS = [120, 240, 360, 720, 1440]
GL = {120: '2 h', 240: '4 h', 360: '6 h', 720: '12 h', 1440: '24 h'}
BANDS = [(5.5, 6.0, '5.5–5.9'), (6.0, 6.5, '6.0–6.4'), (6.5, 20.0, '≥6.5')]
OUT = {}

for nm, f in [('MIMIC-IV', 'out/k3_events_mimic.pkl'), ('eICU-CRD', 'out/k3_events_eicu.pkl')]:
    e = pd.read_pickle(f)
    n = len(e)
    rep = e[e.t_next.notna()]
    norep = int(e.t_next.isna().sum())
    print('\n' + '=' * 100); print(nm); print('=' * 100)
    print('apparent %s 例 | 已复查 %s（%.1f%%）| 未复查 %s（%.1f%%）| 全组确认率 %.1f%%'
          % (format(n, ','), format(len(rep), ','), 100 * len(rep) / n,
             format(norep, ','), 100 * norep / n, 100 * e.confirm.mean()))

    print('\n--- 1/2/3 规则的依从性、可确认率与效率 ---')
    print('  %-6s %10s %12s %12s %10s %12s' % ('窗口', '现状已复查%', '可确认例数', '可确认率%', 'NNR', '当前未覆盖'))
    rules = []
    for W in WS:
        inw = e.t_next <= W
        n_inw = int(inw.sum())
        cap = int((inw & e.confirm).sum())
        r = dict(W=W, label=GL[W], coverage=round(100 * n_inw / n, 1),
                 captured=cap, captured_pct=round(100 * cap / n, 1),
                 nnr=round(n_inw / cap, 1) if cap else None,
                 uncov=round(100 * (1 - n_inw / n), 1),
                 uncov_n=int(n - n_inw))
        rules.append(r)
        print('  %-6s %9.1f%% %12s %11.1f%% %10s %11.1f%% (%s 例)'
              % (GL[W], r['coverage'], format(cap, ','), r['captured_pct'], r['nnr'], r['uncov'], format(r['uncov_n'], ',')))

    print('\n--- 4 分层必要性：规则只施加于更高层 ---')
    print('  %-22s %10s %12s %10s %12s' % ('应用范围', '需复查例数', '可确认例数', 'NNR', '相对全应用省%'))
    sub = e[e.t_next <= 360]
    base_n, base_c = int((e.t_next <= 360).sum()), int(((e.t_next <= 360) & e.confirm).sum())
    strat = []
    for lo, hi, lab in BANDS:
        s = e[(e.k_idx >= lo) & (e.k_idx < hi) & (e.t_next <= 360)]
        c = int(s.confirm.sum())
        strat.append(dict(band=lab, n=len(s), cap=c, nnr=round(len(s) / c, 1) if c else None,
                          save=round(100 * (1 - len(s) / base_n), 1) if base_n else None))
        print('  %-22s %10s %12s %10s %11s%%' % ('仅 %s（6 h 窗口）' % lab, format(len(s), ','), format(c, ','),
                                                 strat[-1]['nnr'], strat[-1]['save']))
    print('  %-22s %10s %12s %10s' % ('全部 apparent', format(base_n, ','), format(base_c, ','),
                                      round(base_n / base_c, 1) if base_c else None))

    print('\n--- 5 时间到确认（已确认事件的实际复查间隔）---')
    conf = rep[rep.confirm]
    ttc = []
    for W in WS:
        ttc.append(dict(W=W, label=GL[W], pct=round(100 * float((conf.t_next <= W).mean()), 1)))
        print('  已确认事件中，复查在 %-4s 内者 %5s 例（%5.1f%%）' % (GL[W], format(int((conf.t_next <= W).sum()), ','), 100 * (conf.t_next <= W).mean()))
    if len(conf):
        print('  已确认事件复查间隔：中位 %.1f h（IQR %.1f–%.1f）| 未确认事件中位 %.1f h'
              % (conf.t_next.median() / 60, conf.t_next.quantile(.25) / 60, conf.t_next.quantile(.75) / 60,
                 rep[~rep.confirm].t_next.median() / 60 if (~rep.confirm).any() else np.nan))

    print('\n--- 附：按实际复查间隔分层的确认率（注意双向因果：重的患者被更早复查）---')
    gaps = []
    for lo, hi, lab in [(0, 180, '≤3 h'), (180, 360, '3–6 h'), (360, 720, '6–12 h'), (720, 1441, '12–24 h')]:
        s = rep[(rep.t_next > lo) & (rep.t_next <= hi)]
        if len(s) < 15: continue
        gaps.append(dict(gap=lab, n=int(len(s)), confirm=round(100 * float(s.confirm.mean()), 1)))
        print('  %-8s n=%4d 确认 %5.1f%%' % (lab, len(s), 100 * s.confirm.mean()))
    print('  未复查 %4d 例 → 结果未知（阶段②：该组院内死亡率 1.8 倍于复查者）' % norep)

    OUT[nm] = dict(n_apparent=n, n_rep=len(rep), n_norep=norep, rules=rules, strat=strat,
                   ttc=ttc, gaps=gaps,
                   conf_med_gap_h=round(float(conf.t_next.median() / 60), 1) if len(conf) else None,
                   unconf_med_gap_h=round(float(rep[~rep.confirm].t_next.median() / 60), 1) if (~rep.confirm).any() else None)
json.dump(OUT, open('out/k3_phase4.json', 'w'), ensure_ascii=False, indent=1)
print('\n写出 out/k3_phase4.json')
