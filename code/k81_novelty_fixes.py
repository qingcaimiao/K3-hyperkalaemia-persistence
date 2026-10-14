# -*- coding: utf-8 -*-
"""k81: novelty-driven manuscript fixes.

1. The closest title-level neighbour found by the three-track search
   (Trevisan 2022, Clin Kidney J — transient vs chronic hyperkalaemia in CKD) is
   now cited and explicitly differentiated, both in the Introduction and in the
   Discussion.  Adding it as reference 17 shifts the three references that follow
   it, so the renumbering is done in ONE pass (17->18, 18->19, 19->20) to avoid
   cascading.
2. The claim "odds ratios were between about 4 and 15" did not match the source
   files: at the 72-hour landmark the persistent state's adjusted ORs across the
   reported specifications run from 4.94 to 20.17 (recomputed from out/*.json),
   so the sentence is corrected to "about 5 to 20".
3. Reference 7 pointed at a bare domain and at the superseded 2020 guideline;
   it now cites the current UK Kidney Association guideline (October 2023) at its
   verified URL.
"""
import io, re, sys

EN = 'out/manuscript_K3.md'
CN = 'out/稿件_K3_中文版.md'
fails = []

NEW_REF = ('17. Trevisan, M.; Clase, C. M.; Evans, M.; Popov, T.; Ludvigsson, J. F.; '
           'Sjölander, A.; Carrero, J. J. Patterns of Chronic and Transient Hyperkalaemia and '
           'Clinically Important Outcomes in Patients with Chronic Kidney Disease. '
           '*Clin. Kidney J.* 2022, 15, 153-161. https://doi.org/10.1093/ckj/sfab159')

OLD_REF7 = ('7. UK Kidney Association. Clinical Practice Guideline: Treatment of Acute '
            'Hyperkalaemia in Adults. Available online: https://ukkidney.org '
            '(accessed on 13 October 2026).')
NEW_REF7 = ('7. UK Kidney Association. UK Kidney Association Clinical Practice Guideline: '
            'Treatment of Acute Hyperkalaemia in Adults. 2023. Available online: '
            'https://guidelines.ukkidney.org/hyperkalaemia (accessed on 14 October 2026).')


def bump_citations(s):
    """One pass: every citation number >= 17 becomes n+1."""
    hit = []

    def f(m):
        nums = [int(x) for x in re.findall(r'\d+', m.group(1))]
        out = [n + 1 if n >= 17 else n for n in nums]
        hit.extend(n for n in nums if n >= 17)
        return '[' + ','.join(str(x) for x in out) + ']'

    s2 = re.sub(r'\[(\d+(?:\s*,\s*\d+)*)\]', f, s)
    return s2, hit


def bump_reflist(s):
    hit = []

    def f(m):
        hit.append(int(m.group(1)))
        return '%d. ' % (int(m.group(1)) + 1)

    s2 = re.sub(r'(?m)^(1[7-9])\. ', f, s)
    return s2, hit


for path, intr_before, disc_after, three_strands_old, three_strands_new, or_old, or_new, ins_intro, ins_disc in [
    (EN,
     'We therefore set out to define what a threshold-defined episode consists of in cardiac intensive care,',
     'while, importantly, the transient episodes that are removed are not low-risk episodes.',
     'Three strands of work come close without addressing it.',
     'Several strands of work come close without addressing it.',
     'Odds ratios were between about 4 and 15, with E-values of 15.5 and 10.6.',
     'The adjusted odds ratio for the persistent state ranged from about 5 to 20 at the '
     '72-hour landmark, with E-values of 15.5 and 10.6.',
     'Trajectories have also been separated into *transient* and *chronic* hyperkalaemia in chronic '
     'kidney disease, where the transient pattern predicted death more strongly over a 12-month '
     'horizon [17]; that formulation describes the burden of hyperkalaemia over a year in '
     'outpatients rather than what becomes of a single episode over the next day. ',
     ' Over a longer horizon the ordering can reverse: in chronic kidney disease followed for a '
     'year, it was the *transient* pattern of hyperkalaemia that predicted death more strongly '
     'than the chronic one [17], which suggests that what is being captured there is instability '
     'of control rather than the fate of a single episode.'),
    (CN,
     '因此本研究旨在界定心脏重症监护中一次阈值定义事件由什么构成',
     '**而被剔除的一过性事件并非低风险事件**。',
     '已有三条工作线索接近这一问题但都未触及它。',
     '已有若干工作线索接近这一问题但都未触及它。',
     '比值比约在 4–15 之间，E 值为 15.5 与 10.6。',
     '在 72 小时 landmark 下，持续性状态的校正比值比约为 5–20，E 值为 15.5 与 10.6。',
     '慢性肾脏病中亦有研究把血钾轨迹分为**一过性**与**慢性**两种模式，发现 12 个月尺度上一过性'
     '模式对死亡的预测更强[17]；但该框架描述的是门诊患者一年内的血钾负荷，而非单个事件在随后一天中的转归。',
     '在更长的观察尺度上次序可能反转：在随访一年的慢性肾脏病患者中，预测死亡更强的是**一过性**'
     '模式而非慢性模式[17]，这提示那里被捕捉到的是控制的不稳定性，而不是单个事件的转归。'),
]:
    s = io.open(path, encoding='utf-8').read()

    # --- 1) renumber (single pass) -------------------------------------------------
    s, hits_c = bump_citations(s)
    s, hits_l = bump_reflist(s)
    print('%-28s 正文引用重编号 %s | 文献表 %s' % (path, sorted(set(hits_c)), sorted(set(hits_l))))
    if sorted(set(hits_l)) != [17, 18, 19]:
        fails.append('%s 文献表重编号异常' % path)

    # --- 2) insert the new reference as No. 17 ------------------------------------
    anchor = '\n18. Johnson, A. E. W.;'
    if s.count(anchor) != 1:
        fails.append('%s: 找不到 18. Johnson 锚点 (%d)' % (path, s.count(anchor)))
    else:
        s = s.replace(anchor, '\n' + NEW_REF + '\n18. Johnson, A. E. W.;', 1)

    # --- 3) reference 7 ------------------------------------------------------------
    if s.count(OLD_REF7) != 1:
        fails.append('%s: ref7 锚点 %d' % (path, s.count(OLD_REF7)))
    else:
        s = s.replace(OLD_REF7, NEW_REF7, 1)

    # --- 4) OR range claim ---------------------------------------------------------
    if s.count(or_old) != 1:
        fails.append('%s: OR 句锚点 %d' % (path, s.count(or_old)))
    else:
        s = s.replace(or_old, or_new, 1)

    # --- 5) "three strands" -> "several strands" -----------------------------------
    if s.count(three_strands_old) != 1:
        fails.append('%s: 三条线索锚点 %d' % (path, s.count(three_strands_old)))
    else:
        s = s.replace(three_strands_old, three_strands_new, 1)

    # --- 6) new strand in the Introduction ----------------------------------------
    if s.count(intr_before) != 1:
        fails.append('%s: 引言插入锚点 %d' % (path, s.count(intr_before)))
    else:
        s = s.replace(intr_before, ins_intro + intr_before, 1)

    # --- 7) contrast sentence in the Discussion -----------------------------------
    if s.count(disc_after) != 1:
        fails.append('%s: 讨论插入锚点 %d' % (path, s.count(disc_after)))
    else:
        s = s.replace(disc_after, disc_after + ins_disc, 1)

    io.open(path, 'w', encoding='utf-8').write(s)
    print('  -> 写入完成\n')

if fails:
    print('ABORT:'); [print('  -', f) for f in fails]; sys.exit(1)

# ------------------------------------------------------------------ verification
print('=== 复核 ===')
for path in (EN, CN):
    s = io.open(path, encoding='utf-8').read()
    body = s[s.index('## 1.'):s.index('## References') if path == EN else s.index('## 参考文献')]
    order, seen = [], set()
    for m in re.finditer(r'\[(\d+(?:\s*,\s*\d+)*)\]', body):
        for x in re.findall(r'\d+', m.group(1)):
            n = int(x)
            if n not in seen:
                seen.add(n); order.append(n)
    reflist = [int(x) for x in re.findall(r'(?m)^(\d{1,2})\. ', s[s.index('## 19.'[:0] + ('## References' if path == EN else '## 参考文献')):])]
    print('%-28s 引用首次出现顺序递增: %s | 顺序 %s' % (path, order == sorted(order), order))
    print('%-28s 参考文献编号: %s' % ('', reflist))
    print('%-28s Trevisan 存在: %s | 新指南 URL 存在: %s | OR 句已改: %s'
          % ('', 'Trevisan' in s, 'guidelines.ukkidney.org/hyperkalaemia' in s,
             'between about 5 and 20' in s or '约为 5–20' in s))
