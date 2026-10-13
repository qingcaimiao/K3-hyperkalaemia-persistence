# -*- coding: utf-8 -*-
"""k66: place every table and figure immediately after the paragraph in which it is
first cited (MDPI requirement), instead of grouping them in trailing sections.

For each file:
  1. cut the trailing "Tables" and "Figure legends" sections and split them into chunks;
  2. locate, in the remaining body, the paragraph of first citation for every float;
  3. sort the floats by (paragraph, offset within paragraph) and re-insert each chunk
     directly after that paragraph.
Asserts that all 7 tables and 6 figures are placed exactly once and that the order of
appearance is non-decreasing in both numbering sequences.
"""
import io, re, sys

CONF = [
    dict(path='out/manuscript_K3.md', tabs='## Tables', figs='## Figure legends',
         end='## Declarations', tre=r'(?m)^### Table (\d+)\.', tlab='Table %d', flab='Figure %d'),
    dict(path='out/稿件_K3_中文版.md', tabs='## 表', figs='## 图注',
         end='## 参考文献', tre=r'(?m)^### 表 (\d+)\.', tlab='表 %d', flab='图 %d'),
]
IMG_RE = re.compile(r'!\[[^\]]*\]\([^)]*\)')


def blocks_with_offsets(text):
    out, start = [], 0
    for m in re.finditer(r'\n{2,}', text):
        out.append((start, text[start:m.start()]))
        start = m.end()
    out.append((start, text[start:]))
    return out


def process(c):
    s = io.open(c['path'], encoding='utf-8').read()
    if not re.search(r'(?m)^' + re.escape(c['tabs']) + r'\s*$', s):
        print(f"\n=== {c['path']} ===\n  already converted - skipped")
        return None
    i_tab, i_fig, i_end = s.index(c['tabs']), s.index(c['figs']), s.index(c['end'])
    assert i_tab < i_fig < i_end, 'sections out of order'

    region_T = s[i_tab + len(c['tabs']): i_fig]
    region_F = s[i_fig + len(c['figs']): i_end]

    # ---- table chunks ----
    tpos = [m.start() for m in re.finditer(c['tre'], region_T)]
    tchunks = {}
    for k, p in enumerate(tpos):
        q = tpos[k + 1] if k + 1 < len(tpos) else len(region_T)
        chunk = region_T[p:q].strip()
        num = int(re.match(c['tre'], region_T[p:]).group(1))
        tchunks[num] = chunk
    assert sorted(tchunks) == list(range(1, 8)), sorted(tchunks)

    # ---- figure chunks ----
    imgs = list(IMG_RE.finditer(region_F))
    fchunks = {}
    for k, m in enumerate(imgs):
        q = imgs[k + 1].start() if k + 1 < len(imgs) else len(region_F)
        cap = region_F[m.end():q].strip()
        num = int(re.match(r'\*\*\D*?(\d+)\.', cap).group(1))
        fchunks[num] = m.group(0) + '\n\n' + cap
    assert sorted(fchunks) == list(range(1, 7)), sorted(fchunks)

    body = s[:i_tab] + s[i_end:]
    bl = blocks_with_offsets(body)

    # ---- locate first citation of each float ----
    plan, report = [], []
    for num in sorted(tchunks):
        tok, kind = c['tlab'] % num, 'T'
        hit = next((i for i, (_, t) in enumerate(bl) if tok in t), None)
        assert hit is not None, f'table {num} never cited'
        off = bl[hit][1].index(tok)
        plan.append((hit, off, kind, num))
    for num in sorted(fchunks):
        tok, kind = c['flab'] % num, 'F'
        hit = next((i for i, (_, t) in enumerate(bl) if tok in t), None)
        assert hit is not None, f'figure {num} never cited'
        off = bl[hit][1].index(tok)
        plan.append((hit, off, kind, num))

    plan.sort(key=lambda x: (x[0], x[1]))

    # numbering must appear in non-decreasing order within each sequence
    for kind in 'TF':
        seq = [n for _, _, k, n in plan if k == kind]
        assert seq == sorted(seq), f'{kind} order broken: {seq}'

    inserts = {}
    for hit, off, kind, num in plan:
        inserts.setdefault(hit, []).append(tchunks[num] if kind == 'T' else fchunks[num])
        report.append((kind, num, hit, bl[hit][1][max(0, bl[hit][1].find((c["tlab"] if kind == "T" else c["flab"]) % num) - 60):][:70]))

    parts = []
    for i, (_, txt) in enumerate(bl):
        parts.append(txt)
        if i in inserts:
            parts.append('\n\n'.join(inserts[i]))
    out = '\n\n'.join(parts)

    # ---- verification ----
    # NOTE: a naive "first occurrence of the token" check is invalid here, because once the
    # floats are inline their own footnotes mention other tables. Verify instead that the
    # table HEADINGS and the FIGURE CAPTIONS themselves appear in ascending order.
    assert not re.search(r'(?m)^' + re.escape(c['tabs']) + r'\s*$', out), 'tables section heading still present'
    assert not re.search(r'(?m)^' + re.escape(c['figs']) + r'\s*$', out), 'figure section heading still present'
    figcap = r'\*\*' + ('Figure' if c['tlab'] == 'Table %d' else '图') + r' (\d+)\.'
    pos = {}
    for num in range(1, 8):
        m = list(re.finditer(r'(?m)^### ' + (c['tlab'] % num).replace('.', r'\.') + r'\.', out))
        assert len(m) == 1, f'table heading {num}: {len(m)} occurrences'
        pos[('T', num)] = m[0].start()
    for num in range(1, 7):
        m = list(re.finditer(figcap.replace(r'(\d+)', str(num)), out))
        assert len(m) == 1, f'figure caption {num}: {len(m)} occurrences'
        pos[('F', num)] = m[0].start()
        assert out.count(c['flab'] % num) >= 2, f'figure {num} cited in text?'
    for kind in 'TF':
        seq = [n for (k, n), _ in sorted(pos.items(), key=lambda kv: kv[1]) if k == kind]
        assert seq == sorted(seq), f'{kind} placement order broken: {seq}'
    # every figure image must sit immediately before its caption
    for num in range(1, 7):
        i = pos[('F', num)]
        head = out[max(0, i - 200):i]
        assert IMG_RE.search(head), f'figure {num}: image not adjacent to caption'

    io.open(c['path'], 'w', encoding='utf-8').write(out)
    print(f"\n=== {c['path']} ===")
    print(f"tables: {len(tchunks)}  figures: {len(fchunks)}  chunks placed: {sum(len(v) for v in inserts.values())}")
    for kind, num, hit, snip in sorted(report):
        print(f"  {kind}{num:>2} -> after block {hit:>3}  ...{snip}")
    return out


for c in CONF:
    process(c)
print("\nOK")
