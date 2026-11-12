"""Create a downloadable archive containing only the eighteen published files."""
from pathlib import Path
import zipfile
from verify_materials import verify

ROOT = Path(__file__).resolve().parents[2]


def package():
    """Validate Office sources and write the course archive; return its path."""
    verify()
    output = ROOT/'lessons/output'
    files = [output/'new-learning-guide.docx', output/'scientific-methodical-guide.docx']
    for i in range(1,9):
        files.extend([output/f'lesson-{i:02}-presentation.pptx',output/f'lesson-{i:02}-teacher-script.docx'])
    target = ROOT/'lessons/python-course-materials.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as archive:
        for file in files:
            archive.write(file,file.name)
    print(target)
    return target


if __name__ == '__main__':
    package()
