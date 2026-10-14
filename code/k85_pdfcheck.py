# -*- coding: utf-8 -*-
"""k85: audit the PDF produced from the Word manuscript (k84 output)."""
import re
import sys

from pypdf import PdfReader

K = 'D:/桌面/workbuddyzuopin/K3xiangmu/'
pdf = sys.argv[1] if len(sys.argv) > 1 else K + 'manuscript_K3_EN_Word转PDF.pdf'

r = PdfReader(pdf)
t = '\n'.join(p.extract_text() or '' for p in r.pages)
i = t.rindex('References')
seg = t[i:]

print('=== References 区段（PDF） ===')
nums = re.findall(r'(?m)^\s*(\d{1,2})\.\s', seg)
print('  以数字开头的行:', nums)
for n in (1, 13, 17, 18, 19, 20):
    m = re.search(r'(?m)^\s*%d\.\s(.{0,120})' % n, seg)
    print('  [%2d] %s' % (n, m.group(1).replace('\n', ' ') if m else 'NOT FOUND'))

c = re.findall(r'(?m)^\s*\d{1,2}\.\s+[A-Z]', seg)
print('\n=== 文献条数（数字. 大写字母）: %d ===' % len(c))
print('=== 末尾 400 字符 ===')
print(repr(seg[-400:]))
