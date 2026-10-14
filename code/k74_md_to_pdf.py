# -*- coding: utf-8 -*-
"""k74: render a manuscript / supplementary Markdown file to a clean PDF.

Pipeline: Markdown -> styled HTML (real <table>, embedded <img>) -> Microsoft Edge
headless --print-to-pdf.  The resulting PDF has a proper text layer: paragraphs and
table cells are real structures, so text-extraction tools no longer glue adjacent
blocks together (the false alarms reported earlier).

Usage: python k74_md_to_pdf.py <in.md> <out.pdf> [body_pt] [base_dir]
"""
import io, os, re, subprocess, sys, tempfile, time, html as _html

EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'

CSS = """
@page { size: A4; margin: 17mm 16mm 16mm 16mm; }
html, body { margin: 0; padding: 0; }
body { font-family: "Times New Roman", "SimSun", serif; font-size: %(pt)spt;
       line-height: 1.42; color: #000; text-align: justify; }
h1 { font-size: %(h1)spt; text-align: center; margin: 0 0 8pt 0; line-height: 1.25; }
h2 { font-size: %(h2)spt; margin: 11pt 0 5pt 0; border-bottom: 0.6pt solid #999; padding-bottom: 2pt; }
h3 { font-size: %(h3)spt; margin: 9pt 0 4pt 0; }
p { margin: 0 0 5pt 0; orphans: 2; widows: 2; }
p.cap { font-size: %(cap)spt; text-align: justify; }
ul, ol { margin: 0 0 5pt 0; padding-left: 15pt; }
li { margin: 0 0 2pt 0; }
hr { border: 0; border-top: 0.6pt solid #bbb; margin: 8pt 0; }
table { border-collapse: collapse; width: 100%%; margin: 3pt 0 6pt 0;
        font-size: %(tbl)spt; page-break-inside: auto; }
th, td { border: 0.5pt solid #666; padding: 1.6pt 3pt; text-align: left; vertical-align: top; }
th { background: #EDEDED; font-weight: bold; }
tr { page-break-inside: avoid; }
thead { display: table-header-group; }   /* 跨页重复表头 */
img { max-width: 100%%; height: auto; display: block; margin: 4pt auto 2pt auto; }
p.imgcap { page-break-before: avoid; }
strong { font-weight: bold; } em { font-style: italic; }
"""


def inline(t):
    t = _html.escape(t, quote=False)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'<em>\1</em>', t)
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    return t


def convert(md, base_dir, pt=9.5):
    out, in_ul = [], False
    lines = md.split('\n')
    i = 0
    while i < len(lines):
        raw = lines[i]
        s = raw.strip()
        if s == '---':
            if in_ul: out.append('</ul>'); in_ul = False
            out.append('<hr/>'); i += 1; continue
        if not s:
            if in_ul: out.append('</ul>'); in_ul = False
            i += 1; continue
        # 表格
        if s.startswith('|') and i + 1 < len(lines) and re.match(r'^\|[\s:|-]+\|$', lines[i + 1].strip()):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')]); i += 1
            head, body = rows[0], rows[2:]
            out.append('<table><thead><tr>' + ''.join('<th>%s</th>' % inline(c) for c in head) +
                       '</tr></thead><tbody>' +
                       ''.join('<tr>' + ''.join('<td>%s</td>' % inline(c) for c in r) + '</tr>' for r in body) +
                       '</tbody></table>')
            continue
        # 插图
        m = re.match(r'^!\[\]\((.+?)(?:\s+"([\d.]+)")?\)\s*$', s)
        if m:
            if in_ul: out.append('</ul>'); in_ul = False
            p = m.group(1)
            if not os.path.isabs(p):
                p = os.path.join(base_dir, p)
            if os.path.exists(p):
                w = float(m.group(2)) if m.group(2) else 6.5
                out.append('<img src="%s" style="width:%.2fin"/>' % ('file:///' + p.replace('\\', '/'), w))
            else:
                out.append('<p style="color:#b00">[missing figure: %s]</p>' % inline(p))
            i += 1; continue
        if s.startswith('#'):
            if in_ul: out.append('</ul>'); in_ul = False
            lvl = len(s) - len(s.lstrip('#'))
            out.append('<h%d>%s</h%d>' % (min(lvl, 3), inline(s.lstrip('#').strip()), min(lvl, 3)))
            i += 1; continue
        if s.startswith('- '):
            if not in_ul: out.append('<ul>'); in_ul = True
            out.append('<li>%s</li>' % inline(s[2:])); i += 1; continue
        if in_ul: out.append('</ul>'); in_ul = False
        # 图注/表注（**Figure 3.** / **表 3.** 之类）单独给样式，便于避免与图分页
        cls = ' class="cap"' if re.match(r'^\*\*(Figure|图|Table|表)\s*\d', s) else ''
        out.append('<p%s>%s</p>' % (cls, inline(s)))
        i += 1
    if in_ul: out.append('</ul>')
    body = '\n'.join(out)
    css = CSS % dict(pt=pt, h1=pt + 4.5, h2=pt + 2, h3=pt + 0.8, cap=pt - 1, tbl=max(pt - 2.5, 6.5))
    return ('<!DOCTYPE html><html><head><meta charset="utf-8"><style>%s</style></head><body>%s</body></html>'
            % (css, body))


def build(md_path, pdf_path, pt=9.5):
    md = io.open(md_path, encoding='utf-8').read()
    base = os.path.dirname(os.path.abspath(md_path))
    io.open(os.path.splitext(pdf_path)[0] + '.html', 'w', encoding='utf-8').write(convert(md, base, pt))
    html_p = os.path.splitext(pdf_path)[0] + '.html'
    if os.path.exists(pdf_path): os.remove(pdf_path)
    url = 'file:///' + html_p.replace('\\', '/')
    for attempt in range(1, 4):
        udd = tempfile.mkdtemp(prefix='k74edge')
        cmd = [EDGE, '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
               '--no-pdf-header-footer', '--user-data-dir=' + udd, '--print-to-pdf=' + pdf_path, url]
        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=240)
        except subprocess.TimeoutExpired:
            pass
        if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 3000:
            break
        print('  attempt %d produced %s bytes, retrying' % (attempt, os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 0))
        time.sleep(3)
    ok = os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 3000
    print('%s -> %s  %s (%d bytes)' % (os.path.basename(md_path), os.path.basename(pdf_path),
                                       'OK' if ok else 'FAILED', os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 0))
    return ok


if __name__ == '__main__':
    a = sys.argv[1:]
    build(a[0], a[1], float(a[2]) if len(a) > 2 else 9.5)
