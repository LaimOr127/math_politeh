"""Add a native PowerPoint entrance animation to shapes named reveal-answer.

The only reveal is the answer/output block; one click exposes it. This is an
OOXML timing edit, not a transition or a speaker-note instruction.
"""
import sys
import zipfile
from pathlib import Path
from lxml import etree as E

P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
NS = {'p': P}

def animate(path):
    """Atomically rewrite a PPTX with valid on-click entrance timing trees."""
    temporary = path.with_suffix('.animated.pptx')
    count = 0
    with zipfile.ZipFile(path) as source, zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as target:
        for info in source.infolist():
            data = source.read(info.filename)
            if info.filename.startswith('ppt/slides/slide') and info.filename.endswith('.xml'):
                root = E.fromstring(data)
                shapes = root.xpath('.//p:cNvPr[@name="reveal-answer"]', namespaces=NS)
                if shapes:
                    assert len(shapes) == 1
                    spid = shapes[0].get('id')
                    for old in root.findall('p:timing', NS): root.remove(old)
                    timing = E.fromstring(f'''<p:timing xmlns:p="{P}"><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst><p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst><p:par><p:cTn id="3" fill="hold"><p:stCondLst><p:cond delay="indefinite"/></p:stCondLst><p:childTnLst><p:par><p:cTn id="4" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst><p:par><p:cTn id="5" presetID="1" presetClass="entr" presetSubtype="0" fill="hold" nodeType="clickEffect"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst><p:set><p:cBhvr><p:cTn id="6" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn><p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr><p:to><p:strVal val="visible"/></p:to></p:set></p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn><p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst><p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq></p:childTnLst></p:cTn></p:par></p:tnLst></p:timing>''')
                    ext = root.find('p:extLst', NS)
                    root.insert(list(root).index(ext) if ext is not None else len(root), timing)
                    data = E.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)
                    count += 1
            target.writestr(info, data)
    temporary.replace(path)
    print(f'{path.name}: {count} click-to-reveal animations')
    if count == 0: raise ValueError('No reveal-answer shapes found.')

if __name__ == '__main__': animate(Path(sys.argv[1]))
