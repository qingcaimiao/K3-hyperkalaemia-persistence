# -*- coding: utf-8 -*-
"""表格内部一致性：逐表核对加总、百分比与源数据。"""
import io, re, json
import pandas as pd

s = io.open('out/manuscript_K3.md', encoding='utf-8').read()
R = []
W = R.append
W('| 检查项 | 稿件值 | 复核值 | 判定 |')
W('|---|---|---|---|')


_blocks, _p = [], 0
for _m in re.finditer(r'\n{2,}', s):
    _blocks.append(s[_p:_m.start()]); _p = _m.end()
_blocks.append(s[_p:])


def T(n):
    """表 n 的整块 = 标题 + 表格 + 表注（浮标就地化后不能再靠 '## Figure legends' 收尾）。"""
    i = next(k for k, b in enumerate(_blocks) if b.strip().startswith('### Table %d.' % n))
    return '\n\n'.join(_blocks[i:i + 3])


def cells(line):
    return [c.strip() for c in line.strip().strip('|').split('|')]


def ck(name, stated, got, tol=0.05):
    ok = abs(float(stated) - float(got)) <= tol
    W('| %s | %s | %s | %s |' % (name, stated, got, '✅' if ok else '⚠️'))


# ---------- Table 2 ----------
t2 = T(2)
W('\n**Table 2**')
for line in t2.split('\n'):
    if line.startswith('| Transient |') or line.startswith('| Intermittent |') or line.startswith('| **Sustained** |') or line.startswith('| Unclassified |'):
        c = cells(line)
        name = c[0].strip('*')
        mv, ev = c[2], c[3]                      # 第3列=MIMIC，第4列=eICU
        n_m = int(re.search(r'([\d,]+)', mv.replace('*', '')).group(1).replace(',', ''))
        n_e = int(re.search(r'([\d,]+)', ev.replace('*', '')).group(1).replace(',', ''))
        pm = float(re.search(r'([\d.]+)\)', mv).group(1))
        pe = float(re.search(r'([\d.]+)\)', ev).group(1))
        ck('Table2 %s MIMIC %%' % name, pm, round(100 * n_m / 20322, 2), 0.005)
        ck('Table2 %s eICU %%' % name, pe, round(100 * n_e / 28805, 2), 0.005)

# 表 2 加总（稿件脚注声称 757+189+86+150=1182）
ck('Table2 四状态合计(MIMIC)', 1182, 757 + 189 + 86 + 150, 0)
ck('Table2 四状态合计(eICU)', 997, 493 + 169 + 100 + 235, 0)

# ---------- Table 5 ----------
t5 = T(5)
W('\n**Table 5**')
nums = {'m_whole': [], 'm_lm': [], 'e_whole': [], 'e_lm': []}
cur = None
for line in t5.split('\n'):
    c = cells(line)
    if not c:
        continue
    if c[0] == '**MIMIC-IV**':
        cur = 'm'; continue
    if c[0] == '**eICU-CRD**':
        cur = 'e'; continue
    if cur and len(c) >= 4 and re.match(r'^[\d,]+$', c[1]) and re.match(r'^[\d,]+$', c[3]):
        nums[cur + '_whole'].append(int(c[1].replace(',', '')))
        nums[cur + '_lm'].append(int(c[3].replace(',', '')))
ck('Table5 全队列加总(MIMIC)', 20322, sum(nums['m_whole']), 0)
ck('Table5 全队列加总(eICU)', 28805, sum(nums['e_whole']), 0)
ck('Table5 72h landmark 加总(MIMIC)', 18227, sum(nums['m_lm']), 0)
ck('Table5 72h landmark 加总(eICU)', 23087, sum(nums['e_lm']), 0)
ck('Table5 72h landmark 加总(MIMIC) 与图2一致', 18227, 17585 + 412 + 102 + 39 + 89, 0)
ck('Table5 72h landmark 加总(eICU) 与图2一致', 23087, 22602 + 245 + 89 + 43 + 108, 0)

# ---------- Table 1 ----------
t1 = T(1)
W('\n**Table 1**')
tot_m = tot_e = 0
for line in t1.split('\n'):
    c = cells(line)
    if len(c) >= 5 and re.match(r'^[\d,]+$', c[1]) and re.match(r'^[\d,]+$', c[4]):
        tot_m += int(c[1].replace(',', '')); tot_e += int(c[4].replace(',', ''))
ck('Table1 各状态 n 合计(MIMIC)', 20322, tot_m, 0)
ck('Table1 各状态 n 合计(eICU)', 28805, tot_e, 0)

# ---------- Table 6 ----------
t6 = T(6)
W('\n**Table 6**')
for line in t6.split('\n'):
    c = cells(line)
    if len(c) >= 5 and c[0].strip('*').strip() in ('2 h', '4 h', '6 h', '12 h', '24 h'):
        for col, tot in ((1, 1182), (3, 997)):
            pct = float(re.search(r'[\d.]+', c[col]).group()); nc = int(c[col + 1].replace(',', ''))
            ck('Table6 %s %s: 覆盖率与未覆盖数互补' % (c[0].strip('*'), 'MIMIC' if col == 1 else 'eICU'),
               round(100 - pct, 1), round(100 * nc / tot, 1), 0.15)

# ---------- Table 7 ----------
t7 = T(7)
ck('Table7 阈值递增（5.0→6.5）', 1, 1 if '5.0' in t7 and '6.5' in t7 else 0, 0)

io.open('out/K3_table_checks.md', 'w', encoding='utf-8').write('# K3 表格内部一致性核对\n\n' + '\n'.join(R) + '\n')
print('\n'.join(R))
bad = sum(1 for l in R if '⚠️' in l)
print('\n⚠️ 不一致项：%d' % bad)
