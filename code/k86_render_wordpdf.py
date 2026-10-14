# -*- coding: utf-8 -*-
"""k86: render selected pages of the Word-derived PDF to PNG for visual inspection."""
import os
import re
import sys

import pypdfium2 as pdfium
from pypdf import PdfReader

K = 'D:/桌面/workbuddyzuopin/K3xiangmu/'
pdf = K + 'manuscript_K3_EN_Word转PDF.pdf'
out = 'out/_pdfword/'
os.makedirs(out, exist_ok=True)

r = PdfReader(pdf)
where = {}
for i, p in enumerate(r.pages, 1):
    t = p.extract_text() or ''
    for k in ['Table 1.', 'Table 2.', 'Table 3.', 'Table 4.', 'Table 5.', 'Table 6.', 'Table 7.',
              'Figure 1.', 'Figure 2.', 'Figure 3.', 'Figure 4.', 'Figure 5.', 'Figure 6.', 'References']:
        if k in t and k not in where:
            where[k] = i
print('定位:', where)

doc = pdfium.PdfDocument(pdf)
picks = sorted(set([1] + list(where.values()) + [len(doc)]))
print('渲染页:', picks)
for pg in picks:
    img = doc[pg - 1].render(scale=1.5).to_pil()
    f = out + 'p%02d.png' % pg
    img.save(f)
    print('  ->', f, img.size)
