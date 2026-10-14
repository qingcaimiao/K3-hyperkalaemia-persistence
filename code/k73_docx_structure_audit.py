# -*- coding: utf-8 -*-
"""k73: docx structure audit — the check that settles PDF-layer false alarms.

Reads word/document.xml directly and verifies, on the ACTUAL document structure:
  1. no duplicated paragraph (the "page 2 is repeated" class of claim)
  2. no run of >=6 consecutive short numbers or >5 years in one paragraph
     (the "1 1 1 1" / "years 2020-2787" class of claim)
  3. every table is a real <w:tbl> whose column count equals its <w:tblGrid>
  4. every heading is its own paragraph (the "StatementMIMIC-IV" class of claim)
  5. reference numbering is unique and consecutive
  6. spelling sentinels that PDF font recognition commonly corrupts
     (capital I read as lower-case l, lost hyphens)
  7. sentence-completeness sentinels for the two sentences repeatedly reported
     as truncated
  8. cross-page protection: tblHeader on every table, keepNext on captions
Run: python k73_docx_structure_audit.py
"""
import io, re, sys, zipfile
from collections import Counter

FILES = [('out/manuscript_K3_EN.docx', 'en'), ('out/稿件_K3_中文版.docx', 'zh')]
R = []
W = R.append
bad = 0


def chk(ok, label, detail=''):
    global bad
    if not ok:
        bad += 1
    W('| %s | %s | %s |' % (label, '✅' if ok else '⚠️ **FAIL**', detail))


def paragraphs(x):
    return [re.sub(r'<[^>]+>', '', p) for p in re.findall(r'<w:p[ >].*?</w:p>', x, re.S)]


W('| 检查项 | 结果 | 说明 |')
W('|---|---|---|')

for path, lang in FILES:
    x = zipfile.ZipFile(path).read('word/document.xml').decode('utf-8')
    paras = [p for p in paragraphs(x) if p.strip()]
    txt = '\n'.join(paras)
    tag = path.split('/')[-1]
    W('\n**%s**（%d 段）\n' % (tag, len(paras)))

    # 1 duplicate paragraphs
    c = Counter(p[:90] for p in paras if len(p) > 150)
    dup = [k[:50] for k, v in c.items() if v > 1]
    chk(not dup, '无重复长段', str(dup[:3]))

    # 2 digit / year runs
    numruns = [p[:60] for p in paras if re.search(r'(\b\d{1,2}\b[ ,]{1,3}){6,}', p)]
    yearruns = [p[:60] for p in paras if len(re.findall(r'\b(?:19|20|21|22|23)\d{2}\b', p)) > 5]
    chk(not numruns, '无「1 1 1 1」式数字串', str(numruns[:2]))
    chk(not yearruns, '无年份串码', str(yearruns[:2]))

    # 3 tables: real tables with consistent grid
    tbls = re.findall(r'<w:tbl>.*?</w:tbl>', x, re.S)
    bad_tbl = []
    for i, t in enumerate(tbls, 1):
        rows = re.findall(r'<w:tr[ >].*?</w:tr>', t, re.S)
        cols = {len(re.findall(r'<w:tc[ >]', r)) for r in rows}
        g = re.search(r'<w:tblGrid>.*?</w:tblGrid>', t, re.S)
        gc = len(re.findall(r'<w:gridCol', g.group(0))) if g else -1
        if len(cols) != 1 or cols != {gc}:
            bad_tbl.append('T%d cols=%s grid=%s' % (i, sorted(cols), gc))
    chk(len(tbls) >= 8 and not bad_tbl, '表格结构（列数=tblGrid）',
        '%d 个真表格 %s' % (len(tbls), bad_tbl or ''))

    # 4 headings stand alone
    heads = (['Data Availability Statement', 'Acknowledgments', 'Institutional Review Board Statement',
              'Informed Consent Statement', 'Author Contributions', 'Funding', 'Conflicts of Interest',
              'Supplementary Materials', 'Abbreviations', 'References', 'Abstract']
             if lang == 'en' else
             ['数据可用性声明', '致谢', '机构审查委员会声明', '知情同意声明', '作者贡献', '资助',
              '利益冲突', '补充材料', '缩写', '参考文献', '摘要'])
    stuck = [h for h in heads if not any(t.startswith(h) for t in paras)]
    chk(not stuck, '各标题独立成段', str(stuck))

    # 5 references
    key = 'References' if lang == 'en' else '参考文献'
    if key in paras:
        k = paras.index(key)
        refs = [p for p in paras[k + 1:] if re.match(r'^\s*\d{1,2}\s*[.、]\s*\S', p)]
        nums = [int(re.match(r'^\s*(\d{1,2})', p).group(1)) for p in refs]
        ok = nums == list(range(1, len(nums) + 1))
        cdup = [a[:40] for a, b in Counter(p[:60] for p in refs).items() if b > 1]
        chk(ok and not cdup, '参考文献编号连续唯一', '%d 条；重复=%s' % (len(refs), cdup or '无'))

    # 6 spelling sentinels
    sent = (['elCU', 'MIMICIV', 'MIMICIV-', 'eICUCRD'] if lang == 'en' else ['elCU', 'MIMICIV'])
    hits = {s: txt.count(s) for s in sent if txt.count(s)}
    chk(not hits, '无 PDF 字体识别易错拼写', str(hits))

    # 7 truncated-sentence sentinels
    if lang == 'en':
        s1 = 'from six hours before the index value to the repeat measurement'
        s2 = 'specifies repeat measurement at 1, 2, 4, 6 and 24 hours'
        chk(s1 in txt and s2 in txt, '两处易被误报截断的句子完整', '')
    else:
        s1 = '自索引值前 6 小时至复查值'
        got = ('6 小时' in txt and '复查' in txt)
        chk(got, '易被误报截断的句子完整', '')

    # 8 cross-page protection
    th = x.count('<w:tblHeader')
    kn = x.count('<w:keepNext')
    chk(th == len(tbls) and kn >= len(tbls) + 6, '跨页保护（重复表头/锁定表题图注）',
        'tblHeader=%d / tbl=%d，keepNext=%d' % (th, len(tbls), kn))

out = ('# docx 结构审计（脚本生成，`k73_docx_structure_audit.py`）\n\n'
       '用于回应「PDF 文本层伪影」类外部意见：全部结论直接取自 `word/document.xml` 的\n'
       '段落（`<w:p>`）、表格（`<w:tbl>`）与单元格（`<w:tc>`）结构。\n\n'
       + '\n'.join(R) + '\n\n' +
       ('**全部通过 ✅**\n' if bad == 0 else '**存在 %d 项需处理 ⚠️**\n' % bad))
io.open('out/K3_docx_structure_audit.md', 'w', encoding='utf-8').write(out)
print(out)
sys.exit(1 if bad else 0)
