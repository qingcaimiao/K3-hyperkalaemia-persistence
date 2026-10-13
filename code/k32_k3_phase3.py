# -*- coding: utf-8 -*-
"""
K3 阶段③：三档定义（transient / confirmed / sustained）与结局关联
关键设计 —— 避免循环论证（用户铁律）：
  死亡或快速转出者不会再有后续测量 → 会被系统性归入"一过性"，造成 informative censoring。
  · 主分析 = 7 天 landmark：暴露（0–7 天血钾轨迹）在 landmark 前确定，结局（landmark 后的院内死亡、
    住院时长）在 landmark 后；队列限定为住院（含死亡）持续 >7 天者。
  · 对照 = 全队列粗率（不做 landmark 限制），用于显示偏倚方向。
分组（互斥，阈 5.5）：
  no_event   24h 后无 ≥5.5
  transient  首次 ≥5.5 且 24h 内下一次 <5.5
  confirmed  首次 ≥5.5 且 24h 内下一次 ≥5.5，但并非全部 ≥5.5
  sustained  首次 ≥5.5 且 24h 内全部 ≥5.5
  unknown    首次 ≥5.5 但 24h 内无复查
"""
import duckdb, pandas as pd, numpy as np, json, warnings
warnings.filterwarnings('ignore')
M = 'D:/shujuku/mimic-iv-3.1'; E = 'D:/shujuku/EICU 2.0'
T = lambda p: "read_csv_auto('{}', strict_mode=false, ignore_errors=true)".format(p)
con = duckdb.connect(); con.execute('SET threads=6')
BASE, HORIZON = 1440, 10080
CIC = "regexp_matches(first_careunit,'CCU|CVICU')"
CIT = "regexp_matches(unittype,'Cardiac ICU|CCU|CSICU|CTICU')"

# ---------- 结局与人口学 ----------
print('抽取结局与人口学 …')
qm = f"""
WITH icu AS (SELECT stay_id, subject_id, hadm_id, intime,
                    ROW_NUMBER() OVER (PARTITION BY hadm_id ORDER BY intime) AS rn
             FROM {T(M + '/icu/icustays.csv')} WHERE {CIC}),
     co AS (SELECT * FROM icu WHERE rn = 1)
SELECT co.stay_id AS sid,
       DATE_DIFF('minute', co.intime, a.dischtime) AS los_hosp_min,
       DATE_DIFF('minute', co.intime, a.deathtime)  AS t_death_min,
       a.hospital_expire_flag AS died_inhosp,
       p.gender AS sex,
       TRY_CAST(p.anchor_age AS DOUBLE)
         + GREATEST(TRY_CAST(EXTRACT(YEAR FROM co.intime) AS INT) - p.anchor_year, 0) AS age
FROM co JOIN {T(M + '/hosp/admissions.csv')} a ON a.hadm_id = co.hadm_id
        JOIN {T(M + '/hosp/patients.csv')}   p ON p.subject_id = co.subject_id"""
om = con.execute(qm).df(); om['db'] = 'MIMIC-IV'
qe = f"""
SELECT patientunitstayid AS sid,
       TRY_CAST(hospitaldischargeoffset AS DOUBLE) AS los_hosp_min,
       NULL AS t_death_min,
       CASE WHEN lower(coalesce(hospitaldischargestatus,'')) LIKE 'expired%' THEN 1 ELSE 0 END AS died_inhosp,
       gender AS sex, TRY_CAST(age AS DOUBLE) AS age
FROM {T(E + '/patient.csv')} WHERE {CIT}"""
oe = con.execute(qe).df(); oe['db'] = 'eICU-CRD'
OUT = {}

for nm, d, oc, idc in [('MIMIC-IV', pd.read_pickle('out/k3_k_series_mimic.pkl'), om, 'mimic'),
                       ('eICU-CRD', pd.read_pickle('out/k3_k_series_eicu.pkl'), oe, 'eicu')]:
    print('\n' + '=' * 104); print(nm); print('=' * 104)
    d = d.sort_values(['sid', 't']).reset_index(drop=True)
    gb = {sid: g for sid, g in d.groupby('sid', sort=False)}
    rows = []
    for sid, g in gb.items():
        pre = g[g.t <= BASE]
        if len(pre) == 0: continue
        kb = float(pre.k.max())
        if kb >= 5.5: continue
        post = g[g.t > BASE]
        if len(post) == 0: continue
        pos = post[post.k >= 5.5]
        if len(pos) == 0:
            rows.append(dict(sid=sid, grp='no_event', k_base=kb, k_idx=np.nan)); continue
        idx = pos.iloc[0]
        after = post[post.t > idx.t]
        a24 = after[after.t <= idx.t + BASE]
        if len(a24) == 0:       grp = 'unknown'
        elif float(a24.k.iloc[0]) < 5.5: grp = 'transient'
        elif bool((a24.k >= 5.5).all()): grp = 'sustained'
        else:                   grp = 'confirmed'
        rows.append(dict(sid=sid, grp=grp, k_base=kb, k_idx=float(idx.k)))
    coh = pd.DataFrame(rows).merge(oc, on='sid', how='left')
    n_coh = len(coh)
    print('K3 队列 %s 例（基线<5.5 且 24h 后有测量）；结局可链接 %s 例'
          % (format(n_coh, ','), format(int(coh.los_hosp_min.notna().sum()), ',')))
    print('\n--- 分组构成 ---')
    for g, lab in [('no_event', '无事件'), ('transient', '一过性'), ('confirmed', '已确认(非持续)'),
                   ('sustained', '持续'), ('unknown', '未复查')]:
        s = coh[coh.grp == g]
        print('  %-8s %-12s %6s 例 (%.1f%%)' % (g, lab, format(len(s), ','), 100 * len(s) / n_coh))

    # ---------- 对照：全队列粗率（不做 landmark，暴露=整个住院) ----------
    print('\n--- 对照 A：全队列粗率（不做 landmark；此处存在 informative censoring）---')
    print('  %-16s %7s %10s' % ('组', 'n', '院内死亡%'))
    full_rows = []
    for g in ['no_event', 'transient', 'confirmed', 'sustained', 'unknown']:
        s = coh[coh.grp == g]
        if not len(s): continue
        d_ = 100 * float(s.died_inhosp.mean())
        full_rows.append(dict(grp=g, n=int(len(s)), died=round(d_, 1)))
        print('  %-16s %7s %9.1f%%' % (g, format(len(s), ','), d_))

    # ---------- 主分析：7 天 landmark ----------
    lmk = coh[coh.los_hosp_min > HORIZON].copy()
    lmk['los_after_d'] = (lmk.los_hosp_min - HORIZON) / 1440.0
    print('\n--- 主分析：7 天 landmark 队列（住院/死亡均 >7 天）n=%s（%.1f%% 的队列）---'
          % (format(len(lmk), ','), 100 * len(lmk) / n_coh))
    print('  %-16s %7s %10s %12s' % ('组', 'n', '院内死亡%', 'landmark后住院天数中位'))
    main_rows = []
    for g in ['no_event', 'transient', 'confirmed', 'sustained', 'unknown']:
        s = lmk[lmk.grp == g]
        if not len(s): continue
        d_ = 100 * float(s.died_inhosp.mean()); l_ = float(s.los_after_d.median())
        main_rows.append(dict(grp=g, n=int(len(s)), died=round(d_, 1), los_med=round(l_, 1)))
        print('  %-16s %7s %9.1f%% %12.1f' % (g, format(len(s), ','), d_, l_))

    # ---------- 索引值分层内的三档比较 ----------
    print('\n--- 同一索引值层内：一过性 vs 已确认 vs 持续（死亡%）---')
    band_rows = []
    for lo, hi, lab in [(5.5, 6.0, '5.5–5.9'), (6.0, 6.5, '6.0–6.4'), (6.5, 20.0, '≥6.5')]:
        rec = dict(band=lab)
        line = '  %-8s' % lab
        for g in ['transient', 'confirmed', 'sustained']:
            s = lmk[(lmk.grp == g) & (lmk.k_idx >= lo) & (lmk.k_idx < hi)]
            rec[g + '_n'] = int(len(s))
            rec[g + '_died'] = round(100 * float(s.died_inhosp.mean()), 1) if len(s) else None
            line += ' | %s n=%3d 死%s%%' % (g[:4], len(s),
                                            ('%.0f' % (100 * s.died_inhosp.mean())) if len(s) else ' -')
        band_rows.append(rec); print(line)
    ne = lmk[lmk.grp == 'no_event']
    print('  %-8s | 参照（无事件）n=%d 死亡 %.1f%%' % ('—', len(ne), 100 * ne.died_inhosp.mean()))

    # ---------- 回归：landmark 后死亡 ~ 轨迹 + 索引值 + 年龄 + 性别 ----------
    print('\n--- logistic（landmark 后院内死亡）---')
    reg_out = {}
    try:
        from sklearn.linear_model import LogisticRegression
        sub = lmk[lmk.grp != 'unknown'].copy()
        sub['g_transient'] = (sub.grp == 'transient').astype(int)
        sub['g_confirmed'] = (sub.grp == 'confirmed').astype(int)
        sub['g_sustained'] = (sub.grp == 'sustained').astype(int)
        sub['k_idx_f'] = sub.k_idx.fillna(sub.k_base)
        sub['age_f'] = sub.age.fillna(sub.age.median())
        sub['sex_m'] = (sub.sex.astype(str).str.upper().str[0] == 'M').astype(int)
        for feats, lab in [(['g_transient', 'g_confirmed', 'g_sustained'], '仅轨迹档（无事件为参照）'),
                           (['g_transient', 'g_confirmed', 'g_sustained', 'k_idx_f'], '+ 索引值'),
                           (['g_transient', 'g_confirmed', 'g_sustained', 'k_idx_f', 'age_f', 'sex_m'],
                            '+ 年龄性别')]:
            X = sub[feats].astype(float).values
            m = LogisticRegression(max_iter=4000).fit(X, sub.died_inhosp.astype(int).values)
            rng = np.random.default_rng(5); bs = []
            for _ in range(400):
                i = rng.integers(0, len(sub), len(sub))
                if len(np.unique(sub.died_inhosp.values[i])) < 2: continue
                try:
                    bs.append(LogisticRegression(max_iter=4000).fit(X[i], sub.died_inhosp.values[i]).coef_[0])
                except Exception: pass
            bs = np.array(bs)
            print('  %s' % lab)
            for j, v in enumerate(['g_transient', 'g_confirmed', 'g_sustained']):
                or_ = float(np.exp(m.coef_[0][j]))
                ci = np.exp(np.percentile(bs[:, j], [2.5, 97.5])) if len(bs) > 50 else [np.nan, np.nan]
                print('     OR %-12s = %.2f (%.2f–%.2f)' % (v, or_, ci[0], ci[1]))
                if lab.startswith('+ 年龄'):
                    reg_out[v] = dict(or_=round(or_, 2), ci=[round(float(ci[0]), 2), round(float(ci[1]), 2)])
    except Exception as ex:
        print('  回归不可用：', str(ex)[:90])

    # ---------- 次要结局：住院期间 RRT ----------
    try:
        tx = pd.read_pickle('out/k3_tx_%s.pkl' % idc)
        rrt = set(tx.loc[tx.cat == 'rrt', 'sid'].astype(int))
        lmk['rrt'] = lmk.sid.isin(rrt).astype(int)
        print('\n--- 次要结局：住院期间 RRT（注意与高钾互为因果，仅描述）---')
        for g in ['no_event', 'transient', 'confirmed', 'sustained']:
            s = lmk[lmk.grp == g]
            if len(s): print('  %-12s n=%5d RRT %.1f%%' % (g, len(s), 100 * s.rrt.mean()))
    except Exception as ex:
        print('\n  RRT 不可用：', str(ex)[:70])

    OUT[nm] = dict(n_coh=n_coh, n_landmark=int(len(lmk)), full=full_rows, main=main_rows,
                   bands=band_rows, reg=reg_out,
                   died_no_event=round(100 * float(ne.died_inhosp.mean()), 1))
json.dump(OUT, open('out/k3_phase3.json', 'w'), ensure_ascii=False, indent=1)
print('\n写出 out/k3_phase3.json')
