# -*- coding: utf-8 -*-
"""k88: audit the Chinese manuscripts Word->PDF (text layer + render a few pages)."""
import os
import re

import pypdfium2 as pdfium
from pypdf import PdfReader

K = 'D:/桌面/workbuddyzuopin/K3xiangmu/'
pdf = K + '稿件_K3_中文版_Word转PDF.pdf'
out = 'out/_pdfword_cn/'
os.makedirs(out, exist_ok=True)

r = PdfReader(pdf)
t = '\n'.join(p.extract_text() or '' for p in r.pages)
print('=== 中文稿 Word→PDF ===')
print('  页数: %d | 字符: %d' % (len(r.pages), len(t)))
pg0 = r.pages[0]
print('  页面: %.0f x %.0f pt' % (float(pg0.mediabox.width), float(pg0.mediabox.height)))
glue = [s for s in ['声明MIMIC', '致谢During', '表头MIMIC', 'MIMIC-IVeICU', '参考文献1.'] if s in t]
print('  粘连哨兵:', glue or '全 0 ✅')
print('  页眉页脚:', [x for x in ['file:///', 'about:blank'] if x in t] or '无 ✅')
keys = ['20,322', '28,805', '1,182', '997', '5.82', '3.46', '0.42', '0.35', '11.87', '8.05', '52.0', '42.0']
print('  关键数字缺失:', [k for k in keys if k not in t] or '无 ✅')
# 后置章节顺序
order = ['补充材料', '作者贡献', '资助', '机构审查委员会声明', '知情同意声明', '数据可用性声明', '致谢', '利益冲突', '缩写', '参考文献']
pos = [(o, t.find(o)) for o in order]
print('  后置章节:', ' → '.join('%s%s' % (o, '✓' if p >= 0 else '✗') for o, p in pos))
print('  顺序单调:', all(p >= 0 for _, p in pos) and pos == sorted(pos, key=lambda kv: kv[1]))
print('\n=== 后置区（PDF 抽取原文，末 1800 字符）===')
print(t[-1800:])
print('\n=== 标题在 PDF 中的匹配（去空白后）===')
flat = re.sub(r'\s+', '', t)
for o in order:
    print('  %-14s %s' % (o, '✓' if o in flat else '✗'))

doc = pdfium.PdfDocument(pdf)
for pg in sorted(set([1, len(doc) // 2, len(doc)])):
    img = doc[pg - 1].render(scale=1.5).to_pil()
    f = out + 'p%02d.png' % pg
    img.save(f)
    print('  ->', f, img.size)
