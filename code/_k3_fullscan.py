# -*- coding: utf-8 -*-
"""全文数字扫描：稿件中每个数字是否都有审计来源（人工判定残留项）"""
import pandas as pd, re
from docx import Document

a = pd.concat([pd.read_csv('out/k3_audit_numbers.csv'), pd.read_csv('out/k3_audit_numbers2.csv')], ignore_index=True)


def norm(s):
    try:
        return '%g' % float(str(s).replace(',', ''))
    except Exception:
        return str(s)


vals = set()
for col in ['value', 'note', 'item']:
    for v in a[col].dropna().astype(str):
        for tok in re.findall(r'\d[\d,]*(?:\.\d+)?', v):
            vals.add(norm(tok))

LEGIT = {'5.5', '24', '72', '7', '6', '12', '2', '4', '1', '3', '5.9', '6.5', '6.0', '1.96', '9', '5', '8',
         '1.5', '3.0', '5.0', '15', '10', '20', '50971', '3.1', '2.0', '3.13', '11', '13', '14', '16', '17',
         '18', '19', '21', '22', '23', '25', '26', '27', '28', '29', '30', '31', '32', '33', '25.5'}
YEARS = {str(y) for y in range(1900, 2031)}

for f in ['out/manuscript_K3_EN.docx', 'out/稿件_K3_中文版.docx']:
    doc = Document(f)
    txt = '\n'.join(p.text for p in doc.paragraphs)
    print('=' * 90); print(f)
    lines = txt.split('\n')
    for i, ln in enumerate(lines, 1):
        if re.search(r'^\s*(\d+\.\s+[A-Z]|参考文献|References)', ln): continue
        nums = re.findall(r'\d[\d,]*(?:\.\d+)?', ln)
        if not nums: continue
        miss = [n for n in nums if norm(n) not in vals and norm(n) not in LEGIT and norm(n) not in YEARS]
        if miss:
            print('  %4d %s' % (i, ln[:150]))
            print('        >> 待人工判定: %s' % miss)
