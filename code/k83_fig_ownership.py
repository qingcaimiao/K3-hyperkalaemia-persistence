# -*- coding: utf-8 -*-
"""k83: settle figure ownership (one script per figure) and restore Figure 5.

Ownership after this script:
  Figure 1 -> k78_fig1_redo.py      Figure 2 -> k41b_fig_flow.py
  Figure 3 -> k70_fig3_fix.py       Figure 4 -> k68_fig_fixes.py
  Figure 5 -> k46_figs_redo.py      Figure 6 -> k62_fig_rule_redo.py

k46 keeps only its forest figure (it draws the current Transient/Intermittent/
Sustained states from out/k39_or.json) and now skips its stale Figure 1.
k37 no longer owns any figure and is refused outright.
"""
import io, shutil, os, sys

NL = '\r\n'
fails = []
GUARD = ("import os as _os" + NL +
         "if not _os.environ.get('K3_ALLOW_STALE_FIG'):" + NL +
         "    print('  [skip] {fig} 现由 {owner} 生成，本脚本默认不再写出（设 K3_ALLOW_STALE_FIG=1 可强制）')" + NL +
         "else:" + NL +
         "    {save}" + NL +
         "plt.close(fig)")


def read(p):
    return io.open(p, encoding='utf-8', newline='').read()


def write(p, s):
    io.open(p, 'w', encoding='utf-8', newline='').write(s)


def sub(s, old, new, tag):
    n = s.count(old)
    if n != 1:
        fails.append('%s: 预期 1 处，实为 %d' % (tag, n))
        return s
    print('  ok  %s' % tag)
    return s.replace(old, new, 1)


# ---------------------------------------------------------- 1) restore the correct Figure 5
src = 'D:/桌面/workbuddyzuopin/K3xiangmu/figures/FigK3_5_forest.png'
if not os.path.exists(src):
    fails.append('找不到正确的 Figure 5 备份')
else:
    shutil.copy(src, 'out/figures_k3/FigK3_5_forest.png')
    print('  ok  已从交付文件夹恢复 Figure 5（k46 生成的正源版本）')

# ---------------------------------------------------------- 2) k46: drop the blanket refusal
s = read('k46_figs_redo.py')
i = s.find('raise SystemExit(')
if i != -1:
    j = s.index(')', s.index("本脚本不再运行。", i)) + 1
    s = s[:i] + s[j:]
    s = s.replace(NL + NL + NL, NL + NL)
    print('  ok  k46 已撤销整脚本弃用')
else:
    print('  --  k46 无可撤销的 raise')

s = sub(s,
        "fig.tight_layout(); fig.savefig(OUT + '/FigK3_1_definition.png', bbox_inches='tight'); plt.close(fig)",
        GUARD.format(fig='Figure 1（含硬编码 3.72 的旧版）', owner='k78_fig1_redo.py',
                     save="fig.tight_layout(); fig.savefig(OUT + '/FigK3_1_definition.png', bbox_inches='tight')"),
        'k46 Figure 1 跳过')
s = sub(s, "fig.savefig(OUT + '/FigK3_4_forest.png', bbox_inches='tight')",
        "fig.savefig(OUT + '/FigK3_5_forest.png', bbox_inches='tight')   # 重编号后的新名",
        'k46 森林图改用新文件名')
s = sub(s, "print('重绘完成：FigK3_1_definition.png, FigK3_4_forest.png')",
        "print('写出 out/figures_k3/FigK3_5_forest.png（Figure 5，重编号后的新名）')",
        'k46 打印信息')
write('k46_figs_redo.py', s)

# ---------------------------------------------------------- 3) k37: no owned figure left
if not os.path.exists('out/_bak_k37_figs_k3.py'):
    fails.append('缺少 k37 备份')
else:
    s = read('out/_bak_k37_figs_k3.py')
    pos = s.index('from matplotlib.patches')
    end = s.index(NL, pos) + len(NL)
    refusal = (NL + NL + 'raise SystemExit(' + NL +
               "    '[已弃用] k37_figs_k3.py 的各张图都已有专属且更新的脚本：'\n" +
               "    'Figure 1 -> k78_fig1_redo.py、Figure 3 -> k70_fig3_fix.py、'\n" +
               "    'Figure 4 -> k68_fig_fixes.py、Figure 5 -> k46_figs_redo.py、'\n" +
               "    'Figure 6 -> k62_fig_rule_redo.py。本脚本不再运行。')" + NL)
    write('k37_figs_k3.py', s[:end] + refusal + s[end:])
    print('  ok  k37 已整体弃用（不再拥有任何图）')

if fails:
    print('ABORT:'); [print('  -', f) for f in fails]; sys.exit(1)
print('\n完成')
