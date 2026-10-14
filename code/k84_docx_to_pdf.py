# -*- coding: utf-8 -*-
"""k84: render a .docx to PDF by reading the Word file itself (not the Markdown).

Pipeline: .docx --(python-docx: paragraphs, runs, real tables, embedded images)-->
styled HTML --> Microsoft Edge headless --print-to-pdf.

Why this exists: k74 renders the *Markdown*, so it cannot catch problems that only
exist in the Word file (stray runs, missing images, table cells lost in conversion,
lost superscripts, paragraph breaks).  This tool renders what the manuscript Word
file actually contains, so the PDF can be audited against the Word source.

Usage: python k84_docx_to_pdf.py <in.docx> <out.pdf> [body_pt]
"""
import base64
import io
import os
import re
import subprocess
import sys
import tempfile
import time

from docx import Document
from docx.oxml.ns import qn

EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'

CSS = """
@page { size: A4; margin: 17mm 16mm 16mm 16mm; }
html, body { margin: 0; padding: 0; background: #fff; }
body { font-family: "Times New Roman", "SimSun", serif; font-size: %(pt)spt;
       line-height: 1.42; color: #000; text-align: justify; }
h1 { font-size: 16pt; text-align: center; margin: 0 0 8pt 0; line-height: 1.25; }
h2 { font-size: 13.5pt; margin: 11pt 0 5pt 0; border-bottom: 0.6pt solid #999; padding-bottom: 2pt; }
h3 { font-size: 12pt; margin: 9pt 0 4pt 0; }
p { margin: 0 0 5pt 0; orphans: 2; widows: 2; }
ul { margin: 0 0 5pt 0; padding-left: 15pt; }
li { margin: 0 0 2pt 0; }
hr { border: 0; border-top: 0.6pt solid #bbb; margin: 8pt 0; }
table { border-collapse: collapse; width: 100%%; margin: 3pt 0 6pt 0;
        font-size: 9pt; page-break-inside: auto; }
th, td { border: 0.5pt solid #666; padding: 1.6pt 3pt; text-align: left; vertical-align: top; }
th { background: #EDEDED; font-weight: bold; }
tr { page-break-inside: avoid; }
thead { display: table-header-group; }
img { display: block; margin: 4pt auto 2pt auto; max-width: 100%%; }
sup { vertical-align: super; font-size: 0.72em; }
sub { vertical-align: sub; font-size: 0.72em; }
"""

EMU_PER_INCH = 914400


def _run_html(run, doc):
    """One <w:r> -> HTML.  Images and superscripts handled here."""
    out = []
    # images
    blips = run._element.findall('.//' + qn('a:blip'))
    for blip in blips:
        rid = blip.get(qn('r:embed'))
        if not rid:
            continue
        try:
            part = doc.part.related_parts[rid]
            b64 = base64.b64encode(part.blob).decode('ascii')
        except Exception:
            continue
        # width from wp:extent (EMU) if present
        ext = run._element.find('.//' + qn('wp:extent'))
        if ext is not None and ext.get('cx'):
            w_in = int(ext.get('cx')) / EMU_PER_INCH
            style = ' style="width:%.2fin"' % w_in
        else:
            style = ''
        out.append('<img src="data:%s;base64,%s"%s/>'
                   % (getattr(part, 'content_type', 'image/png'), b64, style))
    txt = run.text
    if txt:
        t = (txt.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))
        rpr = run._element.find(qn('w:rPr'))
        bold = run.bold
        italic = run.italic
        sup = False
        if rpr is not None:
            va = rpr.find(qn('w:vertAlign'))
            if va is not None and va.get(qn('w:val')) == 'superscript':
                sup = True
        if bold:
            t = '<strong>%s</strong>' % t
        if italic:
            t = '<em>%s</em>' % t
        if sup:
            t = '<sup>%s</sup>' % t
        out.append(t)
    return ''.join(out)


def _para_kind(par):
    """Classify a Word paragraph by the size of its first non-empty run."""
    for run in par.runs:
        if not run.text.strip():
            continue
        sz = None
        rpr = run._element.find(qn('w:rPr'))
        if rpr is not None:
            s = rpr.find(qn('w:sz'))
            if s is not None and s.get(qn('w:val')):
                sz = int(s.get(qn('w:val')))
        if sz is None:
            return 'p'
        if sz >= 32:
            return 'h1'
        if sz >= 27:
            return 'h2'
        if sz >= 24:
            return 'h3'
        return 'p'
    return 'p'


def _is_list(par):
    ppr = par._element.find(qn('w:pPr'))
    if ppr is None:
        return False
    st = ppr.find(qn('w:pStyle'))
    return st is not None and st.get(qn('w:val')) in ('ListBullet', 'ListParagraph', 'ListNumber')


def convert_docx(path, pt=9.5):
    doc = Document(path)
    body = doc.element.body
    out = []
    in_ul = False
    from docx.text.paragraph import Paragraph
    from docx.table import Table

    for child in body.iterchildren():
        tag = child.tag.split('}')[-1]
        if tag == 'p':
            par = Paragraph(child, doc)
            text = par.text.strip()
            has_img = bool(child.findall('.//' + qn('a:blip')))
            if not text and not has_img:
                if in_ul:
                    out.append('</ul>')
                    in_ul = False
                continue
            html_runs = ''.join(_run_html(r, doc) for r in par.runs)
            if has_img and not text:
                if in_ul:
                    out.append('</ul>')
                    in_ul = False
                out.append('<p>%s</p>' % html_runs)
                continue
            kind = _para_kind(par)
            if _is_list(par):
                if not in_ul:
                    out.append('<ul>')
                    in_ul = True
                out.append('<li>%s</li>' % html_runs)
                continue
            if in_ul:
                out.append('</ul>')
                in_ul = False
            out.append('<%s>%s</%s>' % (kind, html_runs, kind))
        elif tag == 'tbl':
            if in_ul:
                out.append('</ul>')
                in_ul = False
            t = Table(child, doc)
            rows = []
            for ri, row in enumerate(t.rows):
                cells = []
                for c in row.cells:
                    inner = ' '.join(_run_html(r, doc) for p in c.paragraphs for r in p.runs)
                    cells.append(inner)
                rows.append(cells)
            if rows:
                head = '<thead><tr>' + ''.join('<th>%s</th>' % c for c in rows[0]) + '</tr></thead>'
                bod = ''.join('<tr>' + ''.join('<td>%s</td>' % c for c in r) + '</tr>' for r in rows[1:])
                out.append('<table>%s<tbody>%s</tbody></table>' % (head, bod))
    if in_ul:
        out.append('</ul>')

    css = CSS % {'pt': pt}
    return ('<!DOCTYPE html><html><head><meta charset="utf-8">'
            '<style>%s</style></head><body>%s</body></html>' % (css, '\n'.join(out)))


def print_pdf(html_path, pdf_path):
    url = 'file:///' + html_path.replace('\\', '/')
    r = None
    for attempt in range(1, 4):
        udd = tempfile.mkdtemp(prefix='k84edge')
        cmd = [EDGE, '--headless=new', '--disable-gpu', '--no-first-run',
               '--no-default-browser-check', '--no-pdf-header-footer',
               '--user-data-dir=' + udd, '--print-to-pdf=' + pdf_path, url]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        except subprocess.TimeoutExpired:
            r = None
        time.sleep(2)
        if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 2000:
            break
        print('  attempt %d produced %s bytes'
              % (attempt, os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 0))
    return r


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    docx_path, pdf_path = sys.argv[1], sys.argv[2]
    pt = float(sys.argv[3]) if len(sys.argv) > 3 else 9.5
    html_doc = convert_docx(docx_path, pt)
    html_path = os.path.splitext(pdf_path)[0] + '.from-docx.html'
    io.open(html_path, 'w', encoding='utf-8').write(html_doc)
    print('HTML written: %s (%.0f KB)' % (html_path, os.path.getsize(html_path) / 1024))
    r = print_pdf(html_path, pdf_path)
    ok = os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 2000
    print('PDF %s: %s' % ('written' if ok else 'FAILED', pdf_path))
    if not ok:
        print((r.stdout or '')[-600:], (r.stderr or '')[-600:])
        sys.exit(1)
    print('  %.0f KB' % (os.path.getsize(pdf_path) / 1024))


if __name__ == '__main__':
    main()
