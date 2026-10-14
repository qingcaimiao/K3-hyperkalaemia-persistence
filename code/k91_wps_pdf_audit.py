# -*- coding: utf-8 -*-
"""k91: audit the WPS-exported PDF (real Word rendering) against the manuscript.

Checks:
  1. page size / count, producer
  2. text-layer quality: are inter-word spaces lost?  (explains the 'glued text' reports)
  3. content completeness: every Word paragraph and every table cell present?
  4. key numbers, references, back-matter order
  5. embedded images (count + sizes)
"""
import io
import re
import sys
from collections import Counter

from docx import Document
from pypdf import PdfReader
from PIL import Image

PDF = 'D:/桌面/01_Manuscript.pdf'
DOCX = 'out/manuscript_K3_EN.docx'


def nz(s):
    return re.sub(r'\s+', '', s)


def main():
    r = PdfReader(PDF)
    t = '\n'.join(p.extract_text() or '' for p in r.pages)
    flat = nz(t)

    print('=== 1. 基本 ===')
    print('  页数 %d | 文本 %d 字符 | 纸张 %.0f x %.0f pt'
          % (len(r.pages), len(t),
             float(r.pages[0].mediabox.width), float(r.pages[0].mediabox.height)))
    print('  （A4 = 595x842 | Letter = 612x792）')

    print('\n=== 2. 文本层空格质量 ===')
    glued = len(re.findall(r'[a-z]{4,}[A-Z][a-z]{3,}', t))
    print('  小写后直接接大写的连写片段: %d 处' % glued)
    for m in list(re.finditer(r'[a-z]{4,}[A-Z][a-z]{3,}', t))[:6]:
        print('     …%s…' % t[max(0, m.start() - 25):m.start() + 30].replace('\n', ' '))
    # 已知哨兵
    sent = [s for s in ['StatementMIMIC', 'AcknowledgmentsDuring', 'WindowMIMIC',
                        'MIMIC-IVeICU', 'elCU', 'MIMICIV', 'codelists', 'rateunder'] if s in flat]
    print('  粘连哨兵（去空白后）:', sent or '无 ✅')

    print('\n=== 3. 内容完整性（Word vs PDF，去空白）===')
    doc = Document(DOCX)
    paras = [p.text for p in doc.paragraphs if len(nz(p.text)) >= 30]
    miss_p = [p for p in paras if nz(p)[:60] not in flat and nz(p)[:35] not in flat]
    cells = []
    for tb in doc.tables:
        for row in tb.rows:
            for c in row.cells:
                if len(nz(c.text)) >= 2:
                    cells.append(c.text)
    miss_c = [c for c in cells if nz(c)[:40] not in flat]
    print('  Word 段落 %d -> 缺失 %d' % (len(paras), len(miss_p)))
    for m in miss_p[:8]:
        print('     ✗', m[:90])
    print('  Word 单元格 %d -> 缺失 %d' % (len(cells), len(miss_c)))
    for m in miss_c[:8]:
        print('     ✗', m[:70])

    print('\n=== 4. 关键数字 / 参考文献 / 后置章节 ===')
    keys = ['20,322', '28,805', '23,429', '41,917', '1,182', '997', '5.82', '3.46', '0.42', '0.35',
            '19.0', '23.5', '11.87', '8.05', '1.56', '2.77', '4.41', '4.52', '52.0', '42.0',
            '15.5', '10.6', '0.101', '0.164']
    print('  关键数字缺失:', [k for k in keys if nz(k) not in flat] or '无 ✅')
    i = flat.rfind('References')
    refs = re.findall(r'(?m)^\s*(\d{1,2})\.\s+[A-Z]', t[t.rindex('References'):]) if 'References' in t else []
    print('  References 内检出编号:', refs)
    order = ['Supplementary Materials', 'Author Contributions', 'Funding',
             'Institutional Review Board Statement', 'Informed Consent Statement',
             'Data Availability Statement', 'Acknowledgments', 'Conflicts of Interest',
             'Abbreviations', 'References']
    pos = [(o, flat.find(nz(o))) for o in order]
    print('  后置章节:', ' → '.join('%s%s' % (o, '✓' if p >= 0 else '✗') for o, p in pos))
    print('  顺序单调:', all(p >= 0 for _, p in pos) and pos == sorted(pos, key=lambda kv: kv[1]))

    print('\n=== 5. 图片 ===')
    tot = 0
    for i, p in enumerate(r.pages, 1):
        try:
            imgs = list(p.images)
        except Exception:
            imgs = []
        if imgs:
            tot += len(imgs)
            print('  第 %2d 页: %d 张  %s' % (i, len(imgs), [im.name for im in imgs][:6]))
    print('  合计图像对象: %d（正文应 6 张）' % tot)

    print('\n=== 6. 页码 / 页眉 ===')
    print('  含页码样式（数字单独一行）的页:', sum(
        1 for p in r.pages if re.search(r'(?m)^\s*\d{1,2}\s*$', p.extract_text() or '')))


if __name__ == '__main__':
    main()
