"""Render all final Word files with the Documents skill for visual QA."""
import os, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RUNTIME=Path(os.environ['RUNTIME_PYTHON'])
RENDER=Path(os.environ['DOCUMENTS_SKILL_DIR'])/'render_docx.py'
for source in sorted((ROOT/'java-course/output').glob('*.docx')):
    target=ROOT/'.build/java-review'/source.stem
    subprocess.run([str(RUNTIME),str(RENDER),str(source),'--output_dir',str(target),'--emit_pdf'],check=True)
    print(source.name,flush=True)
