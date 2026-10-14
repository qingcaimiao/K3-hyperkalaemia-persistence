# -*- coding: utf-8 -*-
"""
Fix 1: remove the non-MDPI "Declarations" wrapper heading (EN) and restructure the
       Chinese back matter to match (level ## sections, References last).
Fix 2: add the missing blank line before the <hr> that follows the Abbreviations table.
Fix 3: align the Conflicts of Interest sentence to the string quoted by MDPI.
"""
import io, re, sys

EN = 'out/manuscript_K3.md'
CN = 'out/稿件_K3_中文版.md'
fails = []

# ---------------------------------------------------------------- EN
s = io.open(EN, encoding='utf-8').read()

# 1) drop the "## Declarations" wrapper (not part of the MDPI template)
old = '---\n\n## Declarations\n\n## Supplementary Materials'
new = '---\n\n## Supplementary Materials'
if s.count(old) != 1:
    fails.append('EN Declarations wrapper: %d' % s.count(old))
else:
    s = s.replace(old, new, 1)
    print('  EN: removed "## Declarations" wrapper')

# 2) blank line before the <hr> that follows the Abbreviations table
old = '| STROBE | Strengthening the Reporting of Observational Studies in Epidemiology |\n---'
new = '| STROBE | Strengthening the Reporting of Observational Studies in Epidemiology |\n\n---'
if s.count(old) != 1:
    fails.append('EN hr after abbreviations table: %d' % s.count(old))
else:
    s = s.replace(old, new, 1)
    print('  EN: added blank line before the separator that follows the Abbreviations table')

# 3) Conflicts of Interest sentence -> the exact string quoted by MDPI
old = 'The authors declare no conflicts of interest.'
new = 'The authors declare no conflict of interest.'
if s.count(old) != 1:
    fails.append('EN CoI: %d' % s.count(old))
else:
    s = s.replace(old, new, 1)
    print('  EN: Conflicts of Interest sentence aligned to the MDPI template string')

io.open(EN, 'w', encoding='utf-8').write(s)

# ---------------------------------------------------------------- CN
t = io.open(CN, encoding='utf-8').read()

i_head = t.index('## 参考文献')
i_decl = t.index('## 声明')

head = t[:i_head]                      # ... 5. 结论 + '---\n\n'
refs = t[i_head:i_decl]                # '## 参考文献\n\n1..19\n'
decl = t[i_decl:]                      # '## 声明\n\n### 补充材料 ... '

if '## 5. 结论' not in head or '19. von Elm' not in refs:
    fails.append('CN block split')
if '### 缩写' not in decl:
    fails.append('CN declaration block')

# strip the wrapper heading and demote nothing: raise '### X' back-matter headings to '## X'
body = decl
body = body[body.index('### 补充材料'):]                       # drop '## 声明' + its intro
n_demote = len(re.findall(r'(?m)^### ', body))
body = re.sub(r'(?m)^### ', '## ', body)
body = body.rstrip('\n')

refs_body = refs[refs.index('1. Rossignol'):].rstrip('\n')

new_cn = head + body + '\n\n---\n\n## 参考文献\n\n' + refs_body + '\n'

if new_cn.count('## 参考文献') != 1 or new_cn.count('## 补充材料') != 1 or new_cn.count('## 缩写') != 1:
    fails.append('CN rebuild heading counts')

io.open(CN, 'w', encoding='utf-8').write(new_cn)
print('  CN: demoted headings raised to "##": %d' % n_demote)
print('  CN: References moved to the end (after the declarations block)')

if fails:
    print('ABORT:', fails)
    sys.exit(1)
print('done')
