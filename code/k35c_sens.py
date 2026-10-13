# -*- coding: utf-8 -*-
"""验证发现的 Q3 问题：把 eICU 限定为 ICU 停留 >24h（与 K2 一致）后，三档结论是否变化"""
import duckdb, pandas as pd, numpy as np, warnings
warnings.filterwarnings('ignore')
E = 'D:/shujuku/EICU 2.0'
T = lambda p: "read_csv_auto('{}', strict_mode=false, ignore_errors=true)".format(p)
con = duckdb.connect()
BASE = 1440
ud = con.execute(f"SELECT patientunitstayid AS sid, TRY_CAST(unitdischargeoffset AS DOUBLE) AS ud FROM {T(E + '/patient.csv')}").df().set_index('sid')
d = pd.read_pickle('out/k3_k_series_eicu.pkl').sort_values(['sid', 't'])
k2 = pd.read_csv('out/k_eicu3.csv', low_memory=False)
print('%s' % ('=' * 90))


def run(tag, df):
    df = df[df.t <= 10080]
    kb = df[df.t <= BASE].groupby('sid').k.max()
    post = df[df.t > BASE]
    atr = kb[(kb < 5.5) & kb.index.isin(post.groupby('sid').size().index)].index
    post = post[post.sid.isin(atr)]
    f = post[post.k >= 5.5].groupby('sid', sort=False).head(1).set_index('sid')
    m = post.merge(f[['t']].rename(columns={'t': 't_idx'}).reset_index(), on='sid', how='inner')
    a = m[(m.t > m.t_idx) & (m.t <= m.t_idx + BASE)].sort_values('t')
    nx = a.groupby('sid').first()
    c = int((nx.k >= 5.5).sum())
    s = int(a.assign(ok=lambda x: x.k >= 5.5).groupby('sid').ok.all().sum())
    print('%-28s 队列 %6s | apparent %5s (%5.2f%%) | 已复查 %5s | confirmed %4s (%.1f%%) | sustained %4s (%.1f%%) | 6h复查 %.1f%%'
          % (tag, format(len(atr), ','), format(len(f), ','), 100 * len(f) / len(atr), format(len(nx), ','),
             c, 100 * c / len(f), s, 100 * s / len(f),
             100 * int(((nx.t - nx.t_idx) <= 360).sum()) / len(f)))
    return len(f), c, s


run('K3 现口径（全部）', d)
e2 = d[d.sid.isin(ud[ud.ud > 1440].index)]
run('K3 限定 ICU 停留 >24h', e2)
d3 = d[d.sid.isin(set(k2.patientunitstayid))]
run('K3 ∩ K2 队列', d3)
print('\nK2 自己的数字（对照）：队列 26,375 | 事件 913')
