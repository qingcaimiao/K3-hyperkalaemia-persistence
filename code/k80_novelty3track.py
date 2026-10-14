# -*- coding: utf-8 -*-
"""k80: three-track novelty search for K3.

Track A  concept level : free text, NO field prefix  -> searches all fields
Track B  abstract level: every term carries an explicit ABSTRACT: prefix
Track C  title level   : every term carries an explicit TITLE: prefix

Why explicit prefixes matter: in Europe PMC a field prefix binds only to the term
that immediately follows it, so '(ABSTRACT:a AND b)' silently searches b in all
fields.  Every term is therefore prefixed individually.

Each query is classified as OK (service answered) or SERVICE_UNAVAILABLE, so a
0-hit result is never produced by a service hiccup.  For every query the top hits
are printed so that a collision can be judged rather than merely counted.
"""
import json, time, urllib.request, urllib.parse

HK_T = '(TITLE:"hyperkalemia" OR TITLE:"hyperkalaemia" OR TITLE:"hyperkalemic" OR TITLE:"hyperkalaemic")'
HK_A = '(ABSTRACT:"hyperkalemia" OR ABSTRACT:"hyperkalaemia" OR ABSTRACT:"hyperkalemic" OR ABSTRACT:"hyperkalaemic")'
HK_C = '("hyperkalemia" OR "hyperkalaemia" OR "hyperkalemic" OR "hyperkalaemic")'

QUERIES = [
    # ---------------- Track A: concept level, all fields ----------------
    ('A1 concept', 'highK + persistence + cardiac ICU',
     HK_C + ' AND ("persistent" OR "persistence" OR "transient") AND ("cardiac intensive care" OR "coronary care unit" OR "cardiac ICU")'),
    ('A2 concept', 'highK + episode + transient/persistent + death',
     HK_C + ' AND "episode" AND ("transient" OR "persistent") AND ("mortality" OR "death")'),
    ('A3 concept', 'threshold value + highK + repeat measurement/confirmation',
     HK_C + ' AND ("single threshold" OR "threshold value" OR "single value") AND ("repeat measurement" OR "confirmation" OR "repeat sample")'),
    ('A4 concept', 'highK + episode/outcome definition',
     HK_C + ' AND ("episode definition" OR "outcome definition" OR "case definition")'),
    ('A5 concept', 'potassium + within-patient variability + ICU',
     '"potassium" AND ("within-patient variability" OR "biological variation" OR "reference change value") AND ("intensive care" OR "critically ill")'),
    ('A6 concept', 'spurious hyperkalaemia + confirmation rate',
     '("pseudohyperkalemia" OR "pseudohyperkalaemia" OR "spurious hyperkalaemia") AND ("confirmation" OR "repeat" OR "artefact" OR "artifact")'),
    ('A7 concept', 'how often does an elevated potassium persist / resolve',
     HK_C + ' AND ("resolves" OR "resolved" OR "reverts" OR "reversion" OR "normalises" OR "normalizes") AND ("next measurement" OR "repeat measurement" OR "subsequent measurement")'),

    # ---------------- Track B: abstract level ----------------
    ('B1 abstract', 'highK + persistent/transient (abstract)',
     HK_A + ' AND (ABSTRACT:"persistent" OR ABSTRACT:"persistence" OR ABSTRACT:"transient" OR ABSTRACT:"sustained")'),
    ('B2 abstract', 'highK + cardiac ICU (abstract)',
     HK_A + ' AND (ABSTRACT:"cardiac intensive care" OR ABSTRACT:"coronary care unit" OR ABSTRACT:"cardiac ICU")'),
    ('B3 abstract', 'highK + repeat measurement/confirmed (abstract)',
     HK_A + ' AND (ABSTRACT:"repeat measurement" OR ABSTRACT:"confirmed" OR ABSTRACT:"confirmation" OR ABSTRACT:"re-measured")'),
    ('B4 abstract', 'potassium + trajectory/variability + mortality (abstract)',
     '(ABSTRACT:"potassium" AND (ABSTRACT:"trajectory" OR ABSTRACT:"variability" OR ABSTRACT:"fluctuation") AND ABSTRACT:"mortality")'),
    ('B5 abstract', 'highK + episode + definition/threshold (abstract)',
     HK_A + ' AND ABSTRACT:"episode" AND (ABSTRACT:"definition" OR ABSTRACT:"threshold")'),

    # ---------------- Track C: title level ----------------
    ('C1 title', 'highK + persistent/transient (title)',
     HK_T + ' AND (TITLE:"persistent" OR TITLE:"persistence" OR TITLE:"transient" OR TITLE:"sustained")'),
    ('C2 title', 'highK + cardiac ICU (title)',
     HK_T + ' AND (TITLE:"cardiac intensive care" OR TITLE:"coronary care unit" OR TITLE:"cardiac ICU")'),
    ('C3 title', 'highK + definition/threshold/confirmation (title)',
     HK_T + ' AND (TITLE:"definition" OR TITLE:"threshold" OR TITLE:"confirmation" OR TITLE:"confirm")'),
    ('C4 title', 'potassium + trajectory/variability + mortality (title)',
     '(TITLE:"potassium" AND (TITLE:"trajectory" OR TITLE:"trajectories" OR TITLE:"variability") AND (TITLE:"mortality" OR TITLE:"outcome" OR TITLE:"prognosis"))'),
    ('C5 title', 'episode persistence/definition (title, no drug name)',
     '(TITLE:"episode" OR TITLE:"episodes") AND (TITLE:"persistent" OR TITLE:"persistence" OR TITLE:"transient") AND (TITLE:"potassium" OR TITLE:"electrolyte")'),
]


def epmc(q, tries=3, timeout=30):
    url = ('https://www.ebi.ac.uk/europepmc/webservices/rest/search?query='
           + urllib.parse.quote(q) + '&format=json&pageSize=5&resultType=lite')
    for _ in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'K3-novelty/1.0'})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return 'OK', json.loads(r.read())
        except Exception as e:
            last = '%s: %s' % (type(e).__name__, e)
            time.sleep(2)
    return 'SERVICE_UNAVAILABLE', last


out = []
for track, desc, q in QUERIES:
    st, d = epmc(q)
    if st != 'OK':
        print('[%s] %s\n    SERVICE_UNAVAILABLE (%s)  <- 不能当作 0 命中\n' % (track, desc, d))
        out.append({'track': track, 'desc': desc, 'query': q, 'state': st, 'hits': None, 'top': []})
        continue
    n = d.get('hitCount', 0)
    hits = d.get('resultList', {}).get('result', [])
    print('[%s] %-46s hits=%d' % (track, desc, n))
    tops = []
    for h in hits[:4]:
        t = (h.get('title') or '').rstrip('.')
        tops.append({'title': t, 'journal': h.get('journalTitle', ''), 'year': h.get('pubYear', '')})
        print('        - %s | %s %s' % (t[:96], h.get('journalTitle', '')[:28], h.get('pubYear', '')))
    print()
    out.append({'track': track, 'desc': desc, 'query': q, 'state': 'OK', 'hits': n, 'top': tops})

json.dump(out, open('out/K3_novelty3track.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('=' * 78)
for tr in ('A concept', 'B abstract', 'C title'):
    sub = [o for o in out if o['track'].startswith(tr[0])]
    bad = [o for o in sub if o['state'] != 'OK']
    tot = [o['hits'] for o in sub if o['hits'] is not None]
    print('%-11s 查询 %d 条 | 命中数 %s | 服务异常 %d'
          % (tr, len(sub), tot, len(bad)))
print('\n已写 out/K3_novelty3track.json')
