# -*- coding: utf-8 -*-
"""K3 投稿前逐项全量核对（不抽查）

覆盖：字符级 AI/格式残留 · Markdown 模板残留 · AI 措辞 · 结构 · 数字溯源 ·
表格内部一致性 · JCM 合规 · 中英一致性
输出：out/K3_preflight_audit.md（并打印摘要）
"""
import io, re, json, unicodedata, collections
import pandas as pd

EN = 'out/manuscript_K3.md'
CN = 'out/稿件_K3_中文版.md'
en = io.open(EN, encoding='utf-8').read()
cn = io.open(CN, encoding='utf-8').read()
R = []
W = R.append


def h(t):
    W('\n## ' + t)


h('A. 字符级审计（AI/格式残留）')

# 允许的非 ASCII（拉丁重音 + 希腊 + 常用数学/排版符号）
ALLOW = set('áàâäãåéèêëíìîïóòôöõúùûüñçÁÀÂÄÃÅÉÈÊËÍÌÎÏÓÒÔÖÕÚÙÛÜÑÇ'
            'μβΦλτσΔκχ²³·°±×÷−≤≥≈∼–—‘’“”′″†‡§¶•…‹›«»‰ε'
            'αγδθπρσωΑΒΓΔΘΛΠΣΩ')
for label, txt in [('EN', en), ('CN', cn)]:
    cnt = collections.Counter(ch for ch in txt if ord(ch) > 126)

    def expected(ch):
        """中文稿中 CJK 与全角标点是预期内容，不计为可疑"""
        if ch in ALLOW:
            return True
        o = ord(ch)
        if label == 'CN' and (0x4E00 <= o <= 0x9FFF or 0x3000 <= o <= 0x303F
                              or 0xFF00 <= o <= 0xFFEF):
            return True
        return False

    susp = {ch: n for ch, n in cnt.items() if not expected(ch)}
    W('- **%s** 非 ASCII 字符共 %d 种。' % (label, len(cnt)))
    if susp:
        W('  - ⚠️ 白名单外字符（含上下文）：')
        for ch, n in sorted(susp.items(), key=lambda x: -x[1]):
            idx = txt.find(ch)
            ctx = txt[max(0, idx - 45):idx + 25].replace('\n', ' ')
            W('    - `%s` U+%04X %s ×%d ｜ 上下文：…%s…'
              % (ch, ord(ch), unicodedata.name(ch, '?'), n, ctx))
    else:
        W('  - 白名单外字符：**无**')

# 危险字符定点排查
DANGER = {'\u00a0': 'NO-BREAK SPACE', '\u200b': 'ZERO WIDTH SPACE', '\u200c': 'ZWNJ',
          '\u200d': 'ZWJ', '\ufeff': 'BOM/ZWNBSP', '\u2010': 'HYPHEN(非ASCII)',
          '\u2011': 'NB HYPHEN', '\u2012': 'FIGURE DASH', '\u1427': 'CANADIAN SYLLABICS',
          '\u3000': 'IDEOGRAPHIC SPACE', '\uff0c': 'FULLWIDTH COMMA', '\uff08': 'FULLWIDTH (',
          '\uff09': 'FULLWIDTH )', '\uff1a': 'FULLWIDTH COLON'}
for ch, name in DANGER.items():
    a, b = en.count(ch), cn.count(ch)
    if ch in '\uff0c\uff08\uff09\uff1a\u3000':      # 中文稿中的全角标点为预期内容
        b = 0
    if a or b:
        W('- ⚠️ `%s`（%s）：EN %d 处 / CN %d 处' % (ch, name, a, b))
W('- 危险字符定点排查完毕（未列出者表示 0 处；中文稿的全角标点为预期内容，已排除）。')

# 英文稿不应含中文
cjk_en = re.findall(r'[\u4e00-\u9fff]', en)
W('- 英文稿中的汉字：**%d** 个%s' % (len(cjk_en), ('' if not cjk_en else ' ⚠️' + ''.join(sorted(set(cjk_en))))))

h('B. Markdown / 模板残留')
pat = {
    '字面反斜杠转义': r'\\[*_`]',
    'HTML 标签': r'<[a-zA-Z/][^>]{0,40}>',
    '双开方括号占位': r'\[\[',
    'TODO/XXX/待填': r'TODO|XXX|待填|FIXME|\[insert',
    '花括号模板': r'\{[a-zA-Z_]{2,}\}',
    '未替换的 %s': r'%[sd]',
    '连续三个以上星号': r'\*\*\*',
}
for label, txt in [('EN', en), ('CN', cn)]:
    hits = {}
    for k, p in pat.items():
        m = re.findall(p, txt)
        if m:
            hits[k] = (len(m), m[:5])
    W('- **%s**：%s' % (label, ('无残留' if not hits else '')))
    for k, (n, ex) in hits.items():
        W('  - ⚠️ %s ×%d，例：%s' % (k, n, ex))

# 每行星号/下划线是否成对
bad_line = []
for i, ln in enumerate(en.split('\n'), 1):
    if ln.count('**') % 2:
        bad_line.append((i, ln[:70]))
W('- 英文稿中 `**` 未成对的行：%d 行%s' % (len(bad_line), '' if not bad_line else ' ⚠️ ' + str(bad_line[:4])))

h('C. AI 措辞残留（英文稿）')
ai_phrases = ['as an AI', 'as a language model', 'I cannot', "I'm sorry", 'Certainly,', 'Sure,',
              'Here is', 'Here are', 'In this article, we', 'delve', 'tapestry', 'testament to',
              'It is worth noting', 'It should be noted', 'In summary,', 'Overall, this',
              'Let me', 'we can see that', 'As we can see', 'navigate the', 'landscape of',
              'underscores the importance', 'plays a crucial role', 'In the realm of']
found = {p: en.lower().count(p.lower()) for p in ai_phrases}
found = {k: v for k, v in found.items() if v}
W('- 命中：%s' % (found if found else '**无**'))

# AI 声明本身是合规内容，单独标注
seg = en[en.find('## Acknowledgments'):en.find('## Conflicts of Interest')]
W('- AI 披露段（Acknowledgments）内容检查：%s' % ('含工具名+版本 ✅' if 'DeepSeek-V4.1-Flash' in seg else '⚠️ 缺版本'))

dash = en.count('\u2014')
W('- em dash（—）出现 %d 次；全文约 %d 词 → 每千词 %.1f 次' % (dash, 7930, 1000 * dash / 7930))
W('- "not ... but ..." 与 "rather than" 计数：%d / %d（仅为风格提示，非错误）'
  % (len(re.findall(r'\bnot\b[^.]{0,40}\bbut\b', en)), en.count('rather than')))

h('D. 结构审计')
heads = re.findall(r'^(#{1,3}) (.+)$', en, flags=re.M)
W('- 一级/二级标题清单：')
for lv, t in heads:
    if len(lv) <= 2:
        W('  - %s %s' % ('#' * len(lv), t))

tabs = re.findall(r'^### Table (\d+)\.', en, flags=re.M)
figs = re.findall(r'^\*\*Figure (\d+)\.\*\*', en, flags=re.M)
W('- 表格编号：%s（共 %d）' % (tabs, len(tabs)))
W('- 图注编号：%s（共 %d）' % (figs, len(figs)))

# ---- 浮标（表/图）就地化后的引用审计 ----------------------------------------
# MDPI/JCM: "All figures, schemes and tables should be inserted into the main text close
# to their first citation and must be numbered following their order of appearance."
# 因此：(a) 每个表/图都要在正文（= 浮标之外的散文）里被引用；
#       (b) 表标题/图注本身的出现顺序必须与编号一致；
#       (c) 首次引用应出现在该浮标自身位置之前。
_blocks, _start, _off = [], 0, []
for m in re.finditer(r'\n{2,}', en):
    _blocks.append(en[_start:m.start()]); _off.append(_start); _start = m.end()
_blocks.append(en[_start:]); _off.append(_start)

mask = [False] * len(en)          # True = 属于某个浮标（表块或图块），不计入正文引用
appear = {}                       # (kind, n) -> 位置
for i, b in enumerate(_blocks):
    mt = re.match(r'### Table (\d+)\.', b.strip())
    if mt:
        n = int(mt.group(1))
        appear[('T', n)] = _off[i]
        assert i + 2 < len(_blocks), 'table %d has no footnote block' % n
        for k in (i, i + 1, i + 2):                      # 标题 + 表格 + 表注
            for j in range(_off[k], _off[k] + len(_blocks[k])):
                mask[j] = True
    mf = re.match(r'!\[', b.strip())
    if mf and i + 1 < len(_blocks) and re.match(r'\*\*Figure (\d+)\.', _blocks[i + 1].strip()):
        n = int(re.match(r'\*\*Figure (\d+)\.', _blocks[i + 1].strip()).group(1))
        appear[('F', n)] = _off[i]
        for k in (i, i + 1):                             # 图片 + 图注
            for j in range(_off[k], _off[k] + len(_blocks[k])):
                mask[j] = True

prose = ''.join(' ' if mask[j] else ch for j, ch in enumerate(en))

def _first_cite(pat):
    for m in re.finditer(pat, en):
        j = m.start()
        if not mask[j] and not any(mask[j:j + len(m.group(0))]):
            return j, m.group(0)
    return None, None

for kind, lab, count in (('F', 'Figure', len(figs)), ('T', 'Table', len(tabs))):
    for n in range(1, count + 1):
        c = len(re.findall(r'(?<!Table S)%s %d(?![0-9])' % (lab, n), prose))   # 允许 Figure 1A
        W('- %s %d 在正文被引用 %d 次%s' % (lab, n, c, '' if c else ' ⚠️ 未被引用'))
        if ('T', n) not in appear:
            W('  ⚠️ %s %d 找不到标题/图注块' % (lab, n))

# (b) 出现顺序
ord_f = [n for (k, n), _ in sorted(appear.items(), key=lambda kv: kv[1]) if k == 'F']
ord_t = [n for (k, n), _ in sorted(appear.items(), key=lambda kv: kv[1]) if k == 'T']
W('- 图出现顺序：%s → %s' % (ord_f, '递增 ✅' if ord_f == sorted(ord_f) else '⚠️ 非递增'))
W('- 表出现顺序：%s → %s' % (ord_t, '递增 ✅' if ord_t == sorted(ord_t) else '⚠️ 非递增'))

# (c) 首次引用须先于浮标自身
bad = []
for (kind, n), pos in sorted(appear.items()):
    lab = 'Figure' if kind == 'F' else 'Table'
    cz, _ = _first_cite(r'(?<!Table S)%s %d(?![0-9])' % (lab, n))
    if cz is None:
        bad.append('%s %d 无正文引用' % (lab, n))
    elif cz > pos:
        bad.append('%s %d 引用晚于其位置' % (lab, n))
W('- 首次引用均先于该图表自身位置：%s' % ('✅' if not bad else '⚠️ ' + '; '.join(bad)))

# 补充材料引用
for n in range(1, 10):
    c = len(re.findall(r'Table S%d\b' % n, en))
    W('- Table S%d 在稿件中被提及 %d 次%s' % (n, c, '' if c else ' ⚠️'))

h('E. 参考文献')
refsec = en[en.index('## References'):]
refs = re.findall(r'^(\d+)\. (.+)$', refsec, flags=re.M)
W('- 条数：%d；编号：%s' % (len(refs), [int(a) for a, _ in refs]))
nums = [int(a) for a, _ in refs]
W('- 编号连续且从 1 开始：%s' % ('✅' if nums == list(range(1, len(refs) + 1)) else '⚠️'))
# 正文字号首次出现顺序（MDPI：编号顺序含表注与图注，故此处用完整正文而非 prose）
body = en[en.index('## 1. Introduction'):en.index('## References')]
seen = []
for m in re.finditer(r'\[(\d+(?:[,\u2013-]\d+)*)\]', body):
    for part in m.group(1).replace('\u2013', '-').split(','):
        rng = range(int(part.split('-')[0]), int(part.split('-')[1]) + 1) if '-' in part else [int(part)]
        for x in rng:
            if x not in seen:
                seen.append(x)
W('- 正文首次出现顺序递增：%s（%s）' % ('✅' if seen == sorted(seen) else '⚠️', seen))
W('- 正文引用的最大编号 %d vs 文献条数 %d：%s' % (max(seen), len(refs), '✅' if max(seen) == len(refs) else '⚠️'))
# 每条格式检查
badref = []
for a, t in refs:
    ok_doi = ('doi.org' in t) or ('Available online' in t)
    ok_yr = bool(re.search(r'\b(19|20)\d{2}\b', t))
    ok_au = (';' in t) or ('Association' in t)
    if not (ok_doi and ok_yr and ok_au):
        badref.append((a, ok_doi, ok_yr, ok_au, t[:90]))
W('- 格式要素（作者分号分隔 / 年份 / DOI或URL）不全的条目：%d %s' % (len(badref), badref if badref else '✅ 全部具备'))
W('- 是否残留 "et al."（MDPI 要求全列作者）：%d 处' % len(re.findall(r'\bet al\b', refsec)))

h('F. JCM 合规')
ab = en[en.index('## Abstract'):en.index('**Keywords**')]
w = re.findall(r"[A-Za-z0-9][A-Za-z0-9\-\.\,\%\(\)\u2013\u2265\u2264\-\u2013]*",
               re.sub(r'\*\*[A-Za-z/ ]+\*\*', '', ab))
W('- 摘要词数：**%d**（JCM 研究论文约 250 词）' % (len(w) - 1))
kw = en[en.index('**Keywords**'):].split('\n')[0].replace('**Keywords**', '')
kws = [k.strip() for k in kw.split(';') if k.strip()]
W('- 关键词：%d 个（JCM 允许 3–10）→ %s' % (len(kws), kws))
W('- 结构化摘要小标题：%s' % re.findall(r'\*\*(Background|Methods|Results|Conclusions)\*\*', ab))
need = ['## Author Contributions', '## Funding', '## Institutional Review Board Statement',
        '## Informed Consent Statement', '## Data Availability Statement', '## Acknowledgments',
        '## Conflicts of Interest', '## Supplementary Materials', '## Abbreviations']
missing = [x for x in need if x not in en]
W('- 必需声明段：%s' % ('全部齐备 ✅' if not missing else '⚠️ 缺 ' + str(missing)))
W('- CRediT 用语：%s' % ('✅' if 'Conceptualization' in en and ('Writing \u2013 Review & Editing' in en or 'Writing \u2014 Review & Editing' in en) else '⚠️'))
W('- 标题页要素：作者 %s | 单位 %d 条 | ORCID %s | 通讯 %s' % (
    '✅' if 'Qingcai Miao' in en else '⚠️',
    len(re.findall(r'^\d (Department|Handan|Hebei)', en, flags=re.M)),
    '✅' if 'orcid.org' in en else '⚠️',
    '✅' if 'Correspondence' in en else '⚠️'))
W('- 无 running title：%s' % ('✅' if 'Running title' not in en and 'Running Title' not in en else '⚠️ 存在'))
W('- 图/表数量：%d 图 / %d 表（JCM 常规 4–8 图）' % (len(figs), len(tabs)))
W('- 单位制/阈值写法：mmol/L 出现 %d 次；≥ 出现 %d 次；>= 字面出现 %d 次（应为 0）'
  % (en.count('mmol/L'), en.count('\u2265'), len(re.findall(r'(?<![<>=])>=', en))))

W('\n---\n')
io.open('out/K3_preflight_audit.md', 'w', encoding='utf-8').write(
    '# K3 投稿前全量核对报告\n\n（脚本生成：`k57_preflight_audit.py`，不抽查）\n' + '\n'.join(R) + '\n')
print('\n'.join(R))
print('\n已写 out/K3_preflight_audit.md')
