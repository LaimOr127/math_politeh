"""Build teacher scripts and the methodical guide from the canonical lesson JSON."""
import argparse
import json
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'lessons/output'

def paragraph(doc, text, bold_label=None):
    """Add readable prose, optionally beginning with a bold field label."""
    p = doc.add_paragraph()
    if bold_label: p.add_run(bold_label + ' ').bold = True
    p.add_run(text)
    return p

def document(title, subtitle):
    """Create a restrained A4 teaching document with portable paragraph styles."""
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Inches(8.27), Inches(11.69)
    sec.top_margin = sec.bottom_margin = Inches(.65)
    sec.left_margin = sec.right_margin = Inches(.75)
    for name in ('Normal', 'Title', 'Subtitle', 'Heading 1', 'Heading 2', 'Heading 3'):
        style = doc.styles[name]
        style.font.name = 'Arial'
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.paragraph_format.space_after = Pt(7)
        for node in style.element.xpath('./w:pPr/w:pBdr'): node.getparent().remove(node)
    normal = doc.styles['Normal']
    normal.font.size = Pt(10.5)
    normal.paragraph_format.line_spacing = 1.12
    doc.styles['Title'].font.size = Pt(25)
    doc.styles['Heading 1'].font.size = Pt(18)
    doc.styles['Heading 2'].font.size = Pt(13)
    doc.add_heading(title, 0)
    paragraph(doc, subtitle)
    return doc

def code(doc, value):
    """Keep Python indentation in an editable monospaced paragraph."""
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(8)
    for index, line in enumerate(value.rstrip().split('\n')):
        run = p.add_run(('\n' if index else '') + line)
        run.font.name = 'Consolas'; run.font.size = Pt(10)
    return p

def picture(doc, path, caption, width=6.4):
    """Embed an existing factual image; missing assets fail the build."""
    path = ROOT / path
    if not path.is_file(): raise FileNotFoundError(path)
    p = doc.add_paragraph()
    r = p.add_run(); inline = r.add_picture(str(path), width=Inches(width))
    inline._inline.docPr.set('descr', caption)
    p.paragraph_format.keep_with_next = True
    paragraph(doc, caption)

def animation_text(slide):
    return ('Прежде чем открыть ответ или результат, выслушайте предположения класса.'
            if slide['animation'] else 'Слайд показан полностью, дополнительных щелчков не требуется.')

def teacher_script(lesson):
    """Build a slide-aligned script with elapsed time, speech and answer keys."""
    doc = document(f"Урок {int(lesson['id'])} {lesson['title']}", 'Сценарий преподавателя для 5–6 класса. 45 минут.')
    paragraph(doc, lesson['goal'], 'Цель:')
    paragraph(doc, 'Подготовьте Python 3, VS Code и расширение Python заранее по методическому пособию. Откройте презентацию и игровой сайт. Установка среды не входит в 45 минут занятия.')
    paragraph(doc, 'В таблице ниже указаны интервалы занятия. Время практики включает набор кода, запуск, обсуждение и помощь детям. Если группа идёт медленнее, дополнительное усложнение оставьте на дом, а итог урока сохраните.')
    table = doc.add_table(rows=1, cols=3)
    table.style = 'Table Grid'
    for c, value in zip(table.rows[0].cells, ('Слайд', 'Время', 'Тема')): c.text=value
    elapsed=0
    for i,s in enumerate(lesson['slides'],1):
        cells=table.add_row().cells
        cells[0].text=str(i);cells[1].text=f'{elapsed}–{elapsed+s["minutes"]} мин';cells[2].text=s['title'];elapsed+=s['minutes']
    elapsed=0
    for i,s in enumerate(lesson['slides'],1):
        doc.add_page_break()
        doc.add_heading(f"Слайд {i} {s['title']}", 1)
        paragraph(doc, f"{elapsed}–{elapsed+s['minutes']} мин · {s['minutes']} мин на этот этап")
        doc.add_heading('Что сказать',2)
        paragraph(doc,s['teacher'])
        paragraph(doc,s['action'],'Действия:')
        if s.get('code'):
            doc.add_heading('Код на слайде',2);code(doc,s['code'])
        paragraph(doc,s['question'],'Вопрос классу:')
        paragraph(doc,s['answer'],'Ожидаемый ответ:')
        if s.get('output'): code(doc,'Результат:\n'+s['output'])
        paragraph(doc,animation_text(s),'Анимация:')
        elapsed+=s['minutes']
    doc.add_page_break();doc.add_heading('Решение практики',1)
    paragraph(doc,lesson['practice'],'Задание:');code(doc,lesson['solution'])
    if lesson.get('solutionStdin'):paragraph(doc,repr(lesson['solutionStdin']),'Ввод для проверки:')
    code(doc,'Ожидаемый вывод:\n'+lesson['solutionOutput'])
    doc.save(OUT/f"lesson-{lesson['id']}-teacher-script-v2.docx")

def guide(lessons, setup):
    """Combine platform setup, theory and solved practice into one guide."""
    doc=document('Python в VS Code', 'Методическое пособие для учеников 5–6 класса и преподавателя')
    paragraph(doc,'Пособие помогает подготовить рабочее место, понять восемь основных тем Python и проверить собственные программы. Сначала пройдите настройку среды вместе со взрослым. Затем изучайте темы по порядку: каждый следующий урок использует уже знакомые команды.')
    paragraph(doc,setup['platform'],'Среда на снимках:')
    paragraph(doc,'Каждый урок длится 45 минут. Установка выполняется до первого занятия. Для практики нужны клавиатура, мышь и отдельная папка с файлами .py. Интернет нужен для скачивания программ и расширения; готовые примеры Python работают локально.')
    doc.add_heading('Содержание',1)
    for heading in ('1 Платформа и настройка','2 Теория и примеры','3 Практика с решениями','4 Ошибки и способы исправления','5 Источники'):
        paragraph(doc,heading)
    doc.add_page_break();doc.add_heading('1 Платформа и настройка',1)
    paragraph(doc,'Python выполняет команды программы. VS Code помогает набрать и сохранить код. Расширение Python добавляет выбор интерпретатора и запуск файла. Это три разные части рабочего места.')
    for i,step in enumerate(setup['steps'],1):
        if i>1: doc.add_page_break()
        doc.add_heading(f"Шаг {i} {step['title']}",2)
        paragraph(doc,step['text'])
        picture(doc,step['image'],f"Шаг {i}. {step['title']}")
        if step.get('expected'): paragraph(doc,step['expected'],'Проверь себя:')
    doc.add_page_break();doc.add_heading('2 Теория и примеры',1)
    for j,lesson in enumerate(lessons):
        if j:doc.add_page_break()
        doc.add_heading(f"Тема {int(lesson['id'])} {lesson['title']}",2)
        paragraph(doc,lesson['goal'],'После темы ты сможешь:')
        paragraph(doc,lesson['analogy'])
        picture(doc,f"site/assets/illustrations/lesson-{lesson['id']}.png",f"Образ для темы «{lesson['concept']}»",5.8)
        for s in lesson['slides']:
            doc.add_heading(s['title'],3)
            for line in s['body']:paragraph(doc,line)
            if s.get('code'):code(doc,s['code'])
            paragraph(doc,s['question'],'Подумай:')
            paragraph(doc,s['answer'],'Проверка:')
        doc.add_heading('Программа целиком',3);code(doc,lesson['code'])
        if lesson.get('stdin'):paragraph(doc,repr(lesson['stdin']),'Ввод для проверки:')
        code(doc,'Ожидаемый вывод:\n'+lesson['output'])
        picture(doc,f"site/assets/screenshots/lesson-{lesson['id']}.png",'Код и фактический результат в VS Code',6.3)
    doc.add_page_break();doc.add_heading('3 Практика с решениями',1)
    for lesson in lessons:
        doc.add_heading(f"Урок {int(lesson['id'])} {lesson['title']}",2)
        paragraph(doc,lesson['practice'],'Задача:')
        paragraph(doc,'Сначала напиши собственный вариант в отдельном файле .py. Сохрани его и запусти. Сравни результат с условием, затем открой решение.')
        code(doc,lesson['solution'])
        if lesson.get('solutionStdin'):paragraph(doc,repr(lesson['solutionStdin']),'Ввод:')
        code(doc,'Ожидаемый вывод:\n'+lesson['solutionOutput'])
        for ex in lesson['exercises']:
            paragraph(doc,ex['prompt'])
            choices=ex.get('options',ex.get('lines',[]))
            for key,label in choices:paragraph(doc,f'{key}: {label}')
            answer=ex['answer']; labels=dict(choices)
            readable=' → '.join(labels[x] for x in answer) if isinstance(answer,list) else labels[answer]
            paragraph(doc,readable+'. '+ex['feedback']['correct'],'Ответ:')
    doc.add_page_break();doc.add_heading('4 Ошибки и способы исправления',1)
    for item in setup['troubleshooting']:
        doc.add_heading(item['problem'],2);paragraph(doc,item['solution'])
    doc.add_heading('5 Источники',1)
    for item in setup['sources']:paragraph(doc,f"{item['title']}: {item['url']}")
    doc.save(OUT/'methodical-guide.docx')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--scripts-only',action='store_true');parser.add_argument('--lesson', action='append', help='Lesson ID, e.g. 01; may be repeated');args=parser.parse_args()
    lessons=[json.loads(p.read_text()) for p in sorted((ROOT/'lessons/content').glob('lesson-*.json'))]
    if args.lesson:
        lessons = [lesson for lesson in lessons if lesson['id'] in args.lesson]
        assert len(lessons) == len(set(args.lesson)), 'Requested lesson JSON not found'
        assert args.scripts_only, '--lesson requires --scripts-only'
    else:
        assert len(lessons)==8,'Expected eight lessons'
    for lesson in lessons:
        assert sum(s['minutes'] for s in lesson['slides'])==45
        assert len(lesson['slides'])<=30
    OUT.mkdir(parents=True,exist_ok=True)
    for lesson in lessons:teacher_script(lesson)
    if not args.scripts_only:guide(lessons,json.loads((ROOT/'lessons/setup-guide.json').read_text()))
    print(f'Built {len(lessons)} teacher scripts'+('' if args.scripts_only else ' and methodical guide'))
