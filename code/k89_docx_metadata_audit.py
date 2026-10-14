# -*- coding: utf-8 -*-
"""k89: audit aspects of the .docx that the text-level checks do not cover.

  1. tracked changes (w:ins / w:del) and comments -- must be absent in a submission
  2. document properties (core.xml / app.xml): author, last-modified-by, company
  3. font coverage: every run must carry an explicit font (ascii + eastAsia)
  4. embedded image inventory: pixel size of each word/media item
  5. unusual parts in the package (e.g. stale embedded objects)
"""
import io
import re
import zipfile

from PIL import Image

K = 'D:/桌面/workbuddyzuopin/K3xiangmu/'
FILES = [
    ('EN', K + '投稿包_JCM/01_Manuscript.docx'),
    ('CN', K + '稿件_K3_中文版.docx'),
]

for tag, path in FILES:
    z = zipfile.ZipFile(path)
    names = z.namelist()
    xml = z.read('word/document.xml').decode('utf-8')
    print('=' * 22, tag, '=' * 22)

    # 1. tracked changes / comments
    ins = len(re.findall(r'<w:ins ', xml))
    dele = len(re.findall(r'<w:del ', xml))
    cmt = [n for n in names if 'comment' in n.lower()]
    footnotes = len(re.findall(r'<w:footnoteReference', xml))
    endnotes = len(re.findall(r'<w:endnoteReference', xml))
    print('  修订插入 w:ins=%d | 修订删除 w:del=%d | 批注文件=%s' % (ins, dele, cmt or '无 ✅'))
    print('  脚注引用=%d | 尾注引用=%d' % (footnotes, endnotes))

    # 2. document properties
    for part in ('docProps/core.xml', 'docProps/app.xml'):
        if part in names:
            s = z.read(part).decode('utf-8', 'ignore')
            for key in ('dc:creator', 'cp:lastModifiedBy', 'dc:title', 'Company', 'AppVersion'):
                m = re.search(r'<%s[^>]*>(.*?)</%s>' % (key, key), s)
                if m and m.group(1).strip():
                    print('  %-16s %s' % (key, m.group(1).strip()[:70]))

    # 3. font coverage
    runs = re.findall(r'<w:r>(?:(?!</w:r>).)*?</w:r>', xml, re.S)
    txt_runs = [r for r in runs if re.sub(r'<[^>]+>', '', r).strip()]
    no_font = [r for r in txt_runs if '<w:rFonts' not in r]
    print('  有文字的 run: %d | 未显式指定字体: %d' % (len(txt_runs), len(no_font)))
    if no_font[:3]:
        for r in no_font[:3]:
            print('     ⚠', re.sub(r'<[^>]+>', '', r)[:60])

    # 4. embedded images
    media = [n for n in names if n.startswith('word/media/')]
    print('  内嵌图片 %d 个:' % len(media))
    for m in sorted(media):
        im = Image.open(io.BytesIO(z.read(m)))
        print('     %-24s %s  %s' % (m.split('/')[-1], im.size, im.format))

    # 5. unusual parts
    odd = [n for n in names if re.search(r'(oleObject|embeddings|chart|activeX|vbaProject|altChunk)', n, re.I)]
    print('  可疑部件:', odd or '无 ✅')
    print()
