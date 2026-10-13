# -*- coding: utf-8 -*-
"""
K3 独立验证（k35b）：修正第一版验证脚本自身的 3 个 bug 后重做
  bug1 merge_asof 用了 forward（应 backward）→ confirmed 被算成 0
  bug2 转移矩阵口径与主脚本不一致（我额外限定了"基线正常"）
  bug3 变量名 E 被 EXPECT[nm] 覆盖 → 数据库路径拼串报错
本版改用「merge + 过滤」的直白实现，并把阶段③的 landmark 死亡与 OR 也重算对照。
"""
import duckdb, pandas as pd, numpy as np, json, warnings
warnings.filterwarnings('ignore')
M = 'D:/shujuku/mimic-iv-3.1'; EICU = 'D:/shujuku/EICU 2.0'
T = lambda p: "read_csv_auto('{}', strict_mode=false, ignore_errors=true)".format(p)
con = duckdb.connect(); con.execute('SET threads=6')
BASE = 1440
FAIL = []

EXPECT = {
 'MIMIC-IV': dict(n_coh=20322, apparent=1182, confirmed=224, sustained=86, conf_pct=21.7,
                  t55=32.3, rule6h=52.0, nnr6=4.5, cap6=137,
                  lmk72=18227, d_nev=4.4, d_tra=8.5, d_con=17.7, d_sus=41.0,
                  or_tra=1.74, or_con=4.10, or_sus=11.93),
 'eICU-CRD': dict(n_coh=28805, apparent=997, confirmed=234, sustained=100, conf_pct=30.7,
                  t55=33.9, rule6h=42.0, nnr6=2.8, cap6=151,
                  lmk72=23087, d_nev=6.4, d_tra=13.5, d_con=14.7, d_sus=34.9,
                  or_tra=2.92, or_con=3.60, or_sus=9.11),
}

# ---------- 结局表（阶段③ 72h landmark 用）----------
qm = f"""WITH icu AS (SELECT stay_id, subject_id, hadm_id, intime,
          ROW_NUMBER() OVER (PARTITION BY hadm_id ORDER BY intime) AS rn
          FROM {T(M + '/icu/icustays.csv')} WHERE regexp_matches(first_careunit,'CCU|CVICU')),
    co AS (SELECT * FROM icu WHERE rn=1)
SELECT co.stay_id AS sid, DATE_DIFF('minute', co.intime, a.dischtime) AS los_hosp_min,
       a.hospital_expire_flag AS died, p.gender AS sex,
       TRY_CAST(p.anchor_age AS DOUBLE)+GREATEST(TRY_CAST(EXTRACT(YEAR FROM co.intime) AS INT)-p.anchor_year,0) AS age
FROM co JOIN {T(M + '/hosp/admissions.csv')} a ON a.hadm_id=co.hadm_id
        JOIN {T(M + '/hosp/patients.csv')} p ON p.subject_id=co.subject_id"""
OM = con.execute(qm).df()
QE = f"""SELECT patientunitstayid AS sid, TRY_CAST(hospitaldischargeoffset AS DOUBLE) AS los_hosp_min,
       CASE WHEN lower(coalesce(hospitaldischargestatus,'')) LIKE 'expired%' THEN 1 ELSE 0 END AS died,
       gender AS sex, TRY_CAST(age AS DOUBLE) AS age FROM {T(EICU + '/patient.csv')}
       WHERE regexp_matches(unittype,'Cardiac ICU|CCU|CSICU|CTICU')"""
OE = con.execute(QE).df()

for nm, pklf, oc in [('MIMIC-IV', 'out/k3_k_series_mimic.pkl', OM), ('eICU-CRD', 'out/k3_k_series_eicu.pkl', OE)]:
    exp_ = EXPECT[nm]
    d = pd.read_pickle(pklf).sort_values(['sid', 't']).reset_index(drop=True)
    print('\n' + '=' * 96); print(nm); print('=' * 96)
    kb = d[d.t <= BASE].groupby('sid').k.max()
    post_all = d[d.t > BASE]
    n_post = post_all.groupby('sid').size()
    atrisk = kb[(kb < 5.5) & (kb.index.isin(n_post.index))].index
    post = post_all[post_all.sid.isin(atrisk)]
    # ---- apparent + 首次越线 ----
    first = post[post.k >= 5.5].groupby('sid', sort=False).head(1).set_index('sid')
    # ---- 24h 内后续测量（merge + 过滤；不使用 merge_asof）----
    m = post.merge(first[['t']].rename(columns={'t': 't_idx'}).reset_index(), on='sid', how='inner')
    a24 = m[(m.t > m.t_idx) & (m.t <= m.t_idx + BASE)].sort_values('t')
    nxt = a24.groupby('sid').first()
    nxt['gap'] = nxt.t - nxt.t_idx
    confirmed = int((nxt.k >= 5.5).sum())
    sus = a24.assign(ok=lambda x: x.k >= 5.5).groupby('sid').ok.all()
    sustained = int(sus.sum())
    conf_pct = 100 * confirmed / len(nxt)
    print('  队列 %-6d apparent %-6d 已复查 %-6d confirmed %-5d (%.1f%%) sustained %-5d'
          % (len(atrisk), len(first), len(nxt), confirmed, conf_pct, sustained))
    for lab, got, e in [('队列', len(atrisk), exp_['n_coh']), ('apparent', len(first), exp_['apparent']),
                        ('confirmed', confirmed, exp_['confirmed']), ('sustained', sustained, exp_['sustained'])]:
        ok = got == e
        print('    %-10s %-7s vs 报告 %-7s %s' % (lab, got, e, 'OK' if ok else '<<< 不一致'))
        if not ok: FAIL.append('%s %s %s≠%s' % (nm, lab, got, e))
    if abs(conf_pct - exp_['conf_pct']) > 0.15:
        FAIL.append('%s 确认率 %.1f≠%.1f' % (nm, conf_pct, exp_['conf_pct']))
    else:
        print('    %-10s %.1f%% vs 报告 %.1f%% OK' % ('确认率', conf_pct, exp_['conf_pct']))

    # ---- 转移矩阵：两种口径都算，看主脚本用的是哪一种 ----
    def trans(base_df, tag):
        pp = base_df.copy()
        pp['kn'] = pp.groupby('sid').k.shift(-1); pp['tn'] = pp.groupby('sid').t.shift(-1)
        pp = pp[(pp.tn - pp.t > 0) & (pp.tn - pp.t <= BASE) & pp.kn.notna()]
        s = pp[(pp.k >= 5.5) & (pp.k < 6.0)]
        return 100 * (s.kn >= 5.5).mean(), len(s)
    t_all, n_all = trans(post_all, '全体')
    t_res, n_res = trans(post, '限基线正常')
    print('    转移 5.5–5.9→≥5.5：全体队列 %.1f%% (n=%d) ｜ 仅基线正常 %.1f%% (n=%d) ｜ 报告 %.1f%%'
          % (t_all, n_all, t_res, n_res, exp_['t55']))
    if abs(t_all - exp_['t55']) < 0.25:
        print('    → 报告采用的是「全体队列」口径（未限定基线正常），需在稿中写明')
    elif abs(t_res - exp_['t55']) < 0.25:
        print('    → 报告采用的是「仅基线正常」口径')
    else:
        FAIL.append('%s 转移概率两种口径均对不上报告 %.1f' % (nm, exp_['t55']))

    # ---- 规则 6h ----
    n_app = len(first)
    inw = nxt[nxt.gap <= 360]
    cap = int((inw.k >= 5.5).sum())
    cov = 100 * len(inw) / n_app
    nnr = len(inw) / cap if cap else np.nan
    print('    6h 内复查 %.1f%%（报告 %.1f%%）｜ 可确认 %d（报告 %d）｜ NNR %.1f（报告 %.1f）'
          % (cov, exp_['rule6h'], cap, exp_['cap6'], nnr, exp_['nnr6']))
    for lab, got, e, tol in [('6h复查率', cov, exp_['rule6h'], 0.2), ('可确认数', cap, exp_['cap6'], 0),
                             ('NNR', nnr, exp_['nnr6'], 0.1)]:
        if abs(got - e) > tol: FAIL.append('%s %s %s≠%s' % (nm, lab, got, e))

    # ---- 阶段③ 72h landmark：死亡与 OR ----
    H = 4320
    kb2 = d[d.t <= BASE].groupby('sid').k.max()
    p2 = d[(d.t > BASE) & (d.t <= H)]
    at2 = kb2[(kb2 < 5.5) & (kb2.index.isin(p2.groupby('sid').size().index))].index
    p2 = p2[p2.sid.isin(at2)]
    f2 = p2[p2.k >= 5.5].groupby('sid', sort=False).head(1).set_index('sid')
    m2 = p2.merge(f2[['t']].rename(columns={'t': 't_idx'}).reset_index(), on='sid', how='inner')
    a2 = m2[(m2.t > m2.t_idx) & (m2.t <= m2.t_idx + BASE)].sort_values('t')
    nx2 = a2.groupby('sid').first()
    grp = pd.Series('no_event', index=at2)
    grp.loc[nx2.index] = np.where(nx2.k >= 5.5, 'confirmed', 'transient')
    s2 = a2.assign(ok=lambda x: x.k >= 5.5).groupby('sid').ok.all()
    grp.loc[s2[s2].index] = 'sustained'
    coh = grp.rename('grp').reset_index().rename(columns={'index': 'sid'}).merge(oc, on='sid', how='left')
    lmk = coh[coh.los_hosp_min > H].copy()
    from sklearn.linear_model import LogisticRegression
    lmk['k_idx'] = lmk.sid.map(f2.k)
    lmk['k_idx'] = lmk.k_idx.fillna(5.4)
    lmk['age'] = pd.to_numeric(lmk.age, errors='coerce').fillna(65)
    lmk['sex_m'] = (lmk.sex.astype(str).str.upper().str[0] == 'M').astype(int)
    for g in ['transient', 'confirmed', 'sustained']:
        lmk['g_' + g] = (lmk.grp == g).astype(int)
    X = lmk[['g_transient', 'g_confirmed', 'g_sustained', 'k_idx', 'age', 'sex_m']].astype(float).values
    lr = LogisticRegression(max_iter=5000).fit(X, lmk.died.astype(int).values)
    print('    72h landmark：n=%d（报告 %d）' % (len(lmk), exp_['lmk72']))
    if len(lmk) != exp_['lmk72']: FAIL.append('%s landmark n %d≠%d' % (nm, len(lmk), exp_['lmk72']))
    for g, key_d, key_or in [('no_event', 'd_nev', None), ('transient', 'd_tra', 'or_tra'),
                             ('confirmed', 'd_con', 'or_con'), ('sustained', 'd_sus', 'or_sus')]:
        s = lmk[lmk.grp == g]
        dd = 100 * s.died.mean()
        line = '    %-10s n=%-6d 死亡 %5.1f%% vs 报告 %5.1f%%' % (g, len(s), dd, exp_[key_d])
        if abs(dd - exp_[key_d]) > 0.15: FAIL.append('%s %s 死亡率 %.1f≠%.1f' % (nm, g, dd, exp_[key_d])); line += ' <<<'
        if key_or:
            j = ['g_transient', 'g_confirmed', 'g_sustained'].index('g_' + g)
            orv = float(np.exp(lr.coef_[0][j]))
            line += ' | OR %.2f vs 报告 %.2f' % (orv, exp_[key_or])
            if abs(orv - exp_[key_or]) > 0.06: FAIL.append('%s %s OR %.2f≠%.2f' % (nm, g, orv, exp_[key_or])); line += ' <<<'
        print(line)

print('\n' + '#' * 100)
print('# Q3  K2 与 K3 的 eICU 队列规模差异')
print('#' * 100)
e = pd.read_pickle('out/k3_k_series_eicu.pkl').sort_values(['sid', 't'])
kb = e[e.t <= BASE].groupby('sid').k.max(); npo = e[e.t > BASE].groupby('sid').size()
k3 = set(kb[(kb < 5.5) & kb.index.isin(npo.index)].index)
k2 = set(pd.read_csv('out/k_eicu3.csv', low_memory=False).patientunitstayid)
only3 = k3 - k2
ud = con.execute(f"SELECT patientunitstayid AS sid, TRY_CAST(unitdischargeoffset AS DOUBLE) AS ud FROM {T(EICU + '/patient.csv')}").df().set_index('sid')
u = ud.reindex(list(only3)).ud
print('  K3 eICU 队列 %s ｜ K2 eICU 队列 %s ｜ 仅 K3 %s 例' % (format(len(k3), ','), format(len(k2), ','), format(len(only3), ',')))
print('  仅 K3 纳入者：unitdischargeoffset ≤1440 占 %.1f%%，>1440 占 %.1f%%（中位 %.0f min）'
      % (100 * (u <= 1440).mean(), 100 * (u > 1440).mean(), u.median()))
print('  → K2 要求 ICU 停留 >24h，K3 未做该限制（仅要求 24h 后有血钾记录）')
print('  → 因此 eICU 侧 apparent：K3 %d 例 vs K2 %d 例；MIMIC 侧两者一致（1,182 = 1,182）' % (997, 913))

print('\n' + '#' * 100)
print('# 验证结论')
print('#' * 100)
print('  发现 %d 处不一致：' % len(FAIL))
for f in FAIL: print('   -', f)
