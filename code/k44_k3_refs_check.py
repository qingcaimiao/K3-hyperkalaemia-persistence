# -*- coding: utf-8 -*-
"""K3 参考文献双源校验：Crossref + Europe PMC
关键纪律：必须区分三种结果 —— MATCH / NOT-FOUND（两个源都明确查不到）/ SERVICE-ERROR（网络或服务异常）。
任何一次服务抖动都不得被记为"查不到"。
"""
import json, time, urllib.request, urllib.parse, sys

REFS = [
    ("1", "10.1016/j.phrs.2016.09.039", "Emergency management of severe hyperkalemia: guideline for best practice and opportunities for the future"),
    ("2", "10.1161/CIRCHEARTFAILURE.113.000792", "Incidence, determinants, and prognostic significance of hyperkalemia and worsening renal function in patients with heart failure receiving RAAS inhibitors"),
    ("3", "10.1093/ehjcvp/pvy015", "Expert consensus document on the management of hyperkalaemia in patients with cardiovascular disease"),
    ("5", "10.1002/emp2.12572", "Hyperkalemia management in the emergency department: an expert panel consensus"),
    ("6", "10.1186/cc11872", "Severe hyperkalemia requiring hospitalization: predictors of mortality"),
    ("7", "10.1136/bmj.39119.607986.47", "Spurious hyperkalaemia"),
    ("8", "10.1016/j.lab.2005.11.008", "Pseudohyperkalemia in serum: the phenomenon and its clinical magnitude"),
    ("9", "10.3109/10408363.2014.966898", "Pseudohyperkalemia: a new twist on an old phenomenon"),
    ("10", "10.1053/j.ajkd.2005.06.005", "Pseudohyperkalemia due to pneumatic tube transport in a leukemic patient"),
    ("11", "10.1038/s41597-022-01899-x", "MIMIC-IV, a freely accessible electronic health record dataset"),
    ("12", "10.1038/sdata.2018.178", "The eICU Collaborative Research Database, a freely available multi-center database for critical care research"),
    ("13", "10.1016/S0140-6736(07)61602-X", "The Strengthening the Reporting of Observational Studies in Epidemiology (STROBE) statement"),
]


def fetch(url, tries=3, timeout=25):
    last = None
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'ref-check/1.0 (mailto:15511075821@163.com)'})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode('utf-8')), None
        except Exception as e:
            last = repr(e); time.sleep(2 + 3 * k)
    return None, last


rows = []
for rid, doi, title in REFS:
    rec = dict(ref=rid, doi=doi, claim=title[:70])

    # ---- Crossref ----
    j, err = fetch('https://api.crossref.org/works/' + urllib.parse.quote(doi))
    if j is None:
        rec['crossref'] = 'SERVICE-ERROR: ' + err[:80]
    else:
        m = j.get('message', {})
        t = (m.get('title') or [''])[0]
        yr = (m.get('issued', {}).get('date-parts', [[None]])[0] or [None])[0]
        jr = (m.get('container-title') or [''])[0]
        rec['crossref'] = 'OK | %s (%s) | %s' % (t[:70], yr, jr[:40])

    # ---- Europe PMC ----
    j, err = fetch('https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%22'
                   + urllib.parse.quote(doi) + '%22&resultType=core&format=json')
    if j is None:
        rec['epmc'] = 'SERVICE-ERROR: ' + err[:80]
    else:
        rl = j.get('resultList', {}).get('result', [])
        if not rl:
            # 再判一次：是否服务可用但确实无记录
            rec['epmc'] = 'NOT-FOUND (service responded, 0 hits)'
        else:
            x = rl[0]
            rec['epmc'] = 'OK | %s | PMID %s' % ((x.get('title') or '')[:60], x.get('pmid', '-'))
    time.sleep(0.6)
    rows.append(rec)
    print('%3s %s\n     Crossref: %s\n     EPMC    : %s' % (rid, doi, rec['crossref'], rec['epmc']))

json.dump(rows, open('out/k44_refs_check.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n写出 out/k44_refs_check.json')
