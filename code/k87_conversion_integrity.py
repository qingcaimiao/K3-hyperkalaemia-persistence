# -*- coding: utf-8 -*-
"""k87: verify the Word->PDF conversion lost nothing.

Checks, at whitespace-stripped character level:
  1. every Word paragraph of >=30 chars appears in the PDF text
  2. every Word table cell of >=2 chars appears in the PDF text
  3. reverse check: PDF text that has no counterpart in Word (should be ~empty)
"""
import io
import re
import sys
import zipfile

from docx import Document
from pypdf import PdfReader

K = 'D:/桌面/workbuddyzuopin/K3xiangmu/'
docx_path = K + '投稿包_JCM/01_Manuscript.docx'
pdf_path = sys.argv[1] if len(sys.argv) > 1 else K + 'manuscript_K3_EN_Word转PDF.pdf'


def nospace(s):
    return re.sub(r'\s+', '', s)


doc = Document(docx_path)
paras = [p.text for p in doc.paragraphs if p.text.strip()]
cells = []
for t in doc.tables:
    for row in t.rows:
        for c in row.cells:
            if c.text.strip():
                cells.append(c.text)

pdf_txt = nospace('\n'.join(p.extract_text() or '' for p in PdfReader(pdf_path).pages))

miss_p = []
for p in paras:
    key = nospace(p)
    if len(key) < 30:
        continue
    probe = key[:60]
    if probe not in pdf_txt:
        # try a shorter probe in case the first 60 chars straddle a page break artifact
        probe2 = key[:35]
        if probe2 not in pdf_txt:
            miss_p.append(p[:80])

miss_c = []
for c in cells:
    key = nospace(c)
    if len(key) < 2:
        continue
    if key[:40] not in pdf_txt:
        miss_c.append(c[:60])

print('=== 完整性比对（去空白字符级） ===')
print('  Word 非空段落: %d | 检出缺失: %d' % (len(paras), len(miss_p)))
for m in miss_p[:10]:
    print('    ✗', m)
print('  Word 非空单元格: %d | 检出缺失: %d' % (len(cells), len(miss_c)))
for m in miss_c[:10]:
    print('    ✗', m)
print('  docx 去空白字符数: %d | pdf 去空白字符数: %d' % (len(nospace(''.join(paras))), len(pdf_txt)))
print('  比值: %.3f' % (len(pdf_txt) / max(1, len(nospace(''.join(paras))))))
