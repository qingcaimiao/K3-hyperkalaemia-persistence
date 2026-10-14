# -*- coding: utf-8 -*-
"""k79: dual-source verification of every reference in the K3 manuscript.

For each reference the script queries BOTH Crossref (api.crossref.org) and
Europe PMC (ebi.ac.uk) by DOI and classifies the outcome in three, not two, ways:

    MATCH              the service returned a record for that DOI
    NO_MATCH           the service answered normally but has no such DOI
    SERVICE_UNAVAILABLE the request itself failed (network / HTTP / timeout)

The distinction matters: a transient service failure must never be reported as
"the reference does not exist".  The returned title is also compared with the
title printed in the manuscript, so a DOI that resolves to an unrelated paper is
caught even when both services agree the DOI exists.
"""
import io, json, re, sys, time, unicodedata, urllib.request, urllib.error

UA = {'User-Agent': 'K3-refcheck/1.0 (mailto:15511075821@163.com)'}
ONLINE_TRIES = 3


def fetch(url):
    """-> (state, payload).  state in {'OK','SERVICE_UNAVAILABLE'}"""
    last = None
    for _ in range(ONLINE_TRIES):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                return 'OK', json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return 'OK', None            # service answered: no such DOI
            last = 'HTTP %d' % e.code
        except Exception as e:
            last = '%s: %s' % (type(e).__name__, e)
        time.sleep(2)
    return 'SERVICE_UNAVAILABLE', last


def norm(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode()
    s = re.sub(r'[^a-z0-9 ]+', ' ', s.lower())
    return re.sub(r'\s+', ' ', s).strip()


def cw(doi):
    st, d = fetch('https://api.crossref.org/works/' + urllib.parse.quote(doi))
    if st != 'OK':
        return st, None, d
    if d is None:
        return 'NO_MATCH', None, None
    m = d['message']
    return 'MATCH', (m.get('title') or [''])[0], None


def epmc(doi):
    st, d = fetch('https://www.ebi.ac.uk/europepmc/webservices/rest/search?'
                  'query=DOI:%22' + urllib.parse.quote(doi) + '%22&format=json&pageSize=1')
    if st != 'OK':
        return st, None, d
    res = d.get('resultList', {}).get('result', [])
    if not res:
        return 'NO_MATCH', None, None
    r0 = res[0]
    return 'MATCH', r0.get('title', ''), r0.get('pubYear')


# ------------------------------------------------------------------ parse refs
s = io.open('out/manuscript_K3.md', encoding='utf-8').read()
refs_txt = s[s.index('## References'):]
items = re.findall(r'(?m)^(\d{1,2})\.\s+(.+?)(?=\n\d{1,2}\.\s|\Z)', refs_txt, re.S)
print('=== 稿件参考文献：%d 条 ===\n' % len(items))

rows, problems = [], []
for num, body in items:
    body = ' '.join(body.split())
    doi = ''
    m = re.search(r'https?://doi\.org/(\S+)', body)
    if m:
        doi = m.group(1).rstrip('.')
    # 题名：去掉作者段之后、句点之前的第一句
    title = ''
    m2 = re.search(r'\.\s([A-Z][^.]{15,240}?)\.\s', body)
    if m2:
        title = m2.group(1)
    if not doi:
        rows.append((int(num), '(no DOI)', 'N/A', 'N/A', title[:60]))
        problems.append('ref %s 无 DOI' % num)
        continue
    cs, ct, cerr = cw(doi)
    es, et, eyear = epmc(doi)
    flag = []
    if cs == 'SERVICE_UNAVAILABLE':
        flag.append('Crossref 服务不可用(%s)' % cerr)
    elif cs == 'NO_MATCH':
        flag.append('Crossref 查不到该 DOI')
    if es == 'SERVICE_UNAVAILABLE':
        flag.append('EuropePMC 服务不可用(%s)' % eyear)
    elif es == 'NO_MATCH':
        flag.append('EuropePMC 查不到该 DOI')
    if cs == 'MATCH' and es == 'MATCH' and title:
        a, b = norm(ct), norm(title)
        # 允许一定差异：取前 8 个词比较
        if a.split()[:8] != b.split()[:8]:
            flag.append('题名与稿件不一致: Crossref=%r' % ct[:70])
    verdict = 'OK' if not flag else 'CHECK'
    print('[%2s] %-6s %s' % (num, verdict, (title or '')[:68]))
    print('       DOI %s' % doi)
    print('       Crossref: %-9s %s' % (cs, (ct or '')[:66]))
    print('       EuropePMC: %-9s %s (%s)' % (es, (et or '')[:60], eyear))
    for f in flag:
        print('       ⚠ %s' % f)
    print()
    rows.append((int(num), doi, cs, es, title[:60]))
    if flag:
        problems.append('ref %s: %s' % (num, '; '.join(flag)))

print('=' * 70)
n_unavail = sum(1 for r in rows if 'SERVICE_UNAVAILABLE' in (r[2], r[3]))
print('合计 %d 条 | 需核查 %d 条 | 其中含"服务不可用"的 %d 条'
      % (len(rows), len(problems), n_unavail))
for p in problems:
    print('   -', p)
io.open('out/K3_refcheck2.json', 'w', encoding='utf-8').write(
    json.dumps({'rows': rows, 'problems': problems}, ensure_ascii=False, indent=1))
print('\n已写 out/K3_refcheck2.json')
