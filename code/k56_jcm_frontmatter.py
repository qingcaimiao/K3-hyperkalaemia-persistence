# -*- coding: utf-8 -*-
"""K3 稿件 → JCM/MDPI 前置件与声明段：
 1. 标题页（作者、单位、ORCID、通讯）
 2. 把 BMC 式 Declarations 改写为 JCM 模板命名
 3. 新增 Supplementary Materials 段（S1–S10）
声明段的顺序依 MDPI 模板：Supplementary Materials → Author Contributions → Funding
→ Institutional Review Board Statement → Informed Consent Statement → Data Availability
→ Acknowledgments → Conflicts of Interest → References
"""
import io

P = 'out/manuscript_K3.md'
s = io.open(P, encoding='utf-8').read()

TITLE_END = s.index('\n', s.index('# '))          # 标题行结束
abstract_at = s.index('## Abstract')

TITLEPAGE = """
Qingcai Miao 1,2, Jianhong Cen 1, Lu Chen 1, Runzhi Lu 1, Renjie Zhang 1,*

1 Department of Cardiology, Handan First Hospital, Handan 056002, China; 15511075821@163.com (Q.M.)
2 Hebei Key Laboratory of Cardiac Precision Medicine, Handan 056002, China
* Correspondence: zhangrenjie725@sina.com; Tel.: +86-155-1107-5821

ORCID: Qingcai Miao, https://orcid.org/0009-0006-1479-6726; Renjie Zhang, https://orcid.org/0009-0009-4026-2068

"""

DECL = """## Supplementary Materials

The following supporting information can be downloaded at the journal website. Table S1: definitions and code
lists; Table S2: cohort derivation; Table S3: full state-transition matrix; Table S4: expected confirmation rate
under competing explanations; Table S5: sensitivity of the persistent state to the minimum number of measurements;
Table S6: sensitivity of the persistence estimate to the potassium threshold; Table S7: robustness of the adjusted
odds ratio for in-hospital death; Table S8: sensitivity of the expected confirmation rate to the between-patient
variance of true potassium; Table S9: E-values for each state against the no-episode group; Table S10: STROBE
checklist for this study.

## Author Contributions

Conceptualization, Q.M. and R.Z.; methodology, Q.M. and R.Z.; software, Q.M.; validation, Q.M., J.C. and L.C.;
formal analysis, Q.M.; investigation, Q.M.; resources, J.C., L.C. and R.L.; data curation, Q.M.; writing-original
draft preparation, Q.M.; writing-review and editing, J.C., L.C., R.L. and R.Z.; visualization, Q.M.; supervision,
R.Z.; project administration, R.Z. All authors have read and agreed to the published version of the manuscript.

## Funding

This research received no external funding.

## Institutional Review Board Statement

The study was conducted in accordance with the Declaration of Helsinki. Both databases are de-identified and
publicly available under credentialed data-use agreements. Their original collection was approved by the
institutional review boards of the Beth Israel Deaconess Medical Center and the Massachusetts Institute of
Technology (MIMIC-IV) and by the institutional review boards of the participating sites (eICU-CRD), with a waiver
of informed consent. No additional ethics approval was required for this secondary analysis of de-identified data.

## Informed Consent Statement

Not applicable. Patient consent was waived because both databases contain only de-identified retrospective data
collected under their original approvals.

## Data Availability Statement

MIMIC-IV (version 3.1) and the eICU Collaborative Research Database (version 2.0) are available on PhysioNet
(refs. [17,18]) to researchers holding a credentialed data-use agreement. Those agreements prohibit the
redistribution of patient-level data, so the derived patient-level datasets cannot be shared publicly. The analysis
code and the derived aggregate tables are archived at GitHub (https://github.com/qingcaimiao/K3-hyperkalaemia-persistence)
and deposited in Zenodo (DOI: 10.5281/zenodo.[XXXXXXX]).

## Acknowledgments

During the preparation of this work the authors used a large language model assistant (DeepSeek, DeepSeek AI,
Hangzhou, China; version [to be confirmed]) to assist with review of the analysis code and with language editing.
The tool did not generate research data or results, and all outputs were reviewed and edited by the authors, who
take full responsibility for the content of this publication.

## Conflicts of Interest

The authors declare no conflicts of interest.

## Abbreviations

The following abbreviations are used in this manuscript:

| Abbreviation | Definition |
|---|---|
| AUC | area under the receiver-operating-characteristic curve |
| CI | confidence interval |
| eICU-CRD | eICU Collaborative Research Database |
| MIMIC-IV | Medical Information Mart for Intensive Care IV |
| OR | odds ratio |
| RCV | reference change value |
| STROBE | Strengthening the Reporting of Observational Studies in Epidemiology |
"""

# ---- 1) 标题页 ----
s = s[:TITLE_END] + '\n' + TITLEPAGE + '\n---\n\n' + s[abstract_at:]

# ---- 2) 参考文献之后的部分整体替换为 JCM 声明段 ----
i = s.index('## Declarations')
s = s[:i] + '## Declarations\n\n' + DECL + '\n'

# ---- 3) MDPI 顺序：声明段在前，References 置于全文最后 ----
ir = s.index('## References')
idc = s.index('## Declarations')
head_block = s[:ir].rstrip('\n').rstrip('-').rstrip('\n')
refs_block = s[ir:idc]
decl_block = s[idc:]
s = head_block + '\n\n---\n\n' + decl_block.rstrip('\n') + '\n\n---\n\n' + refs_block.rstrip('\n') + '\n'

io.open(P, 'w', encoding='utf-8').write(s)

print('标题页与声明段写入完成')
print('章节次序:', [x for x in ['## Abstract', '## 1. Introduction', '## Tables', '## Figure legends',
                               '## Declarations', '## References'] if x in s])
print('Declarations 位置 < References 位置:', s.index('## Declarations') < s.index('## References'))
for k in ['Institutional Review Board Statement', 'Informed Consent Statement', 'Data Availability Statement',
          'Author Contributions', 'Conflicts of Interest', 'Supplementary Materials', 'Abbreviations']:
    print('  %-38s %s' % (k, 'OK' if k in s else '缺失'))
for bad in ['Ethics approval and consent to participate', 'Consent for publication',
            'Availability of data and materials', 'Competing interests', 'Additional files']:
    print('  旧命名 %-42s 残留 %d' % (bad, s.count(bad)))
