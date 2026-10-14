# -*- coding: utf-8 -*-
"""k72: option A - drop supplementary Table S6 (an exact duplicate of main-text Table 7,
which stays in the body) and renumber S7->S6, S8->S7, S9->S8 everywhere.

Touch points (all asserted):
  * K3_Supplementary_Tables.md : delete the S6 block, renumber, add a pointer note
  * manuscript_K3.md           : drop the S6 entry from the list, renumber the list and
                                 the in-text citations
  * 稿件_K3_中文版.md           : same, in Chinese
  * K3_STROBE_checklist.md     : item 16 cites the robustness table
"""
import io, re, sys

K = 'D:/桌面/workbuddyzuopin/K3xiangmu/'
fails = []


def rd(p):
    return io.open(p, encoding='utf-8').read()


def wr(p, s):
    io.open(p, 'w', encoding='utf-8').write(s)


def shift(txt, pat, tag):
    """Renumber S7->S6, S8->S7, S9->S8 in a single pass (no cascading)."""
    seen = []

    def f(m):
        seen.append(m.group(0))
        return m.group(1) + str(int(m.group(2)) - 1)

    out = re.sub(pat, f, txt)
    print('  %-16s renumbered %d reference(s): %s'
          % (tag, len(seen), ', '.join(sorted(set(seen)))))
    return out


# ============ 1. supplementary tables =====================================
p = K + 'K3_Supplementary_Tables.md'
s = rd(p)
i = s.index('## Table S6. Sensitivity of the persistence estimate to the potassium threshold')
j = s.index('## Table S7.')
removed = s[i:j]
if 'Robustness' in removed:
    fails.append('S6 block contains the next heading')
s = s[:i] + s[j:]
print('supplementary: removed S6 block (%d chars, %d data rows)'
      % (len(removed), removed.count('\n|') - 1))
s = shift(s, r'(Table S)([789])\b', 'supplementary')

note = ('Sensitivity of the persistence estimate to the potassium threshold is reported in Table 7 '
        'of the main text and is therefore not repeated here.')
anchor = '## Table S1. Definitions and code lists'
if s.count(anchor) != 1:
    fails.append('supplementary anchor: %d' % s.count(anchor))
else:
    s = s.replace(anchor, note + '\n\n\n' + anchor, 1)
wr(p, s)

# ============ 2. English manuscript ======================================
p = K + 'manuscript_K3.md'
s = rd(p)
frag = 'Table S6: sensitivity of the persistence estimate to the potassium threshold; '
if s.count(frag) != 1:
    fails.append('EN list fragment: %d' % s.count(frag))
s = s.replace(frag, '', 1)
s = shift(s, r'(Table S)([789])\b', 'EN manuscript')
wr(p, s)

# ============ 3. Chinese manuscript ======================================
p = K + '稿件_K3_中文版.md'
s = rd(p)
frag = '表 S6：持续率估计对血钾阈值的敏感性；'
if s.count(frag) != 1:
    fails.append('CN list fragment: %d' % s.count(frag))
s = s.replace(frag, '', 1)
s = shift(s, r'(表 S)([789])', 'CN manuscript')
wr(p, s)

# ============ 4. STROBE checklist ========================================
p = K + 'K3_STROBE_checklist.md'
s = rd(p)
s = shift(s, r'(Table S)([789])\b', 'STROBE checklist')
wr(p, s)

if fails:
    print('ABORT:'); [print('  -', f) for f in fails]; sys.exit(1)
print('done')
