# -*- coding: utf-8 -*-
"""k65: reduce the Chinese-em-dash (——) density in the Chinese companion manuscript.
Each rule is asserted to match exactly once. No quote characters appear in any search
string, so the file's own quotation-mark code points are untouched.
"""
import io, sys

P = 'out/稿件_K3_中文版.md'
s = io.open(P, encoding='utf-8').read()
D = '\u2014\u2014'
before = s.count(D)

# (search, replacement)  -- every search contains exactly one dash pair
RULES = [
 # L33 threshold parenthetical
 ("识别" + D + "最常采用", "识别（最常采用"),
 ("下限[5]" + D + "而阈值的选择", "下限[5]），而阈值的选择"),
 # L57 record level parenthetical
 ("记录层级不同" + D + "MIMIC-IV 在住院记录上", "记录层级不同（MIMIC-IV 在住院记录上"),
 ("挂在 ICU 停留上" + D + "因此我们在两个库中", "挂在 ICU 停留上），因此我们在两个库中"),
 # L63-66 definition list
 ("**一过性**" + D, "**一过性**："),
 ("**间歇**" + D, "**间歇**："),
 ("**持续**" + D, "**持续**："),
 ("**未分类**" + D, "**未分类**："),
 # L78 observed-variability scenario
 ("使用**观察到的**患者内变异" + D + "它同时包含", "使用**观察到的**患者内变异，它同时包含"),
 # L82 landmark rationale
 ("状态分类会被结局决定" + D + "死亡者会被系统性地推向", "状态分类会被结局决定，死亡者会被系统性地推向"),
 # L84 RCV restriction rationale
 ("一个参考变化值以上者" + D + "未越过该幅度的越线", "一个参考变化值以上者，因为未越过该幅度的越线"),
 # L90 treatment categories
 ("我们检索五类治疗" + D + "胰岛素联合葡萄糖", "我们检索五类治疗：胰岛素联合葡萄糖"),
 ("碳酸氢钠与肾脏替代治疗" + D + "若在索引值与复查值之间", "碳酸氢钠与肾脏替代治疗。若在索引值与复查值之间"),
 # L102 measurement frequency
 ("四种状态合计；表 1）" + D + "后文将回到这一点。", "四种状态合计；表 1），后文将回到这一点。"),
 # L104 intermittent episodes
 ("在窗口内再次升高" + D + "这正是我们把它们单列为", "在窗口内再次升高，这正是我们把它们单列为"),
 # L110 transition matrix divergence
 ("（39.0% 对 54.5%）" + D + "这一层正是", "（39.0% 对 54.5%），而这一层正是"),
 # L116 noise parenthetical
 ("视为噪声" + D + "即假设患者真实血钾不变", "视为噪声（即假设患者真实血钾不变"),
 ("只有状态在变" + D + "预期确认率为", "只有状态在变），预期确认率为"),
 # L122 inflated rates
 ("被结构性高估" + D + "死亡患者不可能", "被结构性高估，因为死亡患者不可能"),
 # L130 minimum-measurement reclassification
 ("持续组中的一大部分" + D + "在全队列中", "持续组中的一大部分，因为全队列中"),
 ("仅凭一次复查值成立" + D + "但在每个数据库", "仅凭一次复查值成立。但在每个数据库"),
 # L146 exclusion of truncated episodes
 ("等价于把它们全部归入未分类" + D + "被截断者", "等价于把它们全部归入未分类：被截断者"),
 # L148 fixed exposure window
 ("才首次升高的事件" + D + "72 小时 landmark 下 MIMIC-IV 为 642 例中的 211 例", "才首次升高的事件：72 小时 landmark 下 MIMIC-IV 为 642 例中的 211 例"),
 ("（35.5%）" + D + "因此固定窗下间歇事件稀少", "（35.5%）。因此固定窗下间歇事件稀少"),
 # L156 stratum-specific estimates (also removes an unmatched closing parenthesis)
 ("；表 S7）" + D + "为完整性列出，不作解释）。", "；表 S7），为完整性列出，不作解释。"),
 # L156 E-value
 ("**15.5 与 10.6**" + D + "即某一个未测混杂", "**15.5 与 10.6**，即某一个未测混杂"),
 # L166 artefact reading
 ("正确反应是忽略该结果" + D + "关于假性高钾", "正确反应是忽略该结果；关于假性高钾"),
 # L168 monotonic gradient
 ("在四项独立分析中单调一致" + D + "两个数据库 × 两种 landmark 定义，且", "在四项独立分析中单调一致（两个数据库 × 两种 landmark 定义），且"),
 ("与 0.35%" + D + "**而被剔除的一过性事件并非低风险事件**。", "与 0.35%，**而被剔除的一过性事件并非低风险事件**。"),
 # L170 choice of target
 ("还是持续状态" + D + "这一选择应当被明确作出。", "还是持续状态，而这一选择应当被明确作出。"),
 # L172 persistent state robustness list
 ("由**持续状态**承载" + D + "在我们考察的每一种口径下它都与死亡相关（", "由**持续状态**承载，在我们考察的每一种口径下它都与死亡相关（"),
 # L174 cost of the rule
 ("不到五次复查" + D + "在其中一个数据库中不到三次" + D + "即可识别 1 例已确认事件。", "不到五次复查（在其中一个数据库中不到三次）即可识别 1 例已确认事件。"),
 # L174 non-random subset
 ("未被复查者不是随机子集" + D + "在本队列中", "未被复查者不是随机子集：在本队列中"),
 # L178 ascertainment
 ("24 小时后有测量" + D + "在此之前死亡或转出者按设计被排除。", "24 小时后有测量，因此在此之前死亡或转出者按设计被排除。"),
 # L182 treatment recording
 ("（762 例中 31 例）" + D + "差距反映的是", "（762 例中 31 例），差距反映的是"),
 # L182 treatment does not explain reversion
 ("治疗并未解释回落" + D + "MIMIC-IV 中有治疗记录者", "治疗并未解释回落：MIMIC-IV 中有治疗记录者"),
 ("（29.0% 对 30.8%）" + D + "因此在记录所及的范围内", "（29.0% 对 30.8%），因此在记录所及的范围内"),
]

errs = []
for i, (o, n) in enumerate(RULES, 1):
    c = s.count(o)
    if c != 1:
        errs.append(f"  rule {i}: matched {c} times -> {o[:60]!r}")
        continue
    s = s.replace(o, n, 1)
if errs:
    print("ABORT:"); print('\n'.join(errs)); sys.exit(1)

after = s.count(D)
print(f"Chinese em dashes: {before} -> {after}   (rules applied: {len(RULES)})")
if after:
    for i, l in enumerate(s.split('\n'), 1):
        if D in l:
            print(f"  residual L{i}: {l.strip()[:120]}")
assert after == 0, "not all dashes were removed"

# parentheses must balance
op, cl = s.count('（'), s.count('）')
print(f"full-width parentheses: open {op} / close {cl}  -> {'balanced' if op == cl else 'UNBALANCED'}")
io.open(P, 'w', encoding='utf-8').write(s)
print("written:", P)
