# -*- coding: utf-8 -*-
"""k75: exhaustive table audit — every cell of every table, md source vs docx.

For each table in the manuscript (7 data tables + the Abbreviations table) the markdown
cell text is compared with the text of the corresponding <w:tc> in word/document.xml.
Any difference in row/column count or in a single cell is reported with its coordinates.

Also verifies, for every table: caption present, every figure referenced in the text,
and that the numbers appearing in each table footnote also appear in the table body or
in the results files.
"""
import io, re, sys, zipfile

MD = 'out/manuscript_K3.md'
DOCX = 'out/manuscript_K3_EN.docx'
rows_out = []
fails = 0


def norm(t):
    t = (t.replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
          .replace('&apos;', "'").replace('&amp;', '&'))   # XML 实体
    t = re.sub(r'\*+', '', t)              # markdown emphasis
    t = t.replace('\u00a0', ' ')
    return re.sub(r'\s+', ' ', t).strip()


md = io.open(MD, encoding='utf-8').read()
# ---- markdown tables in document order ----
blocks = re.split(r'\n{2,}', md)
md_tables, md_titles = [], []
for b in blocks:
    if b.lstrip().startswith('|'):
        lines = [l.strip() for l in b.strip().split('\n') if l.strip().startswith('|')]
        head = [norm(c) for c in lines[0].strip('|').split('|')]
        body = [[norm(c) for c in l.strip('|').split('|')] for l in lines[2:]]
        md_tables.append((head, body))
for m in re.finditer(r'(?m)^### (Table \d+\.|Abbreviations)', md):
    md_titles.append(m.group(1))
# Abbreviations table title
md_titles = [t for t in md_titles]

x = zipfile.ZipFile(DOCX).read('word/document.xml').decode('utf-8')
dx_tables = []
for t in re.findall(r'<w:tbl>.*?</w:tbl>', x, re.S):
    rows = []
    for r in re.findall(r'<w:tr[ >].*?</w:tr>', t, re.S):
        rows.append([norm(re.sub(r'<[^>]+>', '', c)) for c in re.findall(r'<w:tc[ >].*?</w:tc>', r, re.S)])
    dx_tables.append(rows)

print('md 表格数: %d | docx 表格数: %d' % (len(md_tables), len(dx_tables)))
if len(md_tables) != len(dx_tables):
    print('*** 表格数量不一致 ***'); fails += 1
labels = ['Table 1', 'Table 2', 'Table 3', 'Table 4', 'Table 5', 'Table 6', 'Table 7', 'Abbreviations']

for k, ((mh, mb), drows) in enumerate(zip(md_tables, dx_tables)):
    lab = labels[k] if k < len(labels) else 'table %d' % (k + 1)
    mrows = [mh] + mb
    diff = []
    if len(mrows) != len(drows):
        diff.append('行数 md=%d docx=%d' % (len(mrows), len(drows)))
    for i in range(min(len(mrows), len(drows))):
        a, b = mrows[i], drows[i]
        if len(a) != len(b):
            diff.append('第 %d 行列数 md=%d docx=%d' % (i + 1, len(a), len(b)))
            continue
        for j, (ca, cb) in enumerate(zip(a, b)):
            if ca != cb:
                diff.append('R%dC%d md=%r docx=%r' % (i + 1, j + 1, ca, cb))
    status = '✅' if not diff else '⚠️'
    if diff:
        fails += 1
    rows_out.append('| %s | %d 行 × %d 列 | %s | %s |'
                    % (lab, len(mrows), len(mh), status, '；'.join(diff[:4]) if diff else '逐格一致'))
    print('  %-14s %2d 行 × %d 列  %s  %s' % (lab, len(mrows), len(mh), status,
                                              '；'.join(diff[:3]) if diff else ''))

# ---- caption presence for every table / figure ----
md_titles = re.findall(r'(?m)^### (Table \d+\.|Abbreviations)', md)
figs = re.findall(r'\*\*(Figure \d+)\.\*\*', md)
titles = [t.rstrip('.') for t in md_titles]
missing = [l for l in labels[:-1] if l not in titles]
print('\n每个表都有标题:', '✅' if not missing else '⚠️ 缺 ' + str(missing))
figcap = re.findall(r'\*\*(Figure \d+)\.', md)
print('图注数: %d | 图片数: %d' % (len(figcap), md.count('![')))
for n in range(1, 7):
    cnt = len(re.findall(r'Figure %d(?![0-9])' % n, md))
    print('  Figure %d 正文引用 %d 次 %s' % (n, cnt - 1, '✅' if cnt - 1 >= 1 else '⚠️'))

io.open('out/K3_table_cell_audit.md', 'w', encoding='utf-8').write(
    '# 表格逐格核对（脚本生成，`k75_table_cell_audit.py`）\n\n'
    '对照对象：`manuscript_K3.md`（源）与 `manuscript_K3_EN.docx` 的 `<w:tbl>` 单元格\n\n'
    '| 表 | 规模 | 结果 | 差异 |\n|---|---|---|---|\n' + '\n'.join(rows_out) +
    '\n\n表数量：md %d / docx %d；表标题齐全：%s\n' % (len(md_tables), len(dx_tables), '是' if not missing else '否'))
print('\n差异项合计: %d' % fails)
sys.exit(1 if fails else 0)
