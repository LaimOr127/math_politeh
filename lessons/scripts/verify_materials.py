"""Validate published Office packages against their canonical lesson sources."""
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'lessons/output'


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
        text = texts(guide, 'word/document.xml', w)
        for lesson in lessons:
            for section in lesson['scientificSections']:
                assert section['text'] in text, (lesson['id'], 'scientific explanation')
            for ex in lesson['exercises']:
                assert ex['prompt'] in text, (lesson['id'], 'scientific questions')
    with zipfile.ZipFile(OUT/'new-learning-guide.docx') as guide:
        text = texts(guide, 'word/document.xml', w)
        for lesson in lessons:
            for section in lesson['web']['sections']:
                assert all(p in text for p in section['paragraphs']), (lesson['id'], 'student explanation')
    print('Verified 144 editable slides, notes, animations and ten Word documents.')


if __name__ == '__main__':
    verify()
