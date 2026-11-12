"""Package final materials and runnable sources, excluding build files and secrets."""
from pathlib import Path
import zipfile,json,hashlib
from verify_materials import ROOT,OUT,files,verify
archive=OUT/'java-course-materials.zip'
# The old archive is intentionally replaced only after final files have been reviewed.
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for file in files():z.write(file,'materials/'+file.name)
    for folder in ['project','examples']:
        for file in sorted((ROOT/'java-course'/folder).rglob('*')):
            if file.is_file() and file.suffix in ('.java','.txt','.md'):z.write(file,file.relative_to(ROOT/'java-course').as_posix())
    z.write(ROOT/'java-course/README.md','README.md')
manifest={p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [*files(),archive]}
(ROOT/'java-course/MATERIALS_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
verify()
print(f'Packaged {len(files())} Office files and runnable source code')
