# -*- coding: utf-8 -*-
"""
K3 外审整改（第二批）：五档重分类 + sustained 测量次数敏感性 + 治疗混杂敏感性 + 阈值敏感性 + 队列流程

口径纪律（2026-10-13 复核确认）：
  A. **landmark 分析（五档重分类）**：暴露窗必须限定在 (24h, H] 内，分类窗 = (idx.t, min(idx.t+24h, H)]。
     与 k33_k3_phase3b.py 完全一致 —— 否则 landmark 之后的高钾会被算成事件，构成信息泄露。
  B. **阈值敏感性 / 治疗敏感性**：无 landmark，用 k30/k31 的全窗口径（暴露窗 = 全部 t>24h）。
  C. 凡两个列表并行索引处，一律 assert len(a)==len(b)，并同时打印变量名与系数。

落盘：out/k39_reclass.csv / k39_threshold.csv / k39_treatment.csv / k39_flow.csv / k39_or.json
"""
import duckdb, pandas as pd, numpy as np, json, warnings
from sklearn.linear_model import LogisticRegression
warnings.filterwarnings('ignore')

M = 'D:/shujuku/mimic-iv-3.1'; E = 'D:/shujuku/EICU 2.0'
T = lambda p: "read_csv_auto('{}', strict_mode=false, ignore_errors=true)".format(p)
con = duckdb.connect(); con.execute('SET threads=6')
BASE = 1440
CIC = "regexp_matches(first_careunit,'CCU|CVICU')"
CIT = "regexp_matches(unittype,'Cardiac ICU|CCU|CSICU|CTICU')"
CATS = ['insulin_glucose', 'binder', 'iv_calcium', 'bicarbonate', 'rrt']

qm = f"""WITH icu AS (SELECT stay_id, subject_id, hadm_id, intime,
             ROW_NUMBER() OVER (PARTITION BY hadm_id ORDER BY intime) AS rn
             FROM {T(M + '/icu/icustays.csv')} WHERE {CIC}), co AS (SELECT * FROM icu WHERE rn=1)
SELECT co.stay_id AS sid, DATE_DIFF('minute', co.intime, a.dischtime) AS los_hosp_min,
       a.hospital_expire_flag AS died_inhosp, p.gender AS sex,
       TRY_CAST(p.anchor_age AS DOUBLE)+GREATEST(TRY_CAST(EXTRACT(YEAR FROM co.intime) AS INT)-p.anchor_year,0) AS age
FROM co JOIN {T(M + '/hosp/admissions.csv')} a ON a.hadm_id=co.hadm_id
        JOIN {T(M + '/hosp/patients.csv')} p ON p.subject_id=co.subject_id"""
om = con.execute(qm).df()
qe = f"""SELECT patientunitstayid AS sid, TRY_CAST(hospitaldischargeoffset AS DOUBLE) AS los_hosp_min,
       CASE WHEN lower(coalesce(hospitaldischargestatus,'')) LIKE 'expired%' THEN 1 ELSE 0 END AS died_inhosp,
       gender AS sex, TRY_CAST(age AS DOUBLE) AS age FROM {T(E + '/patient.csv')} WHERE {CIT}"""
oe = con.execute(qe).df()


def build_lmk(d, H, thr, min_meas_sust=1):
    """landmark 口径：暴露窗 (24h, H]，分类窗 (idx.t, min(idx.t+24h, H)]。与 k33 一致。"""
    rows = []
    for sid, g in d.groupby('sid', sort=False):
        pre = g[g.t <= BASE]
        if len(pre) == 0 or float(pre.k.max()) >= thr:
            continue
        post = g[(g.t > BASE) & (g.t <= H)]          # ← H 截断（防 landmark 泄露）
        if len(post) == 0:
            continue
        pos = post[post.k >= thr]
        if len(pos) == 0:
            rows.append(dict(sid=int(sid), grp='no_event', k_idx=np.nan, n_after=0,
                             win_min=np.nan, truncated=np.nan)); continue
        idx = pos.iloc[0]
        a = post[(post.t > idx.t) & (post.t <= idx.t + BASE)]
        win_min = float(min(idx.t + BASE, H) - idx.t)   # 实际可用分类窗长度（分钟）
        n = len(a)
        if n == 0:
            grp = 'unclassified'
        elif bool((a.k >= thr).all()):
            grp = 'sustained' if n >= min_meas_sust else 'conf_not_assessed'
        elif bool((a.k >= thr).any()):
            grp = 'intermittent'
        else:
            grp = 'transient'
        rows.append(dict(sid=int(sid), grp=grp, k_idx=float(idx.k), n_after=int(n),
                         win_min=win_min, truncated=int(win_min < BASE)))
    return pd.DataFrame(rows)


def build_full(thr, min_meas_sust=1):
    """全窗口径（无 landmark）：暴露窗 = 全部 t>24h。与 k30/k31 一致，用于阈值敏感性。"""
    out = {}
    for nm, f in [('MIMIC-IV', 'out/k3_k_series_mimic.pkl'), ('eICU-CRD', 'out/k3_k_series_eicu.pkl')]:
        d = pd.read_pickle(f).sort_values(['sid', 't']).reset_index(drop=True)
        rows = []
        for sid, g in d.groupby('sid', sort=False):
            pre = g[g.t <= BASE]
            if len(pre) == 0 or float(pre.k.max()) >= thr:
                continue
            post = g[g.t > BASE]
            if len(post) == 0:
                continue
            pos = post[post.k >= thr]
            if len(pos) == 0:
                rows.append(dict(sid=int(sid), grp='no_event', k_idx=np.nan, n_after=0)); continue
            idx = pos.iloc[0]
            a = post[(post.t > idx.t) & (post.t <= idx.t + BASE)]
            n = len(a)
            if n == 0:
                grp = 'unclassified'
            elif bool((a.k >= thr).all()):
                grp = 'sustained' if n >= min_meas_sust else 'conf_not_assessed'
            elif bool((a.k >= thr).any()):
                grp = 'intermittent'
            else:
                grp = 'transient'
            rows.append(dict(sid=int(sid), grp=grp, k_idx=float(idx.k), n_after=int(n)))
        out[nm] = pd.DataFrame(rows)
    return out


def regress(sub, groups, seed=3, nb=400):
    sub = sub.copy()
    names = ['g_' + g for g in groups]
    assert len(groups) == len(names), 'groups/names 长度不一致'
    for g, c in zip(groups, names):
        assert len(groups) == len(names)
        sub[c] = (sub.grp == g).astype(int)
    sub['k_idx_f'] = pd.to_numeric(sub.k_idx, errors='coerce').fillna(5.4)
    sub['age_f'] = pd.to_numeric(sub.age, errors='coerce').fillna(sub.age.median())
    sub['sex_m'] = (sub.sex.astype(str).str.upper().str[0] == 'M').astype(int)
    feats = names + ['k_idx_f', 'age_f', 'sex_m']
    X = sub[feats].astype(float).values; y = sub.died_inhosp.astype(int).values
    if len(np.unique(y)) < 2:
        return {}
    m = LogisticRegression(max_iter=4000).fit(X, y)
    coef = m.coef_[0]
    assert len(feats) == len(coef), 'feats/coef 长度不一致: %d vs %d' % (len(feats), len(coef))
    print('     [回归] 变量与系数：' + ' | '.join('%s %.3f' % (f, c) for f, c in zip(feats, coef)))
    rng = np.random.default_rng(seed); bs = []
    for _ in range(nb):
        i = rng.integers(0, len(y), len(y))
        if len(np.unique(y[i])) < 2:
            continue
        try:
            b = LogisticRegression(max_iter=4000).fit(X[i], y[i]).coef_[0]
            assert len(b) == len(feats)
            bs.append(b)
        except Exception:
            pass
    bs = np.array(bs)
    res = {}
    for j, nm_ in enumerate(names):
        ci = np.exp(np.percentile(bs[:, j], [2.5, 97.5])) if len(bs) > 50 else [np.nan, np.nan]
        res[nm_[2:]] = dict(or_=round(float(np.exp(coef[j])), 2), lo=round(float(ci[0]), 2),
                            hi=round(float(ci[1]), 2))
    assert not any(np.isnan(v['lo']) for v in res.values()), 'CI 计算失败（bootstrap 有效次数不足）'
    return res


GROUPS = ['transient', 'intermittent', 'conf_not_assessed', 'sustained']
D5 = ['no_event'] + GROUPS + ['unclassified']
rows_re, rows_thr, rows_tx, rows_flow = [], [], [], []
OR_STORE = {}
TRUNC = {}

# ============ 1) 五档重分类（landmark 口径，与 k33 一致） ============
for thr, minm, tag in [(5.5, 1, 'primary'), (5.5, 2, 'sust>=2'), (5.5, 3, 'sust>=3')]:
    print('\n' + '#' * 100)
    print('# 五档重分类：阈 %.1f，sustained 至少 %d 次测量（%s）；暴露窗 (24h, H]' % (thr, minm, tag))
    print('#' * 100)
    for nm, dpkl, oc in [('MIMIC-IV', 'out/k3_k_series_mimic.pkl', om),
                         ('eICU-CRD', 'out/k3_k_series_eicu.pkl', oe)]:
        d = pd.read_pickle(dpkl).sort_values(['sid', 't']).reset_index(drop=True)
        for H, lab in [(4320, '72 h'), (10080, '7 d')]:
            coh = build_lmk(d, H, thr, minm).merge(oc, on='sid', how='left')
            lmk = coh[coh.los_hosp_min > H]
            print('\n=== %s  %s landmark  n=%s' % (nm, lab, format(len(lmk), ',')))
            for g in D5:
                s = lmk[lmk.grp == g]
                if not len(s):
                    continue
                d_ = round(100 * float(s.died_inhosp.mean()), 1)
                print('     %-20s n=%6s 死亡 %5.1f%%' % (g, format(len(s), ','), d_))
                rows_re.append(dict(tag=tag, db=nm, landmark=lab, grp=g, n=int(len(s)), died=d_))
            if tag == 'primary':
                sub = lmk[lmk.grp == 'no_event']
                tr = lmk[(lmk.grp != 'no_event') & (lmk.grp != 'unclassified') & (lmk.truncated == 0)]
                print('     分类窗完整(24h)的非无事件亚组 n=%d / 全部非无事件 n=%d'
                      % (len(tr), int((lmk.grp != 'no_event').sum())))
            rr = regress(lmk[lmk.grp != 'unclassified'], GROUPS)
            for k, v in rr.items():
                print('     OR %-20s %.2f (%.2f–%.2f)' % (k, v['or_'], v['lo'], v['hi']))
                rows_re.append(dict(tag=tag, db=nm, landmark=lab, grp='OR_' + k,
                                    n=v['or_'], died=v['lo']))
            OR_STORE['%s|%s|%s' % (tag, nm, lab)] = rr
            if tag == 'primary':
                TRUNC['%s|%s' % (nm, lab)] = rr
                # 截断比例（供局限性说明）
                ev = lmk[lmk.grp != 'no_event']
                print('     暴露窗内事件的分类窗被 H 截断(<24h)比例: %.1f%% (%d/%d)'
                      % (100 * float(ev.truncated.mean()), int(ev.truncated.sum()), len(ev)))
                rows_re.append(dict(tag=tag, db=nm, landmark=lab, grp='truncated_share',
                                    n=round(100 * float(ev.truncated.mean()), 1), died=len(ev)))

# ============ 2) 治疗混杂敏感性（全窗口径，精确整数） ============
print('\n' + '#' * 100); print('# 治疗混杂敏感性：确认例数精确整数（全窗口径）')
for nm, kind in [('MIMIC-IV', 'm'), ('eICU-CRD', 'e')]:
    ev = pd.read_pickle('out/k3_events_tx_%s.pkl' % kind)
    wide = ev[['tx_' + c for c in CATS]].any(axis=1)
    narr = ev[['tn_' + c for c in CATS]].any(axis=1)
    assert len(wide) == len(narr) == len(ev)
    for wname, mask in [('wide[idx-6h,idx+复查]', wide), ('narrow[idx,idx+复查]', narr)]:
        a = ev[mask]; b = ev[~mask]
        print('  %-9s %-24s 有治疗 n=%4d 确认 %4d (%.1f%%) | 无治疗 n=%4d 确认 %4d (%.1f%%)'
              % (nm, wname, len(a), int(a.confirm.sum()), 100 * a.confirm.mean(),
                 len(b), int(b.confirm.sum()), 100 * b.confirm.mean()))
        rows_tx.append(dict(db=nm, window=wname, n_tx=int(len(a)), conf_tx=int(a.confirm.sum()),
                            pct_tx=round(100 * float(a.confirm.mean()), 1),
                            n_notx=int(len(b)), conf_notx=int(b.confirm.sum()),
                            pct_notx=round(100 * float(b.confirm.mean()), 1),
                            n_total=int(len(ev))))

# ============ 3) 阈值敏感性（全窗口径，与表2/表3 同口径） ============
print('\n' + '#' * 100); print('# 阈值敏感性（全窗口径）')
for thr in [5.0, 5.5, 6.0, 6.5]:
    E5 = build_full(thr, 1)
    for nm in ['MIMIC-IV', 'eICU-CRD']:
        e = E5[nm]
        ev = e[e.grp != 'no_event']
        rr = e[e.n_after > 0]
        conf = int((ev.grp.isin(['intermittent', 'sustained', 'conf_not_assessed'])).sum())
        sust = int((ev.grp == 'sustained').sum())
        print('  阈 %.1f %-9s apparent %5d | 有复查 %5d | 确认 %4d (%5.1f%%) | 持续 %4d (%5.1f%%)'
              % (thr, nm, len(ev), len(rr), conf, 100 * conf / max(len(rr), 1), sust,
                 100 * sust / max(len(rr), 1)))
        rows_thr.append(dict(threshold=thr, db=nm, apparent=int(len(ev)), rechecked=int(len(rr)),
                             confirmed=conf, pct_confirmed=round(100 * float(conf / max(len(rr), 1)), 1),
                             sustained=sust,
                             pct_sustained=round(100 * float(sust / max(len(rr), 1)), 1)))

# ============ 4) NNR 分子（6h 内被复查的事件数） ============
print('\n' + '#' * 100); print('# NNR 分子：6h 内被复查的 apparent 事件数')
for nm in ['MIMIC-IV', 'eICU-CRD']:
    e = pd.read_pickle('out/k3_events_%s.pkl' % ('mimic' if nm == 'MIMIC-IV' else 'eicu'))
    n_app = len(e)
    within6 = int((e.t_next <= 360).sum())
    conf6 = int(((e.t_next <= 360) & (e.k_next >= 5.5)).sum())
    print('  %-9s apparent %d | 6h 内复查 %d | 6h 内确认 %d | NNR %.2f'
          % (nm, n_app, within6, conf6, within6 / max(conf6, 1)))
    rows_tx.append(dict(db=nm, window='NNR6h', n_tx=within6, conf_tx=conf6,
                        pct_tx=round(within6 / max(conf6, 1), 2), n_notx=n_app, conf_notx=0,
                        pct_notx=0.0, n_total=n_app))

# ============ 5) 队列流程（STROBE） ============
print('\n' + '#' * 100); print('# 队列流程（STROBE）')
for nm, f in [('MIMIC-IV', 'out/k3_k_series_mimic.pkl'), ('eICU-CRD', 'out/k3_k_series_eicu.pkl')]:
    d = pd.read_pickle(f)
    n_all = d.sid.nunique()
    g = d.groupby('sid')
    pre = g.k.apply(lambda x: float(x[d.loc[x.index, 't'] <= BASE].max())
                    if (d.loc[x.index, 't'] <= BASE).any() else np.nan)
    has_pre = pre.notna(); ge55 = pre >= 5.5
    has_post = g.t.apply(lambda x: int((d.loc[x.index, 't'] > BASE).sum())) > 0
    assert len(has_pre) == len(ge55) == len(has_post) == n_all, '流程三列长度与队列不一致'
    no_pre = int((~has_pre).sum()); n_ge55 = int(ge55.sum())
    no_post = int((has_pre & (~ge55) & (~has_post)).sum())
    coh = int((has_pre & (~ge55) & has_post).sum())
    print('  %-9s %s − %s(无基线) − %s(基线≥5.5) − %s(24h后无测量) = %s'
          % (nm, format(n_all, ','), format(no_pre, ','), format(n_ge55, ','), format(no_post, ','),
             format(coh, ',')))
    assert n_all - no_pre - n_ge55 - no_post == coh
    rows_flow.append(dict(db=nm, n_with_k=n_all, no_baseline=no_pre, baseline_ge55=n_ge55,
                          no_post24=no_post, cohort=coh))

pd.DataFrame(rows_re).to_csv('out/k39_reclass.csv', index=False, encoding='utf-8-sig')
pd.DataFrame(rows_thr).to_csv('out/k39_threshold.csv', index=False, encoding='utf-8-sig')
pd.DataFrame(rows_tx).to_csv('out/k39_treatment.csv', index=False, encoding='utf-8-sig')
pd.DataFrame(rows_flow).to_csv('out/k39_flow.csv', index=False, encoding='utf-8-sig')
json.dump(OR_STORE, open('out/k39_or_all.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump({k.replace('primary|', ''): v for k, v in OR_STORE.items() if k.startswith('primary|')},
          open('out/k39_or.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n写出 out/k39_reclass.csv / k39_threshold.csv / k39_treatment.csv / k39_flow.csv / k39_or.json')
