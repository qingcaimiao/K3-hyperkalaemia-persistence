# -*- coding: utf-8 -*-
"""k69: shorten the abstract, add the Figure 1B citation, rename the Methods heading,
and correct the Figure 4 caption to explain the new right-hand column.

Every replacement is anchored uniquely and asserted; word counts are printed so the
abstract length is verified by script rather than by eye.
"""
import io, re, sys

EN = 'out/manuscript_K3.md'
CN = 'out/稿件_K3_中文版.md'

EN_ABS = """**Background** Hyperkalaemia in cardiac intensive care is defined by one threshold, although guidelines advise a repeat sample. Whether such an episode persists, and whether persistence is prognostic, is unknown.

**Methods** Among cardiac intensive care admissions with potassium records in the Medical Information Mart for Intensive Care IV (MIMIC-IV) and the eICU Collaborative Research Database (eICU-CRD), the 20,322 and 28,805 with a baseline potassium below 5.5 mmol/L and a measurement after 24 hours were classified by the next 24 hours after a first value ≥5.5 mmol/L as transient, intermittent, sustained or unclassified, and related to in-hospital death after a 72-hour landmark.

**Results** Episodes occurred in 1,182 (5.82%) and 997 (3.46%) admissions; 86 (0.42%) and 100 (0.35%) were sustained. Analytical error alone predicted 38–83% confirmation, so the observed reversion reflects genuine fluctuation, not assay error, and recorded treatment did not explain it. Adjusted odds ratios for death for sustained episodes were 11.87 (5.59–20.49) and 8.05 (4.16–15.15), significant in all sensitivity analyses; only 52.0% and 42.0% were re-measured within six hours.

**Conclusions** Most single-threshold episodes in cardiac intensive care do not persist, and the observed rates exclude an isolated assay error. Excess mortality is carried mainly by the persistent state, so the two should be reported separately."""

CN_ABS = """**背景** 心脏重症监护中的高钾血症以单次阈值确定，尽管指南建议复查确认。这样一次事件有多常持续、持续是否携带预后信息，均不清楚。

**方法** 在 MIMIC-IV（Medical Information Mart for Intensive Care IV）与 eICU 协作研究数据库（eICU-CRD）中有血钾记录的心脏重症监护住院里，基线血钾 <5.5 mmol/L 且在 24 小时后有测量的 20,322 与 28,805 例，依据首次 ≥5.5 mmol/L 之后 24 小时内的测量分为一过性、间歇、持续与未分类，并把各状态与 72 小时 landmark 之后的院内死亡关联。

**结果** 事件分别发生于 1,182 例（5.82%）与 997 例（3.46%）；86 例（0.42%）与 100 例（0.35%）为持续。若纯为分析误差，预期确认率应为 38–83%，故观察到的回落更符合真实波动而非测定误差，记录到的治疗亦不能解释。校正后死亡比值比在持续事件为 11.87（5.59–20.49）与 8.05（4.16–15.15），在每一项敏感性分析中均保持显著；仅 52.0% 与 42.0% 的事件在 6 小时内被复查。

**结论** 心脏重症监护中以单次阈值定义的事件多数并不持续，观察到的比例已可排除单纯的测定误差。超额死亡主要由持续状态承载，因此两者应当分别报告。"""

en = io.open(EN, encoding='utf-8').read()
cn = io.open(CN, encoding='utf-8').read()
fails = []


def swap(txt, old, new, tag, count=1):
    n = txt.count(old)
    if n != count:
        fails.append('%s: found %d (expected %d)' % (tag, n, count)); return txt
    return txt.replace(old, new, count)


# ---- 1. abstract (EN + CN) ------------------------------------------------
def replace_abstract(txt, head, tail, new):
    a = txt.index(head) + len(head)
    b = txt.index(tail, a)
    return txt[:a] + '\n\n' + new + '\n\n' + txt[b:]


i0, i1 = en.index('## Abstract') + len('## Abstract'), en.index('**Keywords**')
old_abs = en[i0:i1]
en = replace_abstract(en, '## Abstract', '**Keywords**', EN_ABS)
cn = replace_abstract(cn, '## 摘要', '**关键词**', CN_ABS)

core = re.sub(r'\*\*(Background|Methods|Results|Conclusions)\*\*', '', EN_ABS)
n_core = len(core.split())
n_all = len(EN_ABS.split())
print('EN abstract: core %d words | with the four labels %d words' % (n_core, n_all))
if n_core > 200:
    fails.append('abstract still %d words (>200)' % n_core)

# ---- 2. cite Figure 1B where the incidences are reported -------------------
en = swap(en, 'and 997 of 28,805 in eICU-CRD (3.46%, 3.25\u20133.68) (Table 2).',
          'and 997 of 28,805 in eICU-CRD (3.46%, 3.25\u20133.68) (Table 2, Figure 1B).', 'EN Figure 1B cite')
cn = swap(cn, '\uff083.46%\uff0c3.25\u20133.68\uff09\uff08\u8868 2\uff09\u3002',
          '(3.46%\uff0c3.25\u20133.68)\uff08\u8868 2\u3001\u56fe 1B\uff09\u3002', 'CN 图 1B 引用')

# ---- 3. section heading ----------------------------------------------------
en = swap(en, '## 2. Methods', '## 2. Materials and Methods', 'EN heading')
cn = swap(cn, '## 2. \u65b9\u6cd5', '## 2. \u6750\u6599\u4e0e\u65b9\u6cd5', 'CN heading')

# ---- 4. Figure 4 caption ---------------------------------------------------
en = swap(en, 'Cell values are rounded to the nearest integer; the collapsed probability that the next value is at least 5.5 mmol/L is given exactly in Table 3.',
          'Cell values are rounded to the nearest integer. The right-hand column gives, for each current band, the exact row percentage whose next value is at least 5.5 mmol/L, the collapsed probability quoted in Table 3; because the cells are rounded individually, their sum may differ from it by up to one percentage point.',
          'EN Fig4 caption')
cn_new = ('\u683c\u5185\u6570\u503c\u56db\u820d\u4e94\u5165\u81f3\u6574\u6570\u3002'
          '\u53f3\u7f18\u4e00\u5217\u7ed9\u51fa\u5404\u5f53\u524d\u533a\u95f4\u201c\u4e0b\u4e00\u6b21 \u22655.5 mmol/L\u201d\u7684\u884c\u767e\u5206\u6bd4\u7cbe\u786e\u503c\uff0c'
          '\u5373\u8868 3 \u6240\u5217\u7684\u5408\u5e76\u6982\u7387\uff1b\u7531\u4e8e\u5404\u683c\u5355\u72ec\u53d6\u6574\uff0c\u4e24\u683c\u4e4b\u548c\u4e0e\u5b83\u6700\u591a\u53ef\u5dee 1 \u4e2a\u767e\u5206\u70b9\u3002')
cn = re.sub(r'\u683c\u5185\u6570\u503c\u56db\u820d\u4e94\u5165\u81f3\u6574\u6570\uff1b.*?\u5217\u4e8e\u8868 3\u3002', cn_new, cn, count=1)

if fails:
    print('ABORT:'); [print('  -', f) for f in fails]; sys.exit(1)

io.open(EN, 'w', encoding='utf-8').write(en)
io.open(CN, 'w', encoding='utf-8').write(cn)

print('\nEN abstract (old %d words -> new %d words)' % (len(re.sub(r'\*\*(Background|Methods|Results|Conclusions)\*\*', '', old_abs).split()), n_core))
print('done: abstract, Figure 1B citation, heading, Figure 4 caption')
