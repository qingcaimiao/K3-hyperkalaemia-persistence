# -*- coding: utf-8 -*-
"""K3 数字溯源（全量）：稿件中每个数字是否能在结果文件中找到出处。

做法：把 results/ 下全部 JSON/CSV 的**所有数值**（含嵌套）汇成一个集合，
再逐句提取稿件中的数字做比对。仅输出「找不到出处」的数字，供人工判定。
"""
import io, re, os, json, csv, collections

ROOT = 'D:/桌面/workbuddyzuopin/K3xiangmu'
res_dirs = ['results', os.path.join('K3_repo', 'results'), 'out']   # out/ 含 k60_recomputed.csv（本轮补算落盘）

vals = set()


def add_num(x):
    try:
        f = float(str(x).replace(',', ''))
    except Exception:
        return
    vals.add('%g' % f)                       # 12.30 -> 12.3
    vals.add('%.2f' % f)
    vals.add('%.1f' % f)


def walk(o):
    if isinstance(o, dict):
        for v in o.values():
            walk(v)
    elif isinstance(o, list):
        for v in o:
            walk(v)
    elif isinstance(o, (int, float)):
        add_num(o)
    elif isinstance(o, str):
        for t in re.findall(r'\d[\d,]*(?:\.\d+)?', o):
            add_num(t)


n_files = 0
for d in res_dirs:
    p = os.path.join(ROOT, d)
    if not os.path.isdir(p):
        continue
    for fn in os.listdir(p):
        fp = os.path.join(p, fn)
        try:
            if fn.lower().endswith('.json'):
                walk(json.load(io.open(fp, encoding='utf-8')))
                n_files += 1
            elif fn.lower().endswith('.csv') and (fn.startswith('k60_') or 'results' in d or 'K3_repo' in d):
                with io.open(fp, encoding='utf-8-sig') as fh:
                    for row in csv.DictReader(fh):
                        walk(row)
                n_files += 1
        except Exception as e:
            print('  跳过', fn, repr(e)[:60])
print('已从 %d 个结果文件构建数值源集，共 %d 个不同数值' % (n_files, len(vals)))

# 结构性白名单（非统计量）
STRUCT = set()
for y in range(1990, 2031):
    STRUCT.add(str(y))
for i in range(1, 20):
    STRUCT.add(str(i))
STRUCT |= {'5.5', '5.0', '6.0', '6.5', '0.05', '0.05', '95', '1.96', '2', '4', '6', '12', '24', '48', '72',
           '7', '10', '0.5', '0.25', '2.0', '3.13', '3.1', '2.0', '50971', '400', '1000', '1,000', '5',
           '3', '1', '0', '8', '9', '11', '13', '14', '16', '17', '18', '19', '20', '21', '22', '23', '25',
           '26', '27', '28', '29', '30', '31', '32', '33', '5.9', '1.5', '3.0', '15', '200', '250', '50'}

EN = 'out/manuscript_K3.md'
s = io.open(EN, encoding='utf-8').read()
body = s[s.index('## 1. Introduction'):s.index('## Supplementary Materials')]   # back matter now starts here

missing = collections.defaultdict(list)
for line in body.split('\n'):
    if not line.strip():
        continue
    for t in re.findall(r'\d[\d,]*(?:\.\d+)?', line):
        key = '%g' % float(t.replace(',', '')) if re.match(r'^[\d,]+(\.\d+)?$', t) else t
        if key in vals or t in vals or key in STRUCT or t in STRUCT:
            continue
        missing[key].append(line[:90])

print('\n=== 未在结果文件中找到出处的数字（%d 种）===' % len(missing))
for k in sorted(missing, key=lambda x: (len(x), x)):
    print('  %-12s ×%d ｜ 例：%s' % (k, len(missing[k]), missing[k][0]))

io.open('out/K3_number_trace.md', 'w', encoding='utf-8').write(
    '# K3 数字溯源\n\n源集：%d 个结果文件的全部数值（%d 个）\n\n## 未找到出处（%d 种）\n\n' % (n_files, len(vals), len(missing))
    + '\n'.join('- `%s` ×%d ｜ %s' % (k, len(missing[k]), missing[k][0]) for k in sorted(missing, key=lambda x: (len(x), x)))
    + '\n')
print('\n已写 out/K3_number_trace.md')
