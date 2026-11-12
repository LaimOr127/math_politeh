"""Validate published Office packages against their canonical lesson sources."""
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'lessons/output'
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'


def verify_scientific_format(archive):
    """Check the explicit formal layout and illustration contract of the guide."""
    ns = {'w': W, 'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'}
    root = ET.fromstring(archive.read('word/document.xml'))
    section = root.find('.//w:sectPr', ns)
    margin = section.find('w:pgMar', ns)
    for name, expected in {'left': 1701, 'right': 850, 'top': 1134, 'bottom': 1134}.items():
        assert abs(int(margin.get('{' + W + '}' + name)) - expected) <= 1, ('GOST margin', name)
    assert section.find('w:titlePg', ns) is not None, 'Title must have no printed page number'
    styles = ET.fromstring(archive.read('word/styles.xml'))
    normal = styles.find('.//w:style[@w:styleId="Normal"]', ns)
    assert normal.find('w:rPr/w:rFonts', ns).get('{' + W + '}ascii') == 'Times New Roman'
    assert normal.find('w:rPr/w:sz', ns).get('{' + W + '}val') == '28', '14 pt body'
    assert normal.find('w:pPr/w:spacing', ns).get('{' + W + '}line') == '360', '1.5 line spacing'
    assert normal.find('w:pPr/w:ind', ns).get('{' + W + '}firstLine') == '709', '1.25 cm indent'
    for name in ('Normal', 'Title', 'Subtitle', 'Heading1', 'Heading2', 'Heading3'):
        style = styles.find(f'.//w:style[@w:styleId="{name}"]', ns)
        fonts = style.find('w:rPr/w:rFonts', ns)
        assert fonts.get('{' + W + '}ascii') == 'Times New Roman', ('Font', name)
        assert not any('theme' in key.lower() for key in fonts.attrib), ('Theme overrides font', name)
    media = [name for name in archive.namelist() if name.startswith('word/media/')]
    assert len(media) >= 11, 'Missing course illustrations'
    assert len(root.findall('.//wp:docPr', ns)) >= 11, 'Illustrations not embedded'
    assert all(item.get('descr') for item in root.findall('.//wp:docPr', ns)), 'Missing image descriptions'
    instructions = ' '.join(n.text or '' for n in root.findall('.//w:instrText', ns))
    assert 'TOC' in instructions, 'Missing automatic contents'
    settings = ET.fromstring(archive.read('word/settings.xml'))
    ready = settings.find('.//w:docVar[@w:name="COURSE_TOC_READY"]', ns)
    assert ready is not None and ready.get('{' + W + '}val') == '1', 'Contents need rendered page numbers'
    assert len(root.findall('.//w:hyperlink', ns)) >= 21, 'Contents links missing'
    text = texts(archive, 'word/document.xml', W)
    for expected in ('ВВЕДЕНИЕ', 'ЗАКЛЮЧЕНИЕ', 'СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ',
                     'ПРИЛОЖЕНИЕ В', 'Сценарии проведения занятий', 'дата обращения:', 'Рисунок 11'):
        assert expected in text, ('Missing formal guide element', expected)


def texts(archive, name, namespace):
    """Return joined editable XML text nodes from one Office part."""
    root = ET.fromstring(archive.read(name))
    return '\n'.join(node.text or '' for node in root.iter('{' + namespace + '}t'))


def verify():
    """Fail for missing, stale, raster-only or mismatched published materials."""
    a = 'http://schemas.openxmlformats.org/drawingml/2006/main'
    w = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
    lessons = [json.loads(p.read_text(encoding='utf-8')) for p in sorted((ROOT/'lessons/content').glob('lesson-*.json'))]
    assert len(lessons) == 8
    for lesson in lessons:
        with zipfile.ZipFile(OUT/f"lesson-{lesson['id']}-presentation.pptx") as deck:
            slides = [name for name in deck.namelist() if name.startswith('ppt/slides/slide') and name.endswith('.xml')]
            assert len(slides) == len(lesson['slides']) == 18, lesson['id']
            for i, slide in enumerate(lesson['slides'], 1):
                text = texts(deck, f'ppt/slides/slide{i}.xml', a)
                assert slide['title'] in text, (lesson['id'], i, 'title')
                assert slide['answer'] in text, (lesson['id'], i, 'visible answer')
                for body in slide['body']:
                    assert body in text, (lesson['id'], i, 'body')
                notes = texts(deck, f'ppt/notesSlides/notesSlide{i}.xml', a)
                assert slide['teacher'] in notes, (lesson['id'], i, 'notes')
                if slide['animation']:
                    assert b'<p:timing' in deck.read(f'ppt/slides/slide{i}.xml'), (lesson['id'], i, 'animation')
        with zipfile.ZipFile(OUT/f"lesson-{lesson['id']}-teacher-script.docx") as script:
            text = texts(script, 'word/document.xml', w)
            for slide in lesson['slides']:
                assert slide['teacher'] in text, (lesson['id'], 'script speech')
                assert slide['question'] in text, (lesson['id'], 'script question')
            for ex in lesson['exercises']:
                assert ex['prompt'] in text, (lesson['id'], 'exercise')
    with zipfile.ZipFile(OUT/'scientific-methodical-guide.docx') as guide:
        verify_scientific_format(guide)
        text = texts(guide, 'word/document.xml', w)
        for lesson in lessons:
            for section in lesson['scientificSections']:
                assert section['text'] in text, (lesson['id'], 'scientific explanation')
            for ex in lesson['exercises']:
                assert ex['prompt'] in text, (lesson['id'], 'scientific questions')
            for slide in lesson['slides']:
                assert slide['teacher'] in text, (lesson['id'], 'consolidated teacher speech')
                assert slide['question'] in text, (lesson['id'], 'consolidated slide question')
                assert slide['answer'] in text, (lesson['id'], 'consolidated slide answer')
    with zipfile.ZipFile(OUT/'new-learning-guide.docx') as guide:
        text = texts(guide, 'word/document.xml', w)
        for lesson in lessons:
            for section in lesson['web']['sections']:
                assert all(p in text for p in section['paragraphs']), (lesson['id'], 'student explanation')
    print('Verified 144 editable slides, notes, animations and ten Word documents.')


if __name__ == '__main__':
    verify()
