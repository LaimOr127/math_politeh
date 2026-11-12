"""Materialise page numbers and hyperlinks in the native Word TOC after rendering.

The renderer is the source of pagination; this script does not guess page numbers.
Run it again after the final render to confirm that layout has not shifted.
"""
import argparse
import json
import re
import zipfile
from pathlib import Path

import pdfplumber
from lxml import etree as ET

ROOT = Path(__file__).resolve().parents[2]
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS = {'w': W}


def tag(name):
    return '{' + W + '}' + name


def normal(text):
    return re.sub(r'\s+', ' ', text).strip()


def materialise(docx, pdf, entries_path, check=False):
    """Cache actual rendered heading pages and add internal Word hyperlinks."""
    entries = json.loads(entries_path.read_text(encoding='utf-8'))
    pages = []
    with pdfplumber.open(pdf) as rendered:
        for page in rendered.pages:
            bold = ''.join(char['text'] for char in page.chars if 'bold' in char['fontname'].lower())
            pages.append(re.sub(r'\s+', '', bold))
            page.close()
    heading_pages = []
    for title, target in entries:
        candidates = [i+1 for i, text in enumerate(pages) if i >= 3
                      and re.sub(r'\s+', '', target) in text]
        assert candidates, ('Rendered heading not found', target)
        heading_pages.append(min(candidates))
    assert heading_pages == sorted(heading_pages), 'Contents are not in document order'
    with zipfile.ZipFile(docx) as source:
        parts = {name: source.read(name) for name in source.namelist()}
        infos = source.infolist()
    document = ET.fromstring(parts['word/document.xml'])
    for i, ((title, target), page_number) in enumerate(zip(entries, heading_pages)):
        marks = document.xpath(f'.//w:bookmarkStart[@w:name="_course_toc_{i}"]', namespaces=NS)
        assert len(marks) == 1, ('Missing contents entry', i)
        p = marks[0].getparent()
        values = p.findall('.//w:t', NS)
        assert len(values) >= 2 and title in values[0].text, ('Unexpected TOC cache', title)
        if check:
            assert values[-1].text == str(page_number), ('Outdated contents page', title)
            assert p.xpath('./w:hyperlink/w:r/w:tab', namespaces=NS), ('Missing tab inside contents link', title)
            continue
        values[-1].text = str(page_number)
        body = [item for item in document.findall('.//w:body/w:p', NS)
                if not item.xpath('./w:bookmarkStart[starts-with(@w:name, "_course_toc_")]', namespaces=NS)
                and normal(''.join(item.itertext())) == normal(target)]
        # itertext includes only XML text; native headings contain no field instructions.
        assert body, ('Cannot add link to heading', target)
        anchor = f'_course_body_{i}'
        if not body[0].xpath(f'./w:bookmarkStart[@w:name="{anchor}"]', namespaces=NS):
            start = ET.Element(tag('bookmarkStart'), {tag('id'): str(2000+i), tag('name'): anchor})
            end = ET.Element(tag('bookmarkEnd'), {tag('id'): str(2000+i)})
            body[0].insert(1 if body[0].find('w:pPr', NS) is not None else 0, start)
            body[0].append(end)
        if p.find('w:hyperlink', NS) is None:
            link = ET.Element(tag('hyperlink'), {tag('anchor'): anchor, tag('history'): '1'})
            text_runs = p.findall('w:r', NS)
            insertion = p.index(text_runs[0])
            for run in text_runs:
                p.remove(run); link.append(run)
            p.insert(insertion, link)
        else:
            # Repair old caches that left the tab after the linked page number.
            link = p.find('w:hyperlink', NS)
            for run in p.findall('w:r', NS):
                if run.find('w:tab', NS) is not None:
                    p.remove(run); link.insert(max(0, len(link)-1), run)
    if check:
        print(f'Confirmed {len(entries)} contents page numbers against {len(pages)} rendered pages.')
        return
    settings = ET.fromstring(parts['word/settings.xml'])
    variables = settings.find('w:docVars', NS)
    if variables is None:
        variables = ET.SubElement(settings, tag('docVars'))
    for name, value in [('COURSE_TOC_READY', '1'), ('COURSE_RENDERED_PAGES', str(len(pages)))]:
        existing = variables.find(f'w:docVar[@w:name="{name}"]', NS)
        if existing is None:
            existing = ET.SubElement(variables, tag('docVar'), {tag('name'): name})
        existing.set(tag('val'), value)
    parts['word/document.xml'] = ET.tostring(document, xml_declaration=True, encoding='UTF-8', standalone=True)
    parts['word/settings.xml'] = ET.tostring(settings, xml_declaration=True, encoding='UTF-8', standalone=True)
    temporary = docx.with_suffix('.contents.tmp')
    with zipfile.ZipFile(temporary, 'w') as target_zip:
        for info in infos:
            target_zip.writestr(info, parts[info.filename])
    temporary.replace(docx)
    result = {'rendered_pages': len(pages), 'contents': [
        {'title': entry[0], 'page': page} for entry, page in zip(entries, heading_pages)]}
    (entries_path.parent/'contents-check.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Materialised {len(entries)} linked contents entries from {len(pages)} rendered pages.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pdf', type=Path, help='Rendered PDF used only for pagination QA')
    parser.add_argument('--docx', type=Path, default=ROOT/'lessons/output/scientific-methodical-guide.docx')
    parser.add_argument('--entries', type=Path, default=ROOT/'.build/scientific-review/toc-entries.json')
    parser.add_argument('--check', action='store_true', help='Validate final pagination without changing the DOCX')
    args = parser.parse_args()
    materialise(args.docx, args.pdf, args.entries, args.check)


if __name__ == '__main__':
    main()
