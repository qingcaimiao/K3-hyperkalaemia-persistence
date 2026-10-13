# -*- coding: utf-8 -*-
"""K3 参考文献 → MDPI/JCM 格式 + 按正文首次出现顺序重编号。

数据来源一律为 Crossref（出版商记录），作者名不手工转录。
期刊缩写用受控表（keyed by DOI），缺省回退 Crossref 的 short-container-title。
年份优先 published-print（纸本卷期年），否则 issued。
"""
import io, json, re, time, urllib.request, urllib.parse

P = 'out/manuscript_K3.md'
s = io.open(P, encoding='utf-8').read()
sec = s[s.index('## References'):s.index('## Declarations')]

# ---- 受控期刊缩写表（ISO / MDPI 风格）----
ABBR = {
    '10.1016/j.phrs.2016.09.039': 'Pharmacol. Res.',
    '10.1161/CIRCHEARTFAILURE.113.000792': 'Circ. Heart Fail.',
    '10.1093/ehjcvp/pvy015': 'Eur. Heart J. Cardiovasc. Pharmacother.',
    '10.1002/emp2.12572': 'J. Am. Coll. Emerg. Physicians Open',
    '10.1186/cc11872': 'Crit. Care',
    '10.1136/bmj.39119.607986.47': 'BMJ',
    '10.1016/j.lab.2005.11.008': 'J. Lab. Clin. Med.',
    '10.3109/10408363.2014.966898': 'Crit. Rev. Clin. Lab. Sci.',
    '10.1053/j.ajkd.2005.06.005': 'Am. J. Kidney Dis.',
    '10.1038/s41597-022-01899-x': 'Sci. Data',
    '10.1038/sdata.2018.178': 'Sci. Data',
    '10.1016/S0140-6736(07)61602-X': 'Lancet',
    '10.1161/JAHA.118.011814': 'J. Am. Heart Assoc.',
    '10.1186/s12875-016-0448-5': 'BMC Fam. Pract.',
    '10.1016/j.jacadv.2024.101331': 'JACC Adv.',
    '10.1371/journal.pone.0310046': 'PLoS ONE',
    '10.1097/PEC.0000000000002857': 'Pediatr. Emerg. Care',
    '10.1159/000529588': 'Nephron',
}

refs = {}
for m in re.finditer(r'^(\d+)\.\s+(.*)$', sec, flags=re.M):
    num = int(m.group(1)); body = m.group(2).strip()
    dm = re.search(r'doi:\s*(\S+)', body, flags=re.I)
    refs[num] = dict(raw=body, doi=dm.group(1).rstrip('.') if dm else None)
print('解析 %d 条；无 DOI：%s' % (len(refs), [k for k, v in refs.items() if not v['doi']]))


def crossref(doi, tries=3):
    url = 'https://api.crossref.org/works/' + urllib.parse.quote(doi)
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'K3-refs/1.0 (mailto:15511075821@163.com)'})
            return json.loads(urllib.request.urlopen(req, timeout=30).read().decode())['message']
        except Exception as e:
            if i == tries - 1:
                print('   Crossref 失败 %s: %r' % (doi, e)); return None
            time.sleep(1.5 * (i + 1))


def initials(given):
    parts = [p for p in re.split(r'[\s\-]+', (given or '').replace('.', ' ')) if p]
    return ' '.join(p[0].upper() + '.' for p in parts)


def authors_of(js):
    out = []
    for a in js.get('author') or []:
        fam = (a.get('family') or '').strip(); giv = (a.get('given') or '').strip()
        if fam and giv:
            out.append('%s, %s' % (fam, initials(giv)))
        elif fam:
            out.append(fam)
        elif a.get('name'):
            out.append(a['name'])
    return '; '.join(out)


def year_of(js):
    for key in ('published-print', 'published', 'issued'):
        dp = js.get(key, {}).get('date-parts', [[None]])
        if dp and dp[0] and dp[0][0]:
            return dp[0][0]
    return None


meta = {}
for n, v in refs.items():
    if not v['doi']:
        meta[n] = None; continue
    js = crossref(v['doi'])
    if js is None:
        meta[n] = None; continue
    short = (js.get('short-container-title') or [None])[0]
    jr = ABBR.get(v['doi']) or (short or ((js.get('container-title') or [''])[0]))
    meta[n] = dict(au=authors_of(js),
                   ti=re.sub(r'\s+', ' ', (js.get('title') or [''])[0]).strip(),
                   jr=jr, vol=js.get('volume'),
                   pg=js.get('page') or js.get('article-number'),
                   yr=year_of(js), doi=v['doi'])

# 正文首次出现顺序
body = s[s.index('## 1. Introduction'):s.index('## References')]
order = []
for m in re.finditer(r'\[(\d+(?:[,\u2013-]\d+)*)\]', body):
    for part in m.group(1).replace('\u2013', '-').split(','):
        rng = range(int(part.split('-')[0]), int(part.split('-')[1]) + 1) if '-' in part else [int(part)]
        for x in rng:
            if x not in order:
                order.append(x)
assert sorted(order) == sorted(refs), '正文引用与文献表不一致'
new = {old: i + 1 for i, old in enumerate(order)}


def fmt(n):
    m = meta[n]
    if m is None:                                  # 网站/指南类
        return 'UK Kidney Association. Clinical Practice Guideline: Treatment of Acute Hyperkalaemia in Adults. '\
               'Available online: https://ukkidney.org (accessed on 13 October 2026).'
    au = m['au'].rstrip('.')
    tail = '%s, %s' % (m['yr'], m['vol'])
    if m['pg']:
        tail += ', %s' % m['pg']
    return '%s. %s. *%s* %s. https://doi.org/%s' % (au, m['ti'], m['jr'], tail, m['doi'])


lines = ['%d. %s' % (new[o], fmt(o)) for o in order]

print('\n===== MDPI 参考文献表 =====')
for l in lines:
    print(l)
print('\n映射（旧→新）:', json.dumps(new, ensure_ascii=False))

json.dump(dict(mapping=new, entries=lines), open('out/k55_refs_mdpi.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
io.open('out/k55_refs_mdpi.txt', 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
print('\n已写 out/k55_refs_mdpi.json / .txt')
