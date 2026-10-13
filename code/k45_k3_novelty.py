# -*- coding: utf-8 -*-
"""K3 查新三轨检索（Europe PMC）：
  轨1 概念级（全字段） / 轨2 摘要级 / 轨3 标题级
纪律：区分 NOT-FOUND（服务正常、0 命中）与 SERVICE-ERROR；标题级低命中一律做宽措辞复核。
"""
import json, time, urllib.request, urllib.parse

CONCEPTS = {
    "A. 持续 vs 一过性高钾": '("persistent hyperkalemia" OR "sustained hyperkalemia" OR "transient hyperkalemia" OR "persistent hyperkalaemia" OR "transient hyperkalaemia")',
    "B. 高钾确认/复查":     '("confirmed hyperkalemia" OR "confirmation of hyperkalemia" OR "repeat potassium" OR "repeat measurement" AND hyperkal*)',
    "C. 高钾回落/复常":     '("resolution of hyperkalemia" OR "reversion of hyperkalemia" OR "hyperkalemia resolved" OR "hyperkalemia resolution")',
    "D. 阈值定义事件":       '("threshold-defined" AND (hyperkal* OR potassium)) OR ("episode definition" AND hyperkal*)',
    "E. 血钾短期变异":       '("potassium variability" OR "within-patient variability" AND potassium OR "biological variation" AND potassium)',
    "F. 心脏ICU + 高钾":     '(hyperkal* AND ("cardiac intensive care" OR "coronary care unit" OR "cardiac ICU"))',
    "G. 高钾 + 血钾轨迹":    '(hyperkal* AND ("trajectory" OR "trajectories") AND potassium)',
    "H. 高钾 + 预后分层":    '(hyperkal* AND ("prognostic" OR "outcome") AND ("transient" OR "persistent") AND potassium)',
}


def epmc(q, tries=3, timeout=30):
    url = ('https://www.ebi.ac.uk/europepmc/webservices/rest/search?query='
           + urllib.parse.quote(q) + '&format=json&pageSize=25&resultType=lite')
    last = None
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'novelty/1.0 (mailto:15511075821@163.com)'})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode('utf-8')), None
        except Exception as e:
            last = repr(e); time.sleep(2 + 3 * k)
    return None, last


rows = []
for name, core in CONCEPTS.items():
    tracks = [('concept', core),
              ('abstract', core.replace('(', '(ABSTRACT:', 1).rstrip(')') + ')'),
              ('title', core.replace('(', '(TITLE:', 1).rstrip(')') + ')')]
    for tname, q in tracks:
        j, err = epmc(q)
        if j is None:
            hit, note, sample = None, 'SERVICE-ERROR: ' + err[:70], []
        else:
            hit = j.get('hitCount')
            sample = [(x.get('title') or '')[:95] + ' | ' + (x.get('journalTitle') or '')[:28]
                      + ' | ' + str(x.get('pubYear')) for x in j.get('resultList', {}).get('result', [])[:5]]
            note = 'NOT-FOUND' if hit == 0 else 'ok'
        rows.append(dict(concept=name, track=tname, query=q, hits=hit, note=note, sample=sample))
        print('[%s | %s] hits=%s %s' % (name, tname, hit, note))
        for s in sample[:3]:
            print('      · ' + s)
        time.sleep(0.5)

json.dump(rows, open('out/k45_novelty.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n写出 out/k45_novelty.json')
