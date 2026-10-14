# -*- coding: utf-8 -*-
"""k90: sync the workspace artefacts to the project folder (and the code repository).

Single source of truth:  the workspace  out/  directory.
Delivery copies:         D:/桌面/workbuddyzuopin/K3xiangmu/
Repository mirror:       .../K3xiangmu/K3_repo/

Rules (learned the hard way):
  * the manuscript .md files are regenerated with figures/ (not figures_k3/) paths
  * the repository manuscript keeps the workspace path (figures_k3/)
  * every script listed in SCRIPTS is copied to both code/ and K3_repo/code/
  * every audit report listed in REPORTS is copied to results/
"""
import io
import os
import shutil

WS = os.path.dirname(os.path.abspath(__file__))
K = 'D:/桌面/workbuddyzuopin/K3xiangmu/'
REPO = K + 'K3_repo/'

SCRIPTS = [
    'md2docx.py', '_k3_final_check.py',
    'k57_preflight_audit.py', 'k59_number_trace.py', 'k63_table_checks.py',
    'k73_docx_structure_audit.py', 'k74_md_to_pdf.py', 'k75_table_cell_audit.py',
    'k76_final_full_audit.py', 'k77_backmatter_align.py', 'k78_fig1_redo.py',
    'k79_refcheck2.py', 'k80_novelty3track.py', 'k81_novelty_fixes.py',
    'k82_fig_guards.py', 'k83_fig_ownership.py',
    'k84_docx_to_pdf.py', 'k85_pdfcheck.py', 'k86_render_wordpdf.py',
    'k87_conversion_integrity.py', 'k88_cn_pdfcheck.py', 'k89_docx_metadata_audit.py',
    'k41b_fig_flow.py', 'k46_figs_redo.py', 'k62_fig_rule_redo.py',
    'k68_fig_fixes.py', 'k70_fig3_fix.py', 'k72_drop_s6.py',
    'k47_supp_tables.py', 'k48_k3_round2.py', 'k48c_round2c.py',
]

REPORTS = [
    'K3_preflight_audit.md', 'K3_number_trace.md', 'K3_table_checks.md',
    'K3_docx_structure_audit.md', 'K3_table_cell_audit.md', 'K3_final_full_audit.md',
    'K3_refcheck2.json', 'K3_novelty3track.json',
]

DOCS = ['manuscript_K3_EN.docx', '稿件_K3_中文版.docx',
        'manuscript_K3_EN.pdf', 'manuscript_K3_EN_Word转PDF.pdf',
        '稿件_K3_中文版_Word转PDF.pdf']


def cp(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy(src, dst)


def main():
    # 1. manuscript Markdown (delivery copies use figures/ paths)
    for src, dst in [('out/manuscript_K3.md', 'manuscript_K3.md'),
                     ('out/稿件_K3_中文版.md', '稿件_K3_中文版.md')]:
        s = io.open(os.path.join(WS, src), encoding='utf-8').read()
        io.open(K + dst, 'w', encoding='utf-8').write(s.replace('figures_k3/', 'figures/'))
    print('manuscript md  -> project folder')

    # 2. same file into the repository, with the workspace figure path kept
    io.open(REPO + 'manuscript_K3.md', 'w', encoding='utf-8').write(
        io.open(os.path.join(WS, 'out/manuscript_K3.md'), encoding='utf-8').read())
    print('manuscript md  -> repository')

    # 3. docx / pdf
    for f in DOCS:
        if os.path.exists(os.path.join(WS, 'out', f)):
            cp(os.path.join(WS, 'out', f), K + f)
        elif os.path.exists(K + f):
            pass
        else:
            print('  (skip, absent)', f)
    print('docx/pdf       -> project folder')

    # 4. figures for the manuscript
    for f in sorted(os.listdir(os.path.join(WS, 'out/figures_k3'))):
        cp(os.path.join(WS, 'out/figures_k3', f), K + 'figures/' + f)
        cp(os.path.join(WS, 'out/figures_k3', f), REPO + 'figures/' + f)
    print('figures        -> project folder + repository')

    # 5. scripts
    n = 0
    for f in SCRIPTS:
        p = os.path.join(WS, f)
        if os.path.exists(p):
            cp(p, K + 'code/' + f)
            cp(p, REPO + 'code/' + f)
            n += 1
    print('scripts        -> %d files to code/ + K3_repo/code/' % n)

    # 6. audit reports
    for f in REPORTS:
        p = os.path.join(WS, 'out', f)
        if os.path.exists(p):
            cp(p, K + 'results/' + f)
    print('audit reports  -> results/')

    # 7. supplementary / STROBE
    for f in ['K3_Supplementary_Tables.md', 'K3_STROBE_checklist.md']:
        if os.path.exists(os.path.join(WS, 'out', f)):
            cp(os.path.join(WS, 'out', f), K + f)
    print('done')


if __name__ == '__main__':
    main()
