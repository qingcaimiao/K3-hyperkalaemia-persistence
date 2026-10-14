# -*- coding: utf-8 -*-
"""k92: rebuild and verify the JCM submission package from the current sources.

Slots (MDPI SuSy):
  01_Manuscript.docx              <- out/manuscript_K3_EN.docx            (Word)
  02_Cover_Letter.pdf             <- regenerated from Cover_Letter_JCM.md (this slot accepts PDF only)
  03_Supplementary_Materials.zip  <- regenerated PDFs of the supplement + STROBE checklist
  04_Figures.zip                  <- Figure_1..6.tiff (600 dpi), order = text order
  Figures_单张备用/                <- the same TIFFs as loose files
  00_上传指引.md                   <- kept as is

Verification performed at the end: MD5 vs sources, A4 page size, cantSplit coverage,
zip integrity, TIFF resolution, PDF page counts.
"""
import hashlib
import io
import os
import re
import shutil
import subprocess
import sys
import zipfile

from docx import Document
from PIL import Image
from pypdf import PdfReader

WS = os.path.dirname(os.path.abspath(__file__))
K = 'D:/桌面/workbuddyzuopin/K3xiangmu/'
PKG = K + '投稿包_JCM/'
PY = sys.executable

FIGURE_SRC = ['FigK3_1_definition', 'FigK3_2_flow', 'FigK3_3_variability',
              'FigK3_4_transition', 'FigK3_5_forest', 'FigK3_6_rule']

problems = []


def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=WS)
    if r.returncode != 0:
        problems.append('command failed: %s\n%s' % (' '.join(cmd), r.stdout[-400:] + r.stderr[-400:]))
    return r


def main():
    os.makedirs(PKG, exist_ok=True)
    os.makedirs(PKG + 'Figures_单张备用/', exist_ok=True)

    # ---- 1. manuscript Word -------------------------------------------------
    shutil.copy(K + 'manuscript_K3_EN.docx', PKG + '01_Manuscript.docx')
    print('[1] 01_Manuscript.docx  <- manuscript_K3_EN.docx')

    # ---- 2. cover letter PDF (regenerate from the current Markdown) --------
    r = run([PY, '-u', 'k67_cover_to_pdf.py'])
    if os.path.exists(K + 'Cover_Letter_JCM.pdf'):
        shutil.copy(K + 'Cover_Letter_JCM.pdf', PKG + '02_Cover_Letter.pdf')
        print('[2] 02_Cover_Letter.pdf  <- regenerated')
    else:
        problems.append('cover letter PDF missing')

    # ---- 3. supplementary: regenerate the two PDFs from the current md -----
    for src_md, out_pdf, pt in [('K3_Supplementary_Tables.md', 'K3_Supplementary_Tables.pdf', '8.5'),
                                ('K3_STROBE_checklist.md', 'K3_STROBE_checklist.pdf', '8.5')]:
        run([PY, '-u', 'k74_md_to_pdf.py', K + src_md, K + out_pdf, pt])
    zpath = PKG + '03_Supplementary_Materials.zip'
    if os.path.exists(zpath):
        os.remove(zpath)
    with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as z:
        for n in ['K3_Supplementary_Tables.pdf', 'K3_STROBE_checklist.pdf']:
            if os.path.exists(K + n):
                z.write(K + n, n)
    for h in ('K3_Supplementary_Tables.html', 'K3_STROBE_checklist.html'):
        if os.path.exists(K + h):
            os.remove(K + h)
    print('[3] 03_Supplementary_Materials.zip  <- regenerated (2 PDFs)')

    # ---- 4. figures --------------------------------------------------------
    for i, n in enumerate(FIGURE_SRC, 1):
        src = K + 'figures_600dpi/%s.tiff' % n
        dst = PKG + 'Figures_单张备用/Figure_%d.tiff' % i
        shutil.copy(src, dst)
    fz = PKG + '04_Figures.zip'
    if os.path.exists(fz):
        os.remove(fz)
    with zipfile.ZipFile(fz, 'w', zipfile.ZIP_DEFLATED) as z:
        for i in range(1, 7):
            z.write(PKG + 'Figures_单张备用/Figure_%d.tiff' % i, 'Figure_%d.tiff' % i)
    print('[4] 04_Figures.zip + Figures_单张备用/  <- 6 TIFFs')

    # ================= verification ========================================
    print('\n================ 校验 ================')

    # 01: MD5 + A4 + cantSplit
    a = md5(PKG + '01_Manuscript.docx')
    b = md5(K + 'manuscript_K3_EN.docx')
    print('01_Manuscript.docx 与工作区最新 MD5 一致: %s' % ('✅' if a == b else '❌'))
    if a != b:
        problems.append('01 manuscript MD5 mismatch')
    doc = Document(PKG + '01_Manuscript.docx')
    s = doc.sections[0]
    is_a4 = abs(s.page_width.cm - 21.0) < 0.05 and abs(s.page_height.cm - 29.7) < 0.05
    print('   纸张: %.2f x %.2f cm -> %s' % (s.page_width.cm, s.page_height.cm, 'A4 ✅' if is_a4 else '❌'))
    if not is_a4:
        problems.append('manuscript not A4')
    x = zipfile.ZipFile(PKG + '01_Manuscript.docx').read('word/document.xml').decode('utf-8')
    rows = len(re.findall(r'<w:tr[ >]', x))
    cs = x.count('<w:cantSplit')
    th = x.count('<w:tblHeader')
    print('   表格行 %d / cantSplit %d / tblHeader %d -> %s'
          % (rows, cs, th, '✅' if cs == rows and th == len(doc.tables) else '❌'))
    if cs != rows:
        problems.append('cantSplit incomplete')
    media = [n for n in zipfile.ZipFile(PKG + '01_Manuscript.docx').namelist()
             if n.startswith('word/media/')]
    print('   内嵌图片 %d 张 %s' % (len(media), '✅' if len(media) == 6 else '❌'))

    # 02
    r2 = PdfReader(PKG + '02_Cover_Letter.pdf')
    print('02_Cover_Letter.pdf: %d 页 %s' % (len(r2.pages), '✅' if len(r2.pages) >= 1 else '❌'))

    # 03
    with zipfile.ZipFile(PKG + '03_Supplementary_Materials.zip') as z:
        ok = z.testzip() is None
        items = [(i.filename, i.file_size) for i in z.infolist()]
    print('03_Supplementary_Materials.zip: %s | %s' % ('✅' if ok else '❌', items))
    if not ok:
        problems.append('supplementary zip corrupt')
    for n in ['K3_Supplementary_Tables.pdf', 'K3_STROBE_checklist.pdf']:
        if os.path.exists(K + n):
            print('   %s: %d 页' % (n, len(PdfReader(K + n).pages)))

    # 04
    with zipfile.ZipFile(PKG + '04_Figures.zip') as z:
        ok = z.testzip() is None
        names = [i.filename for i in z.infolist()]
    print('04_Figures.zip: %s | %s' % ('✅' if ok else '❌', names))
    if not ok or names != ['Figure_%d.tiff' % i for i in range(1, 7)]:
        problems.append('figure zip wrong order/content')
    for i in range(1, 7):
        im = Image.open(PKG + 'Figures_单张备用/Figure_%d.tiff' % i)
        dpi = im.info.get('dpi', (0, 0))[0]
        same = md5(PKG + 'Figures_单张备用/Figure_%d.tiff' % i) == md5(
            K + 'figures_600dpi/%s.tiff' % FIGURE_SRC[i - 1])
        print('   Figure_%d.tiff %s dpi=%s 与 figures_600dpi 一致=%s'
              % (i, im.size, dpi, '✅' if same else '❌'))
        if dpi < 600 or not same:
            problems.append('figure %d dpi/mismatch' % i)

    # 00
    print('00_上传指引.md: %s' % ('存在 ✅' if os.path.exists(PKG + '00_上传指引.md') else '缺失 ❌'))

    print('\n包内文件: %s' % sorted(os.listdir(PKG)))
    print('\n结论: %s' % ('**全部通过 ✅**' if not problems else '发现问题:\n  ' + '\n  '.join(problems)))


if __name__ == '__main__':
    main()
