# -*- coding: utf-8 -*-
"""k71: corrections arising from the external (DeepSeek) review, applied only where the
claim was confirmed against the docx/md source.

Confirmed and fixed:
  * Figure 3 caption did not describe the third panel (source of variation / expected
    confirmation) -> caption rewritten for both languages;
  * the Abbreviations list carried AUC, which never appears in the text, and omitted
    abbreviations that are used (CCU, CV, CVICU, E-value, IQR, RR, SD) -> list rebuilt
    from an actual scan of the body;
  * the abstract is brought back up to about 230 words, restoring the transient-state
    odds ratios, the cohort sizes and the analytical-error sentence (journal budget for
    original research is ~250 words);
  * the E-value sentence now points to Table S9.

Not changed (claims refuted against the source; see the audit report):
  * "Introduction duplicated on page 2" - no duplicated paragraph exists in the md or
    the docx;
  * "author block missing from the first page" - the title page carries all five
    authors, three affiliations, correspondence, ORCIDs and e-mail addresses;
  * supplementary numbering - Table S1-S9 all exist and match the in-text citations.
"""
import io, re, sys

EN = 'out/manuscript_K3.md'
CN = 'out/稿件_K3_中文版.md'
fails = []

EN_ABS = """**Background** Hyperkalaemia in cardiac intensive care is defined by one threshold, although guidelines advise a repeat sample. Whether such an episode persists, and whether persistence is prognostic, is unknown.

**Methods** Among cardiac intensive care admissions with potassium records in the Medical Information Mart for Intensive Care IV (MIMIC-IV, 23,429) and the eICU Collaborative Research Database (eICU-CRD, 41,917), the 20,322 and 28,805 with a baseline potassium below 5.5 mmol/L and a measurement after 24 hours were classified by the next 24 hours after a first value ≥5.5 mmol/L as transient, intermittent, sustained or unclassified. We quantified within-patient variability, bounded the contribution of analytical error, and related each state to in-hospital death after a 72-hour landmark.

**Results** Episodes occurred in 1,182 (5.82%) and 997 (3.46%) admissions; 86 (0.42%) and 100 (0.35%) were sustained. Analytical error alone predicted 38–83% confirmation, so the reversion reflects genuine fluctuation, not assay error, and recorded treatment did not explain it. Adjusted odds ratios for death were 11.87 (5.59–20.49) and 8.05 (4.16–15.15) for sustained episodes and 1.56 (0.99–2.45) and 2.77 (1.82–3.93) for transient episodes; the persistent state was significant in all sensitivity analyses, whereas the excess for transient episodes was not significant in MIMIC-IV. Only 52.0% and 42.0% were re-measured within six hours.

**Conclusions** Most single-threshold episodes in cardiac intensive care do not persist, and the observed rates exclude an isolated assay error. Excess mortality is carried mainly by the persistent state, so the two should be reported separately."""

CN_ABS = """**背景** 心脏重症监护中的高钾血症以单次阈值确定，尽管指南建议复查确认。这样一次事件有多常持续、持续是否携带预后信息，均不清楚。

**方法** 在 MIMIC-IV（Medical Information Mart for Intensive Care IV，23,429 例）与 eICU 协作研究数据库（eICU-CRD，41,917 例）中有血钾记录的心脏重症监护住院里，基线血钾 <5.5 mmol/L 且在 24 小时后有测量的 20,322 与 28,805 例，依据首次 ≥5.5 mmol/L 之后 24 小时内的测量分为一过性、间歇、持续与未分类。我们量化患者内变异、界定分析误差的贡献，并把各状态与 72 小时 landmark 之后的院内死亡关联。

**结果** 事件分别发生于 1,182 例（5.82%）与 997 例（3.46%）；86 例（0.42%）与 100 例（0.35%）为持续。若纯为分析误差，预期确认率应为 38–83%，故回落更符合真实波动而非测定误差，记录到的治疗亦不能解释。校正后死亡比值比在持续事件为 11.87（5.59–20.49）与 8.05（4.16–15.15），在一过性事件为 1.56（0.99–2.45）与 2.77（1.82–3.93）；持续状态在全部敏感性分析中均保持显著，而一过性事件的超额风险在 MIMIC-IV 中未达显著。仅 52.0% 与 42.0% 的事件在 6 小时内被复查。

**结论** 心脏重症监护中以单次阈值定义的事件多数并不持续，观察到的比例已可排除单纯的测定误差。超额死亡主要由持续状态承载，因此两者应当分别报告。"""

EN_ABB = """| Abbreviation | Definition |
|---|---|
| CCU | coronary care unit |
| CI | confidence interval |
| CV | coefficient of variation |
| CVICU | cardiac vascular intensive care unit |
| E-value | minimum strength of association that an unmeasured confounder would need in order to explain away an observed association |
| eICU-CRD | eICU Collaborative Research Database |
| IQR | interquartile range |
| MIMIC-IV | Medical Information Mart for Intensive Care IV |
| OR | odds ratio |
| RCV | reference change value |
| RR | risk ratio |
| SD | standard deviation |
| STROBE | Strengthening the Reporting of Observational Studies in Epidemiology |"""

CN_ABB = """| 缩写 | 全称 |
|---|---|
| CCU | 冠心病监护病房 |
| CI | 置信区间 |
| CV | 变异系数 |
| CVICU | 心血管重症监护病房 |
| E 值 | 解释掉某一观察到的关联所需的最小未测混杂关联强度 |
| eICU-CRD | eICU 协作研究数据库 |
| IQR | 四分位距 |
| MIMIC-IV | 重症监护医学信息库 IV |
| OR | 比值比 |
| RCV | 参考变化值 |
| RR | 风险比 |
| SD | 标准差 |
| STROBE | 加强观察性流行病学研究报告声明 |"""

en = io.open(EN, encoding='utf-8').read()
cn = io.open(CN, encoding='utf-8').read()


def swap(txt, old, new, tag):
    n = txt.count(old)
    if n != 1:
        fails.append('%s: matched %d' % (tag, n)); return txt
    return txt.replace(old, new, 1)


def swap_re(txt, pat, new, tag):
    n = len(re.findall(pat, txt))
    if n != 1:
        fails.append('%s: matched %d' % (tag, n)); return txt
    return re.sub(pat, new.replace('\\', '\\\\'), txt, count=1)


# ---- 1. abstract (restore ~30 words) --------------------------------------
a = en.index('## Abstract') + len('## Abstract'); b = en.index('**Keywords**', a)
old_core = re.sub(r'\*\*(Background|Methods|Results|Conclusions)\*\*', '', en[a:b]).split()
en = en[:a] + '\n\n' + EN_ABS + '\n\n' + en[b:]
a2 = cn.index('## 摘要') + len('## 摘要'); b2 = cn.index('**关键词**', a2)
cn = cn[:a2] + '\n\n' + CN_ABS + '\n\n' + cn[b2:]
new_core = len(re.sub(r'\*\*(Background|Methods|Results|Conclusions)\*\*', '', EN_ABS).split())
print('abstract: %d -> %d words (core, labels excluded)' % (len(old_core), new_core))

# ---- 2. Figure 3 captions -------------------------------------------------
en = swap(en, "**Figure 3.** Within-patient variability and its consequences. Distribution of the difference between consecutive measurements within 24 hours, the 95% reference change value, and the proportion of index values exceeding the patient's own variability.",
          "**Figure 3.** Within-patient variability and the explanations for reversion. The two left panels show the distribution of the difference between consecutive potassium measurements up to 24 hours apart, in MIMIC-IV and eICU-CRD; the dashed lines mark the 95% reference change value and the inset gives the within-patient standard deviation, its coefficient of variation and the reference change value. The right panel gives the expected confirmation rate under each assumed source of variation (analytical imprecision at a coefficient of variation of 1.5%, 3.0% and 5.0%, and the observed within-patient variability) beside the observed rate; the same quantities are tabulated in Table 4.",
          'EN Fig3 caption')
cn = swap(cn, "**图 3.** 患者内变异及其后果。24 小时内相邻测量差值分布、95% 参考变化值，以及索引值超过患者自身变异范围的比例。",
          "**图 3.** 患者内变异与回落的可能解释。左侧两幅为 MIMIC-IV 与 eICU-CRD 中间隔 ≤24 小时的相邻血钾测量差值的分布；虚线为 95% 参考变化值，插图给出患者内标准差、变异系数与参考变化值。右侧一幅给出各假设变异来源下（分析不精密度 CV 1.5%、3.0%、5.0%，以及观察到的患者内变异）的预期确认率，并与实际观察到的确认率并列；同一批数值列于表 4。",
          'CN 图3 caption')

# ---- 3. abbreviations -----------------------------------------------------
en = swap_re(en, r'\| Abbreviation \| Definition \|\n\|---\|---\|\n(\|[^\n]*\|\n)+', EN_ABB, 'EN abbreviations')
cn = swap_re(cn, r'\| 缩写 \| 全称 \|\n\|---\|---\|\n(\|[^\n]*\|\n)+', CN_ABB, 'CN abbreviations')

# ---- 4. Table S9 pointer -------------------------------------------------
en = swap(en, 'the E-value for the persistent state was 15.5 and 10.6, meaning that',
          'the E-value for the persistent state was 15.5 and 10.6 (Table S9), meaning that', 'EN Table S9')
cn = swap(cn, '持续状态的 E 值为 **15.5 与 10.6**，即某一个未测混杂',
          '持续状态的 E 值为 **15.5 与 10.6**（表 S9），即某一个未测混杂', 'CN 表 S9')

if fails:
    print('ABORT:'); [print('  -', f) for f in fails]; sys.exit(1)

io.open(EN, 'w', encoding='utf-8').write(en)
io.open(CN, 'w', encoding='utf-8').write(cn)
print('done: abstract, Figure 3 caption, abbreviations, Table S9 pointer')
