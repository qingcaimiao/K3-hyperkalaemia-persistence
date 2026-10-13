# -*- coding: utf-8 -*-
"""K3 查新三轨（修正版）：每条检索式对每个字段都写显式字段前缀，避免 (FIELD:a AND b) 的绑定歧义。
区分 NOT-FOUND（服务正常、0 命中）与 SERVICE-ERROR。
"""
import json, time, urllib.request, urllib.parse

HK = '(TITLE:"hyperkalemia" OR TITLE:"hyperkalaemia" OR TITLE:"hyperkalemic" OR TITLE:"hyperkalaemic")'
HKa = '(ABSTRACT:"hyperkalemia" OR ABSTRACT:"hyperkalaemia")'

SETS = [
    ("T1 标题: 高钾 + 心脏ICU",
     '(TITLE:"hyperkalemia" OR TITLE:"hyperkalaemia") AND (TITLE:"cardiac intensive care" OR TITLE:"coronary care unit" OR TITLE:"cardiac ICU" OR TITLE:"cardiac critical care")'),
    ("T2 摘要: 高钾 + 心脏ICU",
     '(ABSTRACT:"hyperkalemia" OR ABSTRACT:"hyperkalaemia") AND (ABSTRACT:"cardiac intensive care" OR ABSTRACT:"coronary care unit" OR ABSTRACT:"cardiac ICU")'),
    ("T3 标题: 高钾 + 一过性/持续性",
     '(TITLE:"hyperkalemia" OR TITLE:"hyperkalaemia") AND (TITLE:"transient" OR TITLE:"persistent" OR TITLE:"sustained")'),
    ("T4 摘要: 高钾 + 一过性/持续性",
     HKa + ' AND (ABSTRACT:"transient" OR ABSTRACT:"persistent" OR ABSTRACT:"sustained")'),
    ("T5 标题: 高钾 + 确认/复查",
     '(TITLE:"hyperkalemia" OR TITLE:"hyperkalaemia") AND (TITLE:"confirmation" OR TITLE:"repeat" OR TITLE:"recheck" OR TITLE:"remission" OR TITLE:"resolution")'),
    ("T6 标题: 血钾轨迹 + 死亡",
     '(TITLE:"potassium") AND (TITLE:"trajectory" OR TITLE:"trajectories" OR TITLE:"variability") AND (TITLE:"mortality" OR TITLE:"outcome")'),
    ("T7 摘要: 血钾轨迹 + 死亡",
     '(ABSTRACT:"potassium" AND (ABSTRACT:"trajectory" OR ABSTRACT:"variability") AND ABSTRACT:"mortality")'),
    ("T8 标题: 阈值定义 + 高钾",
     '(TITLE:"threshold" OR TITLE:"definition") AND (TITLE:"hyperkalemia" OR TITLE:"hyperkalaemia" OR TITLE:"potassium episode")'),
    ("T9 标题: 高钾 + 回落/复常",
     '(TITLE:"hyperkalemia" OR TITLE:"hyperkalaemia") AND (TITLE:"revert" OR TITLE:"reversion" OR TITLE:"resolved" OR TITLE:"resolving")'),
    ("T10 标题: 高钾 + 预后(任一) + 持续/间歇",
     '(TITLE:"hyperkalemia" OR TITLE:"hyperkalaemia") AND (TITLE:"intermittent" OR TITLE:"episodic" OR TITLE:"non-sustained")'),
    ("T11 概念级(全字段): 高钾状态持续性 + 预后",
     '"hyperkalemia" AND ("transient" OR "persistent") AND ("cardiac intensive care" OR "coronary care unit" OR "cardiac ICU") AND "mortality"'),
    ("T12 概念级(全字段): 阈值事件定义 + 高钾 + 复发率",
     '"hyperkalemia" AND ("episode" AND "definition") AND ("confirmation rate" OR "repeat measurement" OR "recurrence")'),
]


def epmc(q, tries=3, timeout=30):
    url = ('https://www.ebi.ac.uk/europepmc/webservices/rest/search?query='
           + urllib.parse.quote(q) + '&format=json&pageSize=30&resultType=lite')
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
for name, q in SETS:
    j, err = epmc(q)
    if j is None:
        print('[%s] SERVICE-ERROR %s' % (name, err)); rows.append(dict(set=name, query=q, hits=None, note='SERVICE-ERROR')); continue
    hits = j.get('hitCount'); res = j.get('resultList', {}).get('result', [])
    note = 'NOT-FOUND (0 hits)' if hits == 0 else 'ok'
    print('\n[%s]  hits=%s  %s' % (name, hits, note))
    samp = []
    for x in res[:8]:
        s = '%s | %s | %s' % ((x.get('title') or '')[:100], (x.get('journalTitle') or '')[:30], x.get('pubYear'))
        samp.append(s); print('    · ' + s)
    rows.append(dict(set=name, query=q, hits=hits, note=note, sample=samp))
    time.sleep(0.5)

json.dump(rows, open('out/k45b_novelty.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n写出 out/k45b_novelty.json')
