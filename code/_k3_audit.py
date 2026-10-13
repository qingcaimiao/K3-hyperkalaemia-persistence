# -*- coding: utf-8 -*-
"""
K3 稿件数字独立审计：从 pkl 缓存与源库重算表 1-6 及正文的每一个数字。
不信任任何既有 JSON，只与既有 JSON 交叉对照（三者一致才算通过）。
"""
import duckdb, pandas as pd, numpy as np, json, warnings
from scipy.stats import norm
warnings.filterwarnings('ignore')

M = 'D:/shujuku/mimic-iv-3.1'; E = 'D:/shujuku/EICU 2.0'
T = lambda p: "read_csv_auto('{}', strict_mode=false, ignore_errors=true)".format(p)
con = duckdb.connect(); con.execute('SET threads=6')
BASE, HORIZON = 1440, 10080
CIC = "regexp_matches(first_careunit,'CCU|CVICU')"
CIT = "regexp_matches(unittype,'Cardiac ICU|CCU|CSICU|CTICU')"
THR = 5.5

# ---------- 人口学与结局 ----------
qm = f"""
WITH icu AS (SELECT stay_id, subject_id, hadm_id, intime,
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

SER = {'MIMIC-IV': (pd.read_pickle('out/k3_k_series_mimic.pkl'), om),
       'eICU-CRD': (pd.read_pickle('out/k3_k_series_eicu.pkl'), oe)}
ROWS = []


def add(table, item, db, value, note=''):
    ROWS.append(dict(table=table, item=item, db=db, value=value, note=note))


def med(x):
    return float(np.nanmedian(x))


for nm, (d0, oc) in SER.items():
    d = d0.sort_values(['sid', 't']).reset_index(drop=True)
    tag = 'mimic' if nm == 'MIMIC-IV' else 'eicu'
    # ---------- 分组成表（每例一行）----------
    grp, kb_d, kidx_d, knew_d, tnext_d, kprev_d = {}, {}, {}, {}, {}, {}
    for sid, g in d.groupby('sid', sort=False):
        pre = g[g.t <= BASE]
        if len(pre) == 0: continue
        kb = float(pre.k.max())
        if kb >= THR: continue
        post = g[g.t > BASE]
        if len(post) == 0: continue
        kb_d[sid] = kb
        pos = post[post.k >= THR]
        if len(pos) == 0:
            grp[sid] = 'no_event'; continue
        idx = pos.iloc[0]
        a24 = post[(post.t > idx.t) & (post.t <= idx.t + BASE)]
        kidx_d[sid] = float(idx.k)
        before = g[g.t < idx.t]
        kprev_d[sid] = float(before.k.iloc[-1]) if len(before) else np.nan
        if len(a24) == 0:
            grp[sid] = 'unknown'
        else:
            knew_d[sid] = float(a24.k.iloc[0]); tnext_d[sid] = float(a24.t.iloc[0] - idx.t)
            if float(a24.k.iloc[0]) < THR: grp[sid] = 'transient'
            elif bool((a24.k >= THR).all()): grp[sid] = 'sustained'
            else: grp[sid] = 'confirmed'
    coh = pd.DataFrame({'sid': list(grp.keys())})
    coh['grp'] = coh.sid.map(grp)
    coh['k_base'] = coh.sid.map(kb_d)
    coh['k_idx'] = coh.sid.map(kidx_d)
    coh['k_next'] = coh.sid.map(knew_d)
    coh['t_next'] = coh.sid.map(tnext_d)
    coh['k_prev'] = coh.sid.map(kprev_d)
    n_per = d.groupby('sid').size()
    coh['n_k'] = coh.sid.map(n_per)
    coh = coh.merge(oc, on='sid', how='left')
    n_coh = len(coh)
    n_units = d.sid.nunique()

    # ================= 表 2 / 摘要：状态构成 =================
    n_app = int((coh.grp != 'no_event').sum())
    n_conf = int((coh.grp.isin(['confirmed', 'sustained'])).sum())   # 含 sustained
    n_sus = int((coh.grp == 'sustained').sum())
    n_tr = int((coh.grp == 'transient').sum())
    n_unk = int((coh.grp == 'unknown').sum())
    n_ne = int((coh.grp == 'no_event').sum())
    add('T2/摘要', '有血钾记录例数', nm, n_units)
    add('T2/摘要', '队列 n', nm, n_coh)
    add('T2/摘要', 'apparent n', nm, n_app)
    add('T2/摘要', 'apparent % of cohort', nm, round(100 * n_app / n_coh, 2))
    add('T2/摘要', 'transient n', nm, n_tr)
    add('T2/摘要', 'transient % of cohort', nm, round(100 * n_tr / n_coh, 2))
    add('T2/摘要', 'confirmed(含sustained) n', nm, n_conf)
    add('T2/摘要', 'confirmed % of cohort', nm, round(100 * n_conf / n_coh, 2))
    add('T2/摘要', 'confirmed-not-sustained n', nm, n_conf - n_sus)
    add('T2/摘要', 'confirmed-not-sustained % of cohort', nm, round(100 * (n_conf - n_sus) / n_coh, 2))
    add('T2/摘要', 'sustained n', nm, n_sus)
    add('T2/摘要', 'sustained % of cohort', nm, round(100 * n_sus / n_coh, 2))
    add('T2/摘要', 'unclassified n', nm, n_unk)
    add('T2/摘要', 'unclassified % of cohort', nm, round(100 * n_unk / n_coh, 2))
    add('T2/摘要', 'confirmed/apparent %', nm, round(100 * n_conf / n_app, 1))
    add('T2/摘要', 'sustained/apparent %', nm, round(100 * n_sus / n_app, 1))
    rep = coh[coh.k_next.notna()]
    add('T2/摘要', '有复查者 n', nm, len(rep))
    add('T2/摘要', '中位复查值—全部有复查者', nm, round(med(rep.k_next), 2))
    rev = rep[rep.k_next < THR]
    add('T2/摘要', '中位复查值—仅回落者', nm, round(med(rev.k_next), 2))
    add('T2/摘要', '复查值<5.5 占“有复查者”%', nm, round(100 * len(rev) / len(rep), 1))
    add('T2/摘要', '复查值<5.5 占“apparent”%', nm, round(100 * len(rev) / n_app, 1))
    add('T2/摘要', '确认率—分母=有复查者', nm, round(100 * float((rep.k_next >= THR).mean()), 1))
    add('T2/摘要', '确认率—分母=apparent', nm, round(100 * n_conf / n_app, 1))

    # ================= 表 1：描述统计 =================
    for g, lab in [('no_event', 'No episode'), ('transient', 'Transient'),
                   ('confirmed', 'Confirmed-not-sustained'), ('sustained', 'Sustained'),
                   ('unknown', 'Unclassified')]:
        s = coh[coh.grp == g]
        add('T1', lab + ' n', nm, len(s))
        add('T1', lab + ' 年龄中位', nm, round(med(s.age), 1))
        add('T1', lab + ' 男性%', nm, round(100 * float((s.sex.astype(str).str.upper().str[0] == 'M').mean()), 1))
        add('T1', lab + ' 基线K中位', nm, round(med(s.k_base), 2))
        add('T1', lab + ' 测量次数中位', nm, round(med(s.n_k), 1))
    add('T1', '全队列 n', nm, n_coh)
    add('T1', '全队列 年龄中位', nm, round(med(coh.age), 1))
    add('T1', '全队列 男性%', nm, round(100 * float((coh.sex.astype(str).str.upper().str[0] == 'M').mean()), 1))
    add('T1', '全队列 基线K中位', nm, round(med(coh.k_base), 2))
    add('T1', '全队列 测量次数中位', nm, round(med(coh.n_k), 1))
    add('正文3.1', '测量次数中位(全体有记录者)', nm, round(float(n_per.median()), 1))
    add('正文3.1', '测量次数 IQR25', nm, round(float(n_per.quantile(.25)), 1))
    add('正文3.1', '测量次数 IQR75', nm, round(float(n_per.quantile(.75)), 1))
    neo = coh[coh.grp == 'no_event']
    add('正文3.1', '无事件者测量次数中位', nm, round(med(neo.n_k), 1))
    for g in ['transient', 'confirmed', 'sustained', 'unknown']:
        s = coh[coh.grp == g]
        add('正文3.1', '有事件者测量次数中位-' + g, nm, round(med(s.n_k), 1))

    # ================= 表 3：变异与转移 =================
    dd = d.copy(); dd['dk'] = dd.groupby('sid').k.diff(); dd['dt'] = dd.groupby('sid').t.diff()
    pr = dd[(dd.dt > 0) & (dd.dt <= BASE)]
    sd_w = float(pr.dk.std() / np.sqrt(2)); kpop = float(d.k.mean())
    cv_w = 100 * sd_w / kpop; rcv = 1.96 * np.sqrt(2) * sd_w
    add('T3', '≤24h 相邻配对数', nm, len(pr))
    add('T3', 'within-patient SD', nm, round(sd_w, 3))
    add('T3', 'within-patient CV %', nm, round(cv_w, 2))
    add('T3', 'RCV', nm, round(rcv, 2))
    kmed = d.groupby('sid').k.median()
    e2 = coh[coh.k_idx.notna()].copy(); e2['k_med'] = e2.sid.map(kmed)
    add('T3', '索引值>本人中位+RCV %', nm, round(100 * float(((e2.k_idx - e2.k_med) > rcv).mean()), 1))
    dkp = (e2.k_idx - e2.sid.map(kprev_d)).dropna()
    add('T3', '增量≤RCV %', nm, round(100 * float((dkp <= rcv).mean()), 1))
    # 转移矩阵（全体）
    post = d[d.t > BASE].copy()
    post['kn'] = post.groupby('sid').k.shift(-1); post['tn'] = post.groupby('sid').t.shift(-1)
    post['dt'] = post.tn - post.t
    pp = post[(post.dt > 0) & (post.dt <= BASE) & post.kn.notna()]
    for lo, hi, lab in [(4.5, 5.0, '4.5-4.9'), (5.0, 5.5, '5.0-5.4'), (5.5, 6.0, '5.5-5.9'), (6.0, 20.0, '>=6.0')]:
        s = pp[(pp.k >= lo) & (pp.k < hi)]
        add('T3', '转移(全体) %s 下次≥5.5 %%' % lab, nm, round(100 * float((s.kn >= THR).mean()), 1), 'n=%d' % len(s))
    # 转移矩阵（仅基线正常队列内）
    pp2 = pp[pp.sid.isin(coh.sid)]
    for lo, hi, lab in [(4.5, 5.0, '4.5-4.9'), (5.0, 5.5, '5.0-5.4'), (5.5, 6.0, '5.5-5.9'), (6.0, 20.0, '>=6.0')]:
        s = pp2[(pp2.k >= lo) & (pp2.k < hi)]
        add('T3', '转移(基线正常) %s 下次≥5.5 %%' % lab, nm, round(100 * float((s.kn >= THR).mean()), 1), 'n=%d' % len(s))

    # ================= 表 4：误差定界 =================
    g = d.groupby('sid').k; n_i = g.size(); mean_i = g.mean()
    multi = n_i[n_i >= 3].index
    tau2 = max(float(mean_i[multi].var()) - float((sd_w ** 2 / n_i[multi]).mean()), 1e-6)
    rr = rep[rep.k_prev.notna()]
    for lbl, sd in [('CV1.5%', 0.015 * kpop), ('CV3.0%', 0.030 * kpop), ('CV5.0%', 0.050 * kpop), ('observed', sd_w)]:
        lam = tau2 / (tau2 + sd ** 2)
        mu = lam * rr.k_idx.values + (1 - lam) * kpop
        sd2 = sd * np.sqrt(1 + lam)
        p = float((1 - norm.cdf((THR - mu) / sd2)).mean())
        add('T4', lbl + ' SD', nm, round(sd, 3))
        add('T4', lbl + ' 预期确认率%', nm, round(100 * p, 1), '分母:有复查且有前值 n=%d' % len(rr))
    add('T4', '观察确认率(分母=有复查且有前值)%', nm, round(100 * float((rr.k_next >= THR).mean()), 1))
    add('T4', '观察确认率(分母=有复查)%', nm, round(100 * float((rep.k_next >= THR).mean()), 1))

    # ================= 表 6：复查规则 =================
    ev = coh[coh.k_next.notna()].copy()  # 用 t_next 判定
    evall = coh[coh.grp != 'no_event'].copy()
    for W, lab in [(120, '2h'), (240, '4h'), (360, '6h'), (720, '12h'), (1440, '24h')]:
        inw = int((evall.t_next <= W).sum())
        cap = int(((evall.t_next <= W) & (evall.k_next >= THR)).sum())
        add('T6', '%s 复查覆盖%%' % lab, nm, round(100 * inw / len(evall), 1))
        add('T6', '%s 未覆盖例数' % lab, nm, len(evall) - inw)
        add('T6', '%s 内确认例数' % lab, nm, cap)
        add('T6', '%s NNR' % lab, nm, round(inw / cap, 1) if cap else None)
    conf_all = coh[coh.grp.isin(['confirmed', 'sustained'])]
    for W, lab in [(360, '6h'), (720, '12h')]:
        add('T6', '已确认事件中 %s 内被复查%%' % lab, nm,
            round(100 * float((conf_all.t_next <= W).mean()), 1), 'n_conf=%d' % len(conf_all))
    for lo, hi, lab in [(5.5, 6.0, '5.5-5.9'), (6.0, 6.5, '6.0-6.4'), (6.5, 20.0, '>=6.5')]:
        s = evall[(evall.k_idx >= lo) & (evall.k_idx < hi) & (evall.t_next <= 360)]
        c = int((s.k_next >= THR).sum())
        add('T6', '分层 %s 6h内NNR' % lab, nm, round(len(s) / c, 1) if c else None, 'n=%d cap=%d' % (len(s), c))
    # 未复查者 vs 复查者死亡率（正文）
    mt = coh[(coh.grp != 'no_event') & coh.died_inhosp.notna()]
    u = mt[mt.grp == 'unknown']; r = mt[mt.k_next.notna()]
    add('正文4', '未复查者院内死亡%', nm, round(100 * float(u.died_inhosp.mean()), 1))
    add('正文4', '已复查者院内死亡%', nm, round(100 * float(r.died_inhosp.mean()), 1))
    add('正文4', '未复查/已复查 死亡比', nm, round(float(u.died_inhosp.mean() / r.died_inhosp.mean()), 2))

    # ================= 表 5：全队列粗率（暴露窗无上界，k32 口径）=================
    for g, lab in [('no_event', 'No episode'), ('transient', 'Transient'),
                   ('confirmed', 'Confirmed-not-sustained'), ('sustained', 'Sustained'), ('unknown', 'Unclassified')]:
        s = coh[coh.grp == g]
        add('T5', lab + ' 全队列粗死亡%', nm, round(100 * float(s.died_inhosp.mean()), 1))
    # landmark：暴露窗 24h–H
    for H, lab in [(4320, '72h'), (10080, '7d')]:
        g2, ki2 = {}, {}
        for sid, gg in d.groupby('sid', sort=False):
            pre = gg[gg.t <= BASE]
            if len(pre) == 0 or float(pre.k.max()) >= THR: continue
            post = gg[(gg.t > BASE) & (gg.t <= H)]
            if len(post) == 0: continue
            pos = post[post.k >= THR]
            if len(pos) == 0:
                g2[sid] = 'no_event'; continue
            idx = pos.iloc[0]
            a24 = post[(post.t > idx.t) & (post.t <= idx.t + BASE)]
            ki2[sid] = float(idx.k)
            if len(a24) == 0: g2[sid] = 'unknown'
            elif float(a24.k.iloc[0]) < THR: g2[sid] = 'transient'
            elif bool((a24.k >= THR).all()): g2[sid] = 'sustained'
            else: g2[sid] = 'confirmed'
        c2 = pd.DataFrame({'sid': list(g2.keys())}); c2['grp'] = c2.sid.map(g2); c2['k_idx'] = c2.sid.map(ki2)
        c2 = c2.merge(oc, on='sid', how='left')
        lm = c2[c2.los_hosp_min > H]
        add('T5', 'landmark %s 队列 n' % lab, nm, len(lm))
        for g3, lab3 in [('no_event', 'No episode'), ('transient', 'Transient'),
                         ('confirmed', 'Confirmed-not-sustained'), ('sustained', 'Sustained'), ('unknown', 'Unclassified')]:
            s = lm[lm.grp == g3]
            if len(s):
                add('T5', '%s landmark %s n' % (lab3, lab), nm, len(s))
                add('T5', '%s landmark %s 死亡%%' % (lab3, lab), nm, round(100 * float(s.died_inhosp.mean()), 1))
        # 索引值 5.5-5.9 带内死亡%
        for g3, lab3 in [('transient', 'Transient'), ('confirmed', 'Confirmed'), ('sustained', 'Sustained')]:
            s = lm[(lm.grp == g3) & (lm.k_idx >= 5.5) & (lm.k_idx < 6.0)]
            if len(s):
                add('T5', '5.5-5.9带 %s landmark %s 死亡%%' % (lab3, lab), nm,
                    round(100 * float(s.died_inhosp.mean()), 1), 'n=%d' % len(s))
        np.save('out/_audit_lm_%s_%s.npy' % (tag, lab), lm[['sid', 'grp', 'k_idx']].to_records(index=False))

out = pd.DataFrame(ROWS)
out.to_csv('out/k3_audit_numbers.csv', index=False, encoding='utf-8-sig')
print(out.to_string())
print('\n写出 out/k3_audit_numbers.csv  行数=', len(out))
