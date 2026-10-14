# -*- coding: utf-8 -*-
"""k82: repair the figure-script guards (the previous heredoc mangled '\\n').

End state wanted:
  Figure 1  -> k78_fig1_redo.py   (k37, k68 skip; k46 refused)
  Figure 2  -> k41b_fig_flow.py
  Figure 3  -> k70_fig3_fix.py    (k37 skips; k46b refused)
  Figure 4  -> k68_fig_fixes.py   (k37 skips its obsolete-name version)
  Figure 5  -> k37_figs_k3.py     (filename corrected to the post-renumbering name)
  Figure 6  -> k62_fig_rule_redo.py / k37
Files are CRLF, so all inserted text uses CRLF as well.
"""
import io, shutil, sys

NL = '\r\n'
fails = []


def read(p):
    return io.open(p, encoding='utf-8', newline='').read()


def write(p, s):
    io.open(p, 'w', encoding='utf-8', newline='').write(s)


def guard(fig, owner, save, nl=NL):
    return (
        'import os as _os' + nl
        + "if _os.environ.get('K3_ALLOW_STALE_FIG'):" + nl
        + '    ' + save + nl
        + 'else:' + nl
        + "    print('  [skip] " + fig + " 现由 " + owner + " 生成，本脚本默认不再写出（设 K3_ALLOW_STALE_FIG=1 可强制）')" + nl
        + 'plt.close(fig)'
    )


def sub(s, old, new, tag):
    n = s.count(old)
    if n != 1:
        fails.append('%s: 预期 1 处，实为 %d' % (tag, n))
        return s
    print('  ok  %s' % tag)
    return s.replace(old, new, 1)


# ---------------------------------------------------------------- k37 (restored from backup)
s = read('k37_figs_k3.py')
if 'K3_ALLOW_STALE_FIG' in s:
    fails.append('k37: 已含 guard，请先回滚')
else:
    s = sub(s, "fig.tight_layout(); fig.savefig(OUT + '/FigK3_1_definition.png', bbox_inches='tight'); plt.close(fig)",
            guard('Figure 1', 'k78_fig1_redo.py',
                  "fig.tight_layout(); fig.savefig(OUT + '/FigK3_1_definition.png', bbox_inches='tight')"),
            'k37 Fig1 guard')
    s = sub(s, "fig.savefig(OUT + '/FigK3_2_transition.png', bbox_inches='tight'); plt.close(fig)",
            guard('Figure 4（旧名）', 'k68_fig_fixes.py（新名 FigK3_4_transition）',
                  "fig.savefig(OUT + '/FigK3_2_transition.png', bbox_inches='tight')"),
            'k37 FigK3_2_transition guard')
    s = sub(s, "fig.tight_layout(); fig.savefig(OUT + '/FigK3_3_variability.png', bbox_inches='tight'); plt.close(fig)",
            guard('Figure 3', 'k70_fig3_fix.py',
                  "fig.tight_layout(); fig.savefig(OUT + '/FigK3_3_variability.png', bbox_inches='tight')"),
            'k37 Fig3 guard')
    s = sub(s, "fig.savefig(OUT + '/FigK3_4_forest.png', bbox_inches='tight')",
            "fig.savefig(OUT + '/FigK3_5_forest.png', bbox_inches='tight')   # 重编号后的新名",
            'k37 森林图改名 FigK3_5')
    write('k37_figs_k3.py', s)

# ---------------------------------------------------------------- k68: repair the corrupted guard
s = read('k68_fig_fixes.py')
bad = ("import os as _os\r\n"
       "if _os.environ.get('K3_ALLOW_STALE_FIG'):\r\n"
       "    fig.tight_layout(); fig.savefig(OUT + '/FigK3_1_definition.png', bbox_inches='tight')\r\n"
       "else:/n    print('  [skip] Figure 1 现由 k78_fig1_redo.py 生成，本脚本默认不再写出（设 K3_ALLOW_STALE_FIG=1 可强制）')\r\n"
       "plt.close(fig)")
good = guard('Figure 1', 'k78_fig1_redo.py',
             "fig.tight_layout(); fig.savefig(OUT + '/FigK3_1_definition.png', bbox_inches='tight')")
if s.count(bad) == 1:
    s = s.replace(bad, good, 1)
    write('k68_fig_fixes.py', s)
    print('  ok  k68 guard 已修正')
else:
    fails.append('k68: 未找到损坏的 guard 块 (%d)' % s.count(bad))

# ---------------------------------------------------------------- k46 / k46b: module-level refusal
RAISE46 = (NL + NL + 'raise SystemExit(' + NL
           + "    '[已弃用] k46_figs_redo.py 含硬编码发生率（mv = [5.82, 3.72, ...]），运行会把 Figure 1 覆盖为旧版并写入错的柱顶标签。'" + NL
           + "    'Figure 1 现由 k78_fig1_redo.py 生成、Figure 5 由 k37_figs_k3.py 生成。本脚本不再运行。')" + NL)
RAISE46B = (NL + NL + 'raise SystemExit(' + NL
            + "    '[已弃用] Figure 3 现由 k70_fig3_fix.py 生成（含 x 轴标签重叠修复与数值断言）。本脚本不再运行。')" + NL)


def insert_after_imports(path, text, tag):
    s = read(path)
    if 'raise SystemExit' in s:
        print('  --  %s 已含 raise' % tag)
        return
    marker = 'from matplotlib.patches'
    if marker not in s:
        fails.append('%s: 找不到 matplotlib.patches 导入' % tag)
        return
    pos = s.index(marker)
    end = s.index(NL, pos) + len(NL)          # 该 import 行结束处
    write(path, s[:end] + text + s[end:])
    print('  ok  %s 已插入弃用保护' % tag)


insert_after_imports('k46_figs_redo.py', RAISE46, 'k46')
insert_after_imports('k46b_fig3_redo.py', RAISE46B, 'k46b')

if fails:
    print('ABORT:'); [print('  -', f) for f in fails]; sys.exit(1)
print('全部完成')
