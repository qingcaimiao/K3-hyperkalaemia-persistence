# -*- coding: utf-8 -*-
"""
K3 外审（DeepSeek）实证核查 —— 每条指控都用原始数据算，不靠推测
输出 out/k3_ds_check.json
核查项：
 A. sustained 组的复查次数分布（是否"只测一次也算持续"）
 B. 24h 全轨迹重新分类：all<5.5 / intermittent / all≥5.5
 C. landmark 队列中未分类组的 n（表 5 分母对不上之谜）
 D. 索引时间 vs landmark：分类窗越过 landmark 被截断的比例（信息泄露核查）
 E. 排除"索引→复查间记录到降钾治疗"的事件后，确认率是否仍低（治疗混杂敏感性）
 F. 阈值敏感性：5.0 / 5.5 / 6.0 / 6.5
 G. 各状态下复查间隔与治疗记录比例
"""
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings('ignore')
BASE = 1440
SER = {'MIMIC-IV': 'out/k3_k_series_mimic.pkl', 'eICU-CRD': 'out/k3_k_series_eicu.pkl'}
TX = {'MIMIC-IV': 'out/k3_tx_mimic.pkl', 'eICU-CRD': 'out/k3_tx_eicu.pkl'}
OUT = {}


def build(thr):
    """返回 {db: DataFrame(sid, k_base, k_idx, t_idx, n_after, all_ge, any_ge, k_next, dt_next)}"""
    res = {}
    for nm, f in SER.items():
        d = pd.read_pickle(f).sort_values(['sid', 't']).reset_index(drop=True)
        rows = []
        for sid, g in d.groupby('sid', sort=False):
            pre = g[g.t <= BASE]
            if len(pre) == 0 or float(pre.k.max()) >= thr:
                continue
            post = g[g.t > BASE]
            if len(post) == 0:
                continue
            kb = float(pre.k.max())
            pos = post[post.k >= thr]
            if len(pos) == 0:
                continue
            idx = pos.iloc[0]
            a = post[(post.t > idx.t) & (post.t <= idx.t + BASE)]
            rows.append(dict(sid=int(sid), k_base=kb, k_idx=float(idx.k), t_idx=float(idx.t),
                             n_after=int(len(a)),
                             all_ge=bool((a.k >= thr).all()) if len(a) else False,
                             any_ge=bool((a.k >= thr).any()) if len(a) else False,
                             k_next=float(a.k.iloc[0]) if len(a) else np.nan,
                             dt_next=float(a.t.iloc[0] - idx.t) if len(a) else np.nan))
        res[nm] = pd.DataFrame(rows)
    return res


print('=' * 100)
print('A. sustained 组的复查次数分布（"只测一次也算持续？"）')
print('=' * 100)
ev55 = build(5.5)
OUT['A'] = {}
for nm, e in ev55.items():
    s = e[e.all_ge].copy()
    vc = s.n_after.value_counts().sort_index()
    print('\n%s  sustained n=%d' % (nm, len(s)))
    print('  索引后 24h 内复查次数分布：')
    for k, v in vc.head(10).items():
        print('    %2d 次: %4d (%.1f%%)' % (k, v, 100 * v / len(s)))
    print('  → 仅 1 次测量即判为持续： %d (%.1f%%)' % (int((s.n_after == 1).sum()),
                                                100 * (s.n_after == 1).mean()))
    print('  → ≥2 次：%d (%.1f%%) ；≥3 次：%d (%.1f%%)' % (
        int((s.n_after >= 2).sum()), 100 * (s.n_after >= 2).mean(),
        int((s.n_after >= 3).sum()), 100 * (s.n_after >= 3).mean()))
    print('  → 复查次数中位 %.1f (IQR %.1f–%.1f)' % (s.n_after.median(),
                                                  s.n_after.quantile(.25), s.n_after.quantile(.75)))
    # 严格版：要求 ≥2 次全部 ≥5.5
    s2 = s[s.n_after >= 2]
    OUT['A'][nm] = dict(n_sustained=int(len(s)), n1=int((s.n_after == 1).sum()),
                        pct1=round(100 * float((s.n_after == 1).mean()), 1),
                        n_ge2=int(len(s2)), pct_ge2=round(100 * float(len(s2) / len(s)), 1),
                        n_ge3=int((s.n_after >= 3).sum()),
                        med_n=float(s.n_after.median()),
                        dist={int(k): int(v) for k, v in vc.items()})

print('\n' + '=' * 100)
print('B. 24h 全轨迹重新分类（transient 是否只看下一次？）')
print('=' * 100)
OUT['B'] = {}
for nm, e in ev55.items():
    r = e[e.n_after > 0].copy()
    strict_tr = ((~r.any_ge)).sum()
    inter = (r.any_ge & ~r.all_ge).sum()
    sust = r.all_ge.sum()
    print('\n%s  有复查的事件 n=%d' % (nm, len(r)))
    print('  全部 <5.5（严格一过性）      : %4d (%5.1f%% of 有复查者)' % (strict_tr, 100 * strict_tr / len(r)))
    print('  间歇（至少一次≥5.5 但非全部）: %4d (%5.1f%%)' % (inter, 100 * inter / len(r)))
    print('  全部 ≥5.5（持续）            : %4d (%5.1f%%)' % (sust, 100 * sust / len(r)))
    print('  → 现稿"一过性"=%d，其中被误归为"不再升高"的间歇事件 %d (%.1f%% of 现一过性)'
          % (int((r.k_next < 5.5).sum()), inter, 100 * inter / max(int((r.k_next < 5.5).sum()), 1)))
    OUT['B'][nm] = dict(n_rechecked=int(len(r)), strict_transient=int(strict_tr),
                        intermittent=int(inter), sustained=int(sust),
                        pct_strict=round(100 * float(strict_tr / len(r)), 1),
                        pct_inter=round(100 * float(inter / len(r)), 1),
                        pct_sust=round(100 * float(sust / len(r)), 1),
                        n_transient_now=int((r.k_next < 5.5).sum()))

print('\n' + '=' * 100)
print('C. 表 5 分母核查（未分类组 n 未列出）')
print('=' * 100)
ph = json.load(open('out/k3_phase3b.json', encoding='utf-8'))
OUT['C'] = {}
for nm, v in ph.items():
    for lab in ['72 h', '7 d']:
        rr = {r['grp']: r['n'] for r in v[lab]['rows']}
        tot = v[lab]['n_landmark']
        s = rr.get('no_event', 0) + rr.get('transient', 0) + rr.get('confirmed', 0) + rr.get('sustained', 0)
        print('  %-9s %-5s 表头 n=%s | no_ep %s + tr %s + conf %s + sust %s = %s | 差 = %s（未分类）'
              % (nm, lab, format(tot, ','), rr.get('no_event'), rr.get('transient'),
                 rr.get('confirmed'), rr.get('sustained'), format(s, ','), tot - s))
        OUT['C']['%s|%s' % (nm, lab)] = dict(n_landmark=tot, no_event=rr.get('no_event'),
                                             transient=rr.get('transient'), confirmed=rr.get('confirmed'),
                                             sustained=rr.get('sustained'), unclassified=rr.get('unknown'),
                                             sum4=s, diff=tot - s)

print('\n' + '=' * 100)
print('D. 分类窗是否越过 landmark（信息泄露核查）')
print('=' * 100)
OUT['D'] = {}
for nm, f in SER.items():
    d = pd.read_pickle(f).sort_values(['sid', 't']).reset_index(drop=True)
    for H, lab in [(4320, '72 h'), (10080, '7 d')]:
        e = ev55[nm]
        e2 = e[e.t_idx <= H]
        over = e2[(e2.t_idx + BASE) > H]
        print('  %-9s %-5s 索引发生在 landmark 前且分类窗越过 landmark： %d / %d (%.1f%%)'
              % (nm, lab, len(over), len(e2), 100 * len(over) / max(len(e2), 1)))
        OUT['D']['%s|%s' % (nm, lab)] = dict(n_idx_before_lmk=int(len(e2)),
                                             n_window_over=int(len(over)),
                                             pct=round(100 * float(len(over) / max(len(e2), 1)), 2))

print('\n' + '=' * 100)
print('E. 治疗混杂敏感性：排除"索引→复查间记录到降钾治疗"的事件后确认率')
print('=' * 100)
OUT['E'] = {}
for nm in SER:
    e = ev55[nm]
    tx = pd.read_pickle(TX[nm])
    r = e[e.n_after > 0].copy()
    txs = tx.groupby('sid')['off'].apply(lambda s: np.array(sorted(s.values))).to_dict()
    txcat = tx.groupby('sid')['cat'].apply(lambda s: set(s)).to_dict()

    def has_tx(row):
        arr = txs.get(row.sid)
        if arr is None:
            return False
        return bool(((arr >= row.t_idx) & (arr <= row.t_idx + (row.dt_next if not np.isnan(row.dt_next) else BASE))).any())

    r['tx'] = r.apply(has_tx, axis=1)
    allc = 100 * float((r.k_next >= 5.5).mean())
    unt = r[~r.tx]
    tre = r[r.tx]
    print('\n%s  有复查事件 n=%d' % (nm, len(r)))
    print('  窗口内记录到降钾治疗： %d (%.1f%%)' % (int(r.tx.sum()), 100 * r.tx.mean()))
    print('  全部确认率                : %.1f%% (n=%d)' % (allc, len(r)))
    print('  未记录治疗者确认率        : %.1f%% (n=%d)' % (100 * float((unt.k_next >= 5.5).mean()), len(unt)))
    if len(tre):
        print('  记录治疗者确认率          : %.1f%% (n=%d)' % (100 * float((tre.k_next >= 5.5).mean()), len(tre)))
    OUT['E'][nm] = dict(n_rechecked=int(len(r)), n_tx=int(r.tx.sum()),
                        pct_tx=round(100 * float(r.tx.mean()), 1),
                        confirm_all=round(allc, 1),
                        confirm_untreated=round(100 * float((unt.k_next >= 5.5).mean()), 1),
                        n_untreated=int(len(unt)),
                        confirm_treated=round(100 * float((tre.k_next >= 5.5).mean()), 1) if len(tre) else None,
                        n_treated=int(len(tre)))

print('\n' + '=' * 100)
print('F. 阈值敏感性（5.0 / 5.5 / 6.0 / 6.5）')
print('=' * 100)
OUT['F'] = {}
for thr in [5.0, 5.5, 6.0, 6.5]:
    r = build(thr)
    line = '  阈 %.1f :' % thr
    for nm in SER:
        e = r[nm]
        rr = e[e.n_after > 0]
        conf = int((rr.k_next >= thr).sum())
        sust = int(rr.all_ge.sum())
        line += '  %s apparent %d | 有复查 %d | 确认 %d (%.1f%%) | 持续 %d (%.1f%%)' % (
            nm, len(e), len(rr), conf, 100 * conf / max(len(rr), 1), sust, 100 * sust / max(len(rr), 1))
        OUT['F']['%.1f|%s' % (thr, nm)] = dict(apparent=int(len(e)), rechecked=int(len(rr)),
                                               confirmed=int(conf),
                                               pct_confirmed=round(100 * float(conf / max(len(rr), 1)), 1),
                                               sustained=int(sust),
                                               pct_sustained=round(100 * float(sust / max(len(rr), 1)), 1))
    print(line)

json.dump(OUT, open('out/k3_ds_check.json', 'w', ensure_ascii=False, indent=1))
print('\n写出 out/k3_ds_check.json')
