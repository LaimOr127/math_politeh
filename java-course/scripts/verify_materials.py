"""Validate all Java Office artifacts against their canonical content using stdlib only."""
import json,re,zipfile,hashlib,posixpath
from pathlib import Path
from xml.etree import ElementTree as E
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'java-course/output'
C=json.loads((ROOT/'java-course/content/course.json').read_text(encoding='utf-8'))
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
A='{http://schemas.openxmlformats.org/drawingml/2006/main}'
def norm(s):return re.sub(r'\s+',' ',s).strip()
def text(z,name,tag):return norm(' '.join(n.text or '' for n in E.fromstring(z.read(name)).iter(tag)))
def files():
    return [OUT/f'lesson-{i:02d}-{suffix}' for i in range(1,11) for suffix in ('presentation.pptx','teacher-script.docx')]+[OUT/'scientific-methodical-guide.docx']
def verify():
    with zipfile.ZipFile(OUT/'scientific-methodical-guide.docx') as guide:
        full=text(guide,'word/document.xml',W+'t')
        body=E.fromstring(guide.read('word/document.xml'))
        for paragraph in body.iter(W+'p'):
            if paragraph.find('.//'+W+'br') is not None:
                alignment=paragraph.find('./'+W+'pPr/'+W+'jc')
                assert alignment is not None and alignment.get(W+'val') in ('left','center'),'Manual line breaks must not stretch across a justified paragraph'
        section=body.find('.//'+W+'sectPr');margins=section.find(W+'pgMar')
        assert margins.get(W+'left')=='1701' and margins.get(W+'right')=='850'
        assert len(guide.namelist())>15
        guide_media={hashlib.sha256(guide.read(n)).hexdigest() for n in guide.namelist() if n.startswith('word/media/')}
        for name in [lesson['diagram'] for lesson in C['lessons']]+['project-screen']:
            expected=hashlib.sha256((ROOT/'java-course/illustrations'/f'{name}.png').read_bytes()).hexdigest()
            assert expected in guide_media,('Stale or missing guide diagram',name)
        links=[link for link in body.findall('.//'+W+'hyperlink') if (link.get(W+'anchor') or '').startswith('_course_body_')]
        assert len(links)>=20,'Materialise linked contents after rendering'
        for link in links:
            assert link.find('.//'+W+'tab') is not None,'TOC page separator must stay inside the link'
            assert link.findall(W+'r')[-1].find(W+'t') is not None
        variables=E.fromstring(guide.read('word/settings.xml'))
        assert any(v.get(W+'name')=='COURSE_TOC_READY' and v.get(W+'val')=='1' for v in variables.iter(W+'docVar'))
    for i,l in enumerate(C['lessons'],1):
        assert sum(s['minutes'] for s in l['slides'])==90
        assert sum(s['minutes'] for s in l['slides'][:7])==45
        with zipfile.ZipFile(OUT/f'lesson-{i:02d}-teacher-script.docx') as z:script=text(z,'word/document.xml',W+'t')
        for value in [l['title'],l['code'],l['stdout'],l['lab'],l['solution'],l['homework'],*[t['text'] for t in l['theory']]]:
            assert norm(value) in full,(i,value[:40])
        assert norm(l['code']) in script
        for extra in l.get('extraExamples',[]):assert norm(extra['code']) in script and norm(extra['code']) in full
        with zipfile.ZipFile(OUT/f'lesson-{i:02d}-presentation.pptx') as z:
            slide_names=[n for n in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+.xml',n)]
            assert len(slide_names)==15
            for j,s in enumerate(l['slides'],1):
                notes=text(z,f'ppt/notesSlides/notesSlide{j}.xml',A+'t')
                assert norm(s['teacher']) in notes and norm(s['answer']) in notes
                assert norm(s['teacher']) in script and norm(s['answer']) in script
                assert norm(s['teacher']) in full
                xml=z.read(f'ppt/slides/slide{j}.xml')
                if not s.get('diagram'):assert b'<p:timing' in xml
                else:
                    slide=E.fromstring(xml)
                    blip=slide.find('.//'+A+'blip')
                    embed=blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                    relations=E.fromstring(z.read(f'ppt/slides/_rels/slide{j}.xml.rels'))
                    target=next(r.get('Target') for r in relations if r.get('Id')==embed)
                    media_path=target.lstrip('/') if target.startswith('/') else posixpath.normpath('ppt/slides/'+target)
                    expected=(ROOT/'site/java/figures'/f'{s["diagram"]}.png').read_bytes()
                    assert z.read(media_path)==expected,('Stale slide diagram',i,j)
    for filename in ('RoutePlanner.java','RoutePlannerTest.java','Main.java'):
        assert norm((ROOT/'java-course/project'/filename).read_text(encoding='utf-8')) in full
    archive=OUT/'java-course-materials.zip'
    if archive.exists():
        with zipfile.ZipFile(archive) as z:
            for file in files():assert z.read('materials/'+file.name)==file.read_bytes(),file.name
            assert not any(n.endswith('.class') or '/.env' in n for n in z.namelist())
    print('Java materials: 10 PPTX, 10 scripts, unified guide and canonical content verified')
if __name__=='__main__':verify()
