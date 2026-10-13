# -*- coding: utf-8 -*-
"""① 查清三篇最接近的前作做到哪一步  ② 查清建模所需化验项在两库的映射"""
import urllib.request, urllib.parse, json, time, warnings
import duckdb, pandas as pd
warnings.filterwarnings('ignore')

M = 'D:/shujuku/mimic-iv-3.1'
E = 'D:/shujuku/EICU 2.0'
T = lambda p: "read_csv_auto('{}', strict_mode=false, ignore_errors=true)".format(p)

def epmc(q, n=2):
    for _ in range(3):
        try:
            u = ('https://www.ebi.ac.uk/europepmc/webservices/rest/search?'
                 + urllib.parse.urlencode({'query': q, 'format': 'json',
                                           'pageSize': n, 'resultType': 'core'}))
            d = json.load(urllib.request.urlopen(
                urllib.request.Request(u, headers={'User-Agent': 'k/1.0'}), timeout=45))
            return d.get('resultList', {}).get('result', [])
        except Exception:
            time.sleep(1.5)
    return []

print('=' * 104)
print('① 关键前作核实（做到哪一步 / 什么人群 / 用什么数据）')
print('=' * 104)
for tag, q in [
    ('T1 Diagnostics 2023 · ML预测ICU钾/酸碱失衡', 'TITLE:"Prediction of Acid-Base and Potassium Imbalances in Intensive Care Patients Using Machine Learning"'),
    ('T2 Medicine 2024 · 可解释ML早期预后', 'TITLE:"Development and Validation of an Interpretable Machine Learning Model for Early Prognosis" AND TITLE:"Potassium"'),
    ('T3 Sci Rep 2025 · 危重患者高钾与短期中期死亡', 'TITLE:"Hyperkalemia is associated with short- and mid-term mortalities in critically ill patients"'),
]:
    print('-' * 104)
    print(f'[{tag}]')
    rs = epmc(q)
    if not rs:
        print('   ⚠️ 未检索到（可能标题略异）')
    for x in rs:
        print('  TITLE  :', x.get('title'))
        print('  JOURNAL:', (x.get('journalInfo', {}).get('journal', {}) or {}).get('title'),
              x.get('pubYear'), '| DOI', x.get('doi'), '| PMID', x.get('pmid'))
        a = (x.get('abstractText') or 'NO ABSTRACT')
        print('  ABSTRACT:', a[:1600].replace('\n', ' '))
        print()

print()
print('=' * 104)
print('② 化验项映射：MIMIC d_labitems（Blood / Chemistry）')
print('=' * 104)
con = duckdb.connect(); con.execute('SET threads=6')
print(con.execute(f"""
  SELECT itemid, label, fluid, category
  FROM {T(M + '/hosp/d_labitems.csv')}
  WHERE fluid = 'Blood' AND category = 'Chemistry'
    AND regexp_matches(lower(label),
      '^(potassium|sodium|chloride|bicarbonate|creatinine|urea nitrogen|glucose|calcium, total|albumin|magnesium|phosphate|anion gap|estimated gfr)')
  ORDER BY label
""").df().to_string(index=False))

print()
print('=' * 104)
print('③ 化验项映射：eICU lab.labname（心脏 ICU 内出现的项目）')
print('=' * 104)
print(con.execute(f"""
WITH cicu AS (
  SELECT patientunitstayid FROM {T(E + '/patient.csv')}
  WHERE regexp_matches(unittype, 'Cardiac ICU|CCU|CSICU|CTICU')
)
SELECT l.labname, COUNT(*) AS n, COUNT(DISTINCT l.patientunitstayid) AS n_stay
FROM {T(E + '/lab.csv')} l JOIN cicu USING (patientunitstayid)
WHERE regexp_matches(lower(l.labname),
  'potassium|sodium|chloride|bicarbonate|creatinine|BUN|glucose|calcium|albumin|magnesium|phosphate|anion gap|GFR|eGFR')
  AND l.labresult IS NOT NULL
GROUP BY 1 ORDER BY n_stay DESC LIMIT 40
""").df().to_string(index=False))

print()
print('=' * 104)
print('④ MIMIC 心脏 ICU：多化验项可用人数（首 24h 内）')
print('=' * 104)
print(con.execute(f"""
WITH cicu AS (
  SELECT stay_id, subject_id, hadm_id, intime FROM {T(M + '/icu/icustays.csv')}
  WHERE regexp_matches(first_careunit, 'CCU|CVICU') OR regexp_matches(last_careunit, 'CCU|CVICU')
),
lb AS (
  SELECT c.stay_id, l.itemid, COUNT(*) AS n
  FROM cicu c JOIN {T(M + '/hosp/labevents.csv')} l
    ON l.subject_id = c.subject_id AND l.hadm_id = c.hadm_id
  WHERE l.valuenum IS NOT NULL
    AND l.charttime >= c.intime AND l.charttime <= c.intime + INTERVAL 24 HOUR
    AND l.itemid IN (50971,50983,50902,50882,50912,51006,50931,50893,50862,50960,50970,50863)
  GROUP BY 1,2
)
SELECT itemid, COUNT(*) AS n_stay FROM lb GROUP BY 1 ORDER BY n_stay DESC
""").df().to_string(index=False))

print('\n完成。')
