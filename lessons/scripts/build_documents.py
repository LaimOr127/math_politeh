"""Build published Word materials from the same sources as the website and decks.

Run with the document runtime supplied by Codex, then render every output with
the Documents skill. No generated screenshots or experimental claims are used.
"""
import argparse
import json
from pathlib import Path
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.shared import Cm, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from build_illustrations import build_course_figures

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'lessons/output'


def paragraph(doc, text, label=None):
    """Append a paragraph with an optional bold label and return it."""
    p = doc.add_paragraph()
    if label:
        p.add_run(label + ' ').bold = True
    p.add_run(text)
    return p


def document(title, subtitle, scientific=False):
    """Return a styled A4 document with page numbers and black headings."""
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.top_margin = sec.bottom_margin = Cm(2 if scientific else 1.8)
    sec.left_margin, sec.right_margin = (Cm(3), Cm(1.5)) if scientific else (Cm(2.4), Cm(1.8))
    for name in ('Normal', 'Title', 'Subtitle', 'Heading 1', 'Heading 2', 'Heading 3'):
        style = doc.styles[name]
        style.font.name = 'Times New Roman' if scientific else 'Arial'
        style.font.color.rgb = RGBColor(0, 0, 0)
        if scientific:
            fonts = style.element.get_or_add_rPr().get_or_add_rFonts()
            for attribute in list(fonts.attrib):
                if 'theme' in attribute.lower():
                    del fonts.attrib[attribute]
            for attribute in ('ascii', 'hAnsi', 'eastAsia', 'cs'):
                fonts.set(qn('w:' + attribute), 'Times New Roman')
        for border in style.element.xpath('./w:pPr/w:pBdr'):
            border.getparent().remove(border)
    normal = doc.styles['Normal']
    normal.font.size = Pt(14 if scientific else 10.5)
    normal.paragraph_format.line_spacing = 1.5 if scientific else 1.12
    normal.paragraph_format.space_after = Pt(0 if scientific else 7)
    if scientific:
        normal.paragraph_format.first_line_indent = Cm(1.25)
        normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        normal.paragraph_format.widow_control = True
    doc.styles['Title'].font.size = Pt(18 if scientific else 25)
    for name, size in [('Heading 1', 18), ('Heading 2', 14), ('Heading 3', 11.5)]:
        style = doc.styles[name]
        style.font.size = Pt(14 if scientific else size)
        style.font.bold = True
        style.paragraph_format.space_before = Pt(14)
        style.paragraph_format.space_after = Pt(7)
        style.paragraph_format.keep_with_next = True
        if scientific:
            style.paragraph_format.first_line_indent = Cm(1.25)
            style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    if scientific:
        doc.styles['Heading 1'].paragraph_format.page_break_before = True
        sec.different_first_page_header_footer = True
        doc.styles['Footer'].font.name = 'Times New Roman'
        doc.styles['Footer'].font.size = Pt(14)
    footer = sec.footer.paragraphs[0]
    footer.alignment = 1 if scientific else 2
    footer.paragraph_format.first_line_indent = Cm(0)
    if not scientific:
        footer.add_run('Лаборатория Питона   ·   ')
    field = OxmlElement('w:fldSimple')
    field.set(qn('w:instr'), 'PAGE')
    footer._p.append(field)
    for run in footer.runs:
        run.font.size = Pt(14 if scientific else 9)
    if scientific:
        p = doc.add_paragraph('Учебно-методическое пособие')
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.space_after = Cm(4.5)
    p = doc.add_paragraph(title, style='Title')
    if scientific:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.space_after = Pt(24)
    p = paragraph(doc, subtitle)
    if scientific:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Cm(0)
        p = paragraph(doc, 'Лаборатория Питона\nВосемь занятий по 45 минут')
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.space_before = Cm(2)
        p = paragraph(doc, '2026')
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.space_before = Cm(5)
    return doc


def code(doc, value):
    """Append editable, unwrapped code preserving indentation."""
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(.3)
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(9)
    p.paragraph_format.line_spacing = 1.05
    p.paragraph_format.keep_together = True
    r = p.add_run(value.rstrip())
    r.font.name = 'Consolas'
    r.font.size = Pt(12 if doc.styles['Normal'].font.name == 'Times New Roman' else 9.5)
    return p


def table(doc, headers, rows, widths):
    """Add a repeatable header table with explicit widths and visible borders."""
    scientific = doc.styles['Normal'].font.name == 'Times New Roman'
    if scientific:
        ratio = min(1, 16.5 / sum(widths))
        widths = [w * ratio for w in widths]
    t = doc.add_table(rows=1, cols=len(headers))
    t.autofit = False
    for c, width in zip(t.columns, widths):
        c.width = Cm(width)
    for cell, title in zip(t.rows[0].cells, headers):
        cell.text = title
        shade = OxmlElement('w:shd'); shade.set(qn('w:fill'), 'EAEAEA'); cell._tc.get_or_add_tcPr().append(shade)
        for r in cell.paragraphs[0].runs:
            r.bold = True
    repeat = OxmlElement('w:tblHeader'); t.rows[0]._tr.get_or_add_trPr().append(repeat)
    for values in rows:
        cells = t.add_row().cells
        for cell, value in zip(cells, values):
            cell.text = str(value)
    borders = OxmlElement('w:tblBorders')
    for side in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        edge = OxmlElement('w:' + side)
        for key, value in [('val', 'single'), ('sz', '5'), ('color', 'D9D9D9')]:
            edge.set(qn('w:' + key), value)
        borders.append(edge)
    t._tbl.tblPr.append(borders)
    for row in t.rows:
        row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
        for cell, width in zip(row.cells, widths):
            cell.width = Cm(width)
            cell.vertical_alignment = 1
            margins = OxmlElement('w:tcMar')
            for side in ('top', 'left', 'bottom', 'right'):
                e = OxmlElement('w:' + side); e.set(qn('w:w'), '90'); e.set(qn('w:type'), 'dxa'); margins.append(e)
            cell._tc.get_or_add_tcPr().append(margins)
            for p in cell.paragraphs:
                p.paragraph_format.first_line_indent = Cm(0)
                p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
                p.paragraph_format.space_after = Pt(3)
                p.paragraph_format.line_spacing = 1.05
                for r in p.runs:
                    r.font.size = Pt(12 if scientific else 9)
    if len(rows) <= 6:
        # Keep compact matrices together; avoids a truncated trailing row in LO.
        for row in t.rows[:-1]:
            for cell in row.cells:
                for p in cell.paragraphs:
                    p.paragraph_format.keep_with_next = True
    return t


def run_block(doc, lesson, solution=False):
    """Present stdin and captured stdout separately, avoiding invented terminal echo."""
    program = lesson['solution' if solution else 'code']
    input_text = lesson['solutionStdin' if solution else 'stdin']
    output_text = lesson['solutionOutput' if solution else 'output']
    code(doc, program)
    if input_text:
        paragraph(doc, input_text.strip().replace('\n', ', '), 'Данные для ввода в терминале:')
        paragraph(doc, 'Ниже показан только поток вывода программы. Ввод с клавиатуры не включён; приглашение input и следующий print могут находиться на одной строке.')
    paragraph(doc, 'Вывод программы').paragraph_format.keep_with_next = True
    code(doc, output_text)


def questions(doc, lesson):
    """Append the exact three website questions and explained answers."""
    for i, ex in enumerate(lesson['exercises'], 1):
        first = len(doc.paragraphs)
        paragraph(doc, f"{i}. {ex['prompt']}")
        options = ex.get('options', ex.get('lines'))
        for key, text in options:
            paragraph(doc, f'{key}) {text}')
        labels = dict(options)
        answer = ex['answer']
        readable = ' → '.join(labels[key] for key in answer) if isinstance(answer, list) else labels[answer]
        paragraph(doc, readable + '. ' + ex['feedback']['correct'], 'Ответ:')
        paragraph(doc, ex['feedback']['incorrect'], 'Подсказка при ошибке:')
        for p in doc.paragraphs[first:-1]:
            p.paragraph_format.keep_with_next = True


def setup(doc, formal=False):
    """Append factual setup instructions without pretending missing images exist."""
    entries = [
        ('Установка Python', 'С официальной страницы python.org/downloads загружается Python 3. На Windows выбирается пользовательская установка; параметр Add Python to PATH включается, если он доступен. После установки в новом терминале выполняется python --version. На macOS и Linux обычно используется команда python3 --version.'),
        ('Установка редактора', 'VS Code загружается с code.visualstudio.com/download. В разделе Extensions устанавливается расширение Python от Microsoft. Редактор перезапускается после установки Python, чтобы получить обновлённые переменные среды.'),
        ('Учебная папка', 'Создаётся отдельная папка python-course. В VS Code выбирается File → Open Folder. В Explorer создаётся файл greeting.py. В файл записывается print("Привет, мир!"); изменения сохраняются сочетанием Ctrl+S, на macOS Cmd+S.'),
        ('Выбор интерпретатора', 'Через палитру команд Ctrl+Shift+P, на macOS Cmd+Shift+P, вызывается Python: Select Interpreter. Выбирается установленный Python 3. Команда Run Python File in Terminal запускает сохранённый файл. Ответ на input вводится в панели Terminal и завершается Enter.'),
        ('Проверка готовности', 'Среда подготовлена, если файл .py запускается, терминал показывает ожидаемую строку и после изменения сообщения повторный запуск отражает новое значение. Установка и устранение системных ошибок проводятся до первого 45-минутного занятия.'),
    ]
    for i, (title, text) in enumerate(entries, 1):
        doc.add_heading(f'4.{i} {title}' if formal else title, 2)
        paragraph(doc, text)
    paragraph(doc, 'Для освоения Python Docker не требуется. Для запуска самого сайта нужен Node.js 22 или новее; контейнерный вариант предназначен для размещения сервера.')


def teacher_script(lesson):
    """Build a complete slide-aligned scenario with timing, speech and solutions."""
    doc = document(f"Сценарий занятия {int(lesson['id'])}", lesson['title'] + ' · 5–6 классы · 45 минут')
    paragraph(doc, lesson['goal'], 'Цель занятия:')
    paragraph(doc, 'До занятия подготавливаются Python 3, VS Code и расширение Python. Каждый ученик работает в собственной папке. Установка среды не включается в 45 минут. Презентация и данный сценарий собраны из одного источника.')
    elapsed = 0
    rows = []
    for i, slide in enumerate(lesson['slides'], 1):
        rows.append((i, f"{elapsed}–{elapsed + slide['minutes']}", slide['title']))
        elapsed += slide['minutes']
    table(doc, ['Слайд', 'Минуты', 'Этап занятия'], rows, [1.4, 2.2, 13.1])
    doc.add_heading('Проведение занятия', 1).paragraph_format.page_break_before = True
    elapsed = 0
    for i, slide in enumerate(lesson['slides'], 1):
        doc.add_heading(f"{i} {slide['title'].replace(':', '').replace('—', '')}", 2)
        paragraph(doc, f"{elapsed}–{elapsed + slide['minutes']} мин", 'Время:').paragraph_format.keep_with_next = True
        paragraph(doc, slide['teacher'])
        paragraph(doc, slide['action'], 'Действия преподавателя:')
        if slide.get('code'):
            code(doc, slide['code'])
        paragraph(doc, slide['question'], 'Вопрос:').paragraph_format.keep_with_next = True
        paragraph(doc, slide['answer'], 'Ожидаемый ответ:')
        if slide.get('output'):
            paragraph(doc, 'Вывод программы без эха клавиатуры')
            code(doc, slide['output'])
        if slide['animation']:
            paragraph(doc, 'Сначала собираются предположения. Затем один щелчок в режиме показа открывает ответ или результат; в PDF ответ виден сразу.')
        elapsed += slide['minutes']
    doc.add_heading('Практическая работа и оценка', 1)
    paragraph(doc, lesson['practice'], 'Задание:')
    run_block(doc, lesson, solution=True)
    paragraph(doc, 'Работа оценивается по запуску программы, совпадению результата с условием и объяснению ключевого действия. Исправление после подсказки допускается. Угадывание ответа на сайте само по себе не подтверждает умение написать программу.')
    questions(doc, lesson)
    doc.save(OUT / f"lesson-{lesson['id']}-teacher-script.docx")


def student_guide(lessons):
    """Build the student companion using shared prose and exact lesson programs."""
    doc = document('Python в космической лаборатории', 'Пособие ученика 5–6 класса · восемь занятий с Пытиком')
    paragraph(doc, 'Пособие помогает подготовить рабочее место, прочитать объяснения и написать собственные программы. Изучайте темы по порядку. После каждого примера сначала предположите результат, затем сохраните файл и запустите его в VS Code.')
    setup(doc)
    for lesson in lessons:
        doc.add_heading(f"Урок {int(lesson['id'])} {lesson['web']['title'].replace(':', '')}", 1)
        paragraph(doc, lesson['goal'], 'Цель:')
        for section in lesson['web']['sections']:
            doc.add_heading(section['title'], 2)
            for text in section['paragraphs']:
                paragraph(doc, text)
            if section.get('code'):
                code(doc, section['code'])
            if section.get('output'):
                paragraph(doc, 'Результат примера')
                code(doc, section['output'])
        doc.add_heading('Общий пример занятия', 2)
        run_block(doc, lesson)
        doc.add_heading('Самостоятельная работа', 2)
        paragraph(doc, lesson['practice'])
        doc.add_heading('Возможное решение', 2)
        run_block(doc, lesson, solution=True)
    doc.save(OUT / 'new-learning-guide.docx')


def structural_heading(doc, title):
    """Add a centred, unnumbered structural element on its own page."""
    p = doc.add_heading(title, 1)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    return p


def appendix_heading(doc, letter, title):
    """Start one appendix without inventing institution-specific title metadata."""
    structural_heading(doc, 'ПРИЛОЖЕНИЕ ' + letter)
    p = paragraph(doc, title)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.keep_with_next = True
    for run in p.runs:
        run.bold = True


def scientific_contents(doc, lessons):
    """Create a native editable TOC with cached entries to materialise after render."""
    entries = [(t, t) for t in ('ВВЕДЕНИЕ', '1 Цель и границы разработки',
               '2 Методика и организация обучения', '3 Программная архитектура',
               '4 Подготовка рабочего места', '5 Содержание восьми занятий')]
    entries.extend((f"5.{int(lesson['id'])} {lesson['web']['title'].replace(':', '')}",
                    f"5.{int(lesson['id'])} {lesson['web']['title'].replace(':', '')}") for lesson in lessons)
    entries.extend((t, t) for t in ('6 Контроль результатов и план апробации',
                   '7 Эксплуатация и развитие комплекса', 'ЗАКЛЮЧЕНИЕ',
                   'СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ'))
    entries.extend((f'ПРИЛОЖЕНИЕ {letter} {title}', f'ПРИЛОЖЕНИЕ {letter}') for letter, title in (
        ('А', 'Вопросы и ответы'), ('Б', 'Планирование занятий'), ('В', 'Сценарии проведения занятий')))
    structural_heading(doc, 'СОДЕРЖАНИЕ')
    for i, (title, target) in enumerate(entries):
        p = doc.add_paragraph()
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.tab_stops.add_tab_stop(Cm(16.5), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
        p.paragraph_format.space_after = Pt(0)
        if i == 0:
            start = OxmlElement('w:fldChar'); start.set(qn('w:fldCharType'), 'begin')
            p.add_run()._r.append(start)
            instruction = OxmlElement('w:instrText')
            instruction.set(qn('xml:space'), 'preserve')
            instruction.text = ' TOC \\o "1-2" \\h \\z \\u '
            p.add_run()._r.append(instruction)
            separate = OxmlElement('w:fldChar'); separate.set(qn('w:fldCharType'), 'separate')
            p.add_run()._r.append(separate)
        mark = OxmlElement('w:bookmarkStart')
        mark.set(qn('w:id'), str(1000+i)); mark.set(qn('w:name'), f'_course_toc_{i}')
        p._p.append(mark)
        p.add_run(title + '\t')
        p.add_run('1')
        end = OxmlElement('w:bookmarkEnd'); end.set(qn('w:id'), str(1000+i)); p._p.append(end)
        if i == len(entries)-1:
            finish = OxmlElement('w:fldChar'); finish.set(qn('w:fldCharType'), 'end')
            p.add_run()._r.append(finish)
    build = ROOT / '.build/scientific-review'
    build.mkdir(parents=True, exist_ok=True)
    (build/'toc-entries.json').write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding='utf-8')


def scientific_figure(doc, number, file, title, explanation):
    """Embed an original 300 dpi figure with reference, alternative text and caption."""
    paragraph(doc, f'{explanation} На рисунке {number} представлена соответствующая схема.')
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.line_spacing = 1
    picture = p.add_run().add_picture(str(ROOT/'lessons/illustrations'/file), width=Cm(16.5))
    picture._inline.docPr.set('descr', f'{title}. Авторская схема по исходникам учебного комплекса.')
    p = paragraph(doc, f'Рисунок {number} — {title}')
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.line_spacing = 1
    p.paragraph_format.space_after = Pt(12)


def scientific_table(doc, title, headers, rows, widths):
    """Pair each numbered table with its caption, keeping it inside the text area."""
    p = paragraph(doc, f'Таблица {len(doc.tables)+1} — {title}')
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_before = Pt(8)
    return table(doc, headers, rows, widths)


def scientific_guide(lessons):
    """Compile an evidence-bounded scientific and methodical report for the course."""
    doc = document('Разработка учебного комплекса по основам Python', 'Описание разработки и методика организации занятий в 5–6 классах', scientific=True)
    build_course_figures(lessons)
    structural_heading(doc, 'РЕФЕРАТ')
    paragraph(doc, 'В пособии описан учебный комплекс «Лаборатория Питона», включающий восемь занятий по основам Python, веб-приложение с последовательным прохождением заданий, презентации и сценарии преподавателя. Рассматриваются модель содержания, организация практической деятельности, архитектура программной части и способы проверки знаний. Представлены программы, входные данные, ожидаемый вывод и критерии оценки. Документ объединяет учебную и техническую составляющие проекта и предназначен для преподавателей и разработчиков образовательных ресурсов.')
    paragraph(doc, 'Python, обучение программированию, основная школа, учебный комплекс, формирующее оценивание, веб-приложение.', 'Ключевые слова:')
    paragraph(doc, 'Документ содержит 11 авторских схем, 10 таблиц и три приложения. В приложения включены вопросы с ответами, поурочное планирование и полные сценарии работы с 144 слайдами. Схемы поясняют содержание и архитектуру; они не являются снимками экрана. Приведённые учебные примеры воспроизводимы по общим исходным данным курса.')
    scientific_contents(doc, lessons)
    structural_heading(doc, 'ВВЕДЕНИЕ')
    paragraph(doc, 'Начальное обучение программированию требует согласования объяснения, демонстрации и самостоятельной работы. В настоящем пособии рассматривается учебный комплекс «Лаборатория Питона» для учащихся 5–6 классов. Его содержание и программная реализация представлены в открытом репозитории [1]. Работа объединяет описание проекта и материалы, необходимые преподавателю для проведения восьми занятий.')
    paragraph(doc, 'Для оформления применены положения ГОСТ 7.32–2017, относящиеся к странице, основному тексту, рубрикации, иллюстрациям, таблицам и приложениям [2]. Библиографические описания электронных ресурсов составлены с учётом ГОСТ Р 7.0.100–2018 [3]. Документ имеет характер учебно-методического пособия. В работе разграничиваются результаты технической проверки и планируемая педагогическая апробация.')
    doc.add_heading('1 Цель и границы разработки', 1).paragraph_format.page_break_before = True
    paragraph(doc, 'Цель разработки состоит в создании согласованного комплекта материалов для первоначального освоения Python учащимися 5–6 классов. Объектом рассмотрения является организация начального обучения программированию. Предметом разработки выступает взаимодействие текстового объяснения, демонстрации, самостоятельной работы и обратной связи в рамках одного учебного маршрута.')
    paragraph(doc, 'Проект решает задачи последовательного введения базовых конструкций, обеспечения воспроизводимости примеров и сохранения результатов прохождения. Курс включает восемь занятий по 45 минут, то есть 360 минут учебной работы. Предварительная установка программ проводится отдельно. Для завершения курса не требуется создание учётной записи ученика.')
    paragraph(doc, 'Пособие описывает реализованные технические решения и предлагаемый порядок проведения занятий. Данные педагогического эксперимента отсутствуют. Поэтому положения о вовлечённости, мотивации и образовательной эффективности рассматриваются как направления последующей проверки, а не как установленные результаты.')
    scientific_figure(doc, 1, 'course-sequence.png', 'Последовательность тем учебного курса', 'Переход между темами определяется расширением набора доступных ученику конструкций. Итоговая игра объединяет ранее изученные действия, а не вводит новый обязательный синтаксис.')
    doc.add_heading('2 Методика и организация обучения', 1)
    paragraph(doc, 'Сложность материала возрастает последовательно. Вывод текста предшествует переменным и вводу данных, сравнение подготавливает изучение ветвления. Циклы, списки и функции расширяют набор действий. Мини-проект объединяет изученные конструкции.')
    paragraph(doc, 'Работа с примером включает прогноз результата, запуск программы, сравнение вывода с прогнозом и объяснение расхождений. Метод направлен на осмысленное чтение команд; его результативность для конкретной группы подлежит проверке в ходе занятий.')
    paragraph(doc, 'Общий контекст задают космическая лаборатория и робот Пытик. За три успешно решённых вопроса урока начисляется одна деталь робота. Награда отражает продвижение; практическое умение оценивается отдельно по программе и объяснению ученика.')
    paragraph(doc, 'При затруднении проверяются парные знаки, отступы, имя переменной и сохранение файла. После исправления выполняется повторный запуск. Дополнительная работа состоит в изменении данных и проверке новых случаев. Обязательный результат — работающий пример и объяснение его действия.')
    scientific_table(doc, 'Действия учащегося и основания для обратной связи', ['Этап', 'Действие учащегося', 'Основание для обратной связи'], [
        ('Объяснение', 'Читает и прогнозирует вывод', 'Называет ожидаемый результат'),
        ('Практика', 'Создаёт и запускает файл', 'Код соответствует условию'),
        ('Проверка', 'Сопоставляет результат с условием', 'Объясняет ошибку или подтверждает прогноз'),
        ('Закрепление', 'Решает вопросы на сайте', 'Использует пояснение для следующей попытки'),
    ], [3.2, 6.2, 7.1])
    doc.add_heading('3 Программная архитектура', 1)
    paragraph(doc, 'Клиентская часть реализована средствами HTML, CSS и JavaScript без внешних зависимостей времени выполнения. Слой данных содержит сгенерированное представление уроков. Предметный слой Mission проверяет ответы и доступность следующего урока. ProgressStore валидирует снимок прогресса, выполняет миграцию старых данных и ограничивает доступ к браузерному хранилищу. Интерфейс передаёт действия пользователя этим слоям.')
    paragraph(doc, 'Единым источником содержания служат JSON-файлы lessons/content. Они содержат объяснения для сайта, программы, вопросы, слайды и сценарий преподавателя. Генератор синхронизирует данные сайта, а сборщики создают PPTX и DOCX. Автоматическая проверка обнаруживает устаревшее представление курса и выполняет основные примеры Python с заданным вводом.')
    scientific_figure(doc, 2, 'shared-content.png', 'Формирование материалов из единого источника', 'Связь между форматами обеспечивается генерацией и проверкой содержимого. Смысловые изменения вносятся в исходные уроки, после чего создаются производные материалы.')
    paragraph(doc, 'Сервер Node.js обеспечивает проверку кода преподавателя и выдачу учебных файлов. При успешном входе создаётся случайный идентификатор сессии в cookie с атрибутами HttpOnly и SameSite Strict. Сессия действует восемь часов, прекращается при выходе и теряется при перезапуске сервера. Проверка выполняется также при прямом обращении к файлу, поэтому скрытие ссылки в интерфейсе не является механизмом защиты.')
    paragraph(doc, 'Коды задаются конфигурацией сервера. Кодовое слово lesson предназначено для простого общего доступа по требованию владельца. Такое слово не обеспечивает индивидуальную идентификацию преподавателя и не должно использоваться для защиты персональных данных. Для ограничения доступа к реальным закрытым материалам администратор задаёт собственные коды и использует HTTPS. Ограничение частоты попыток снижает возможность автоматического перебора.')
    paragraph(doc, 'Прогресс учащегося остаётся в конкретном браузере. Сервер не получает ответы на тесты и не запускает произвольный Python-код. При недоступности хранилища приложение продолжает работу в памяти вкладки. Ответы проверяются на клиенте, поэтому этот механизм подходит для самопроверки, но не для защищённого экзамена.')
    paragraph(doc, 'Сервер использует встроенные модули Node.js. Назначение модулей HTTP и Crypto описано в официальной документации [4]. При описании проекта различаются реализованный механизм общего кода и индивидуальная идентификация пользователя; последняя в текущую архитектуру не входит.')
    scientific_figure(doc, 3, 'application-architecture.png', 'Разделение ученического интерфейса и доступа преподавателя', 'Учебные ответы и настройки обрабатываются в браузере. Доступ к преподавательским файлам определяется серверной сессией; проверка применяется и к прямым запросам файлов.')
    doc.add_heading('4 Подготовка рабочего места', 1)
    setup(doc, formal=True)
    paragraph(doc, 'Последовательность выбора интерпретатора и запуска файла уточняется по официальному руководству VS Code [5]. Подготовку среды следует завершать до начала урока, чтобы технические затруднения не подменяли учебную практику.')
    doc.add_heading('5 Содержание восьми занятий', 1)
    paragraph(doc, 'Для каждой темы представлены ожидаемое действие учащегося, объяснение, единый пример и практическая работа. Подробная речь преподавателя находится в отдельных сценариях. В приложениях приведены вопросы самопроверки и все этапы слайдового планирования. Программы рассчитаны на Python 3; значения input вводятся в терминале. Преподаватель оценивает запуск файла, соответствие вывода условию и объяснение конструкции. В программе с вводом проверяются разные допустимые значения, в игре — оба исхода.')
    paragraph(doc, 'Описание синтаксиса и поведения стандартных функций опирается на официальную документацию Python [6, 7]. Учебные формулировки адаптированы к начальному уровню и не заменяют справочник языка.')
    figures = [
        ('sequence', 'Последовательное исполнение команд вывода', 'Каждая команда print выполняется после предыдущей. Строки вывода соответствуют порядку команд в файле.'),
        ('binding', 'Изменение связи имени переменной со строковым значением', 'При повторном присваивании имя name связывается с новым значением. Ранее выведенная строка при этом не изменяется.'),
        ('conversion', 'Преобразование введённой строки в целое число', 'Функция input возвращает строку. Преобразование int позволяет выполнить арифметическую операцию; произвольная строка не обязана быть допустимым целым числом.'),
        ('branch', 'Выбор одного блока условной конструкции', 'После вычисления условия выполняется только одна из ветвей if и else. Для проверки программы необходимы примеры, при которых условие принимает оба значения.'),
        ('range', 'Последовательность значений управляющей переменной цикла', 'Конструкция for последовательно связывает переменную с элементами диапазона. Правая граница range не включается в результат.'),
        ('index', 'Индексы элементов списка', 'Индекс определяет позицию элемента в упорядоченном наборе. Добавление элемента в конец не изменяет индексы ранее находившихся в списке элементов.'),
        ('call', 'Различие определения и вызова функции', 'Определение функции создаёт именованное действие. Тело функции выполняется при вызове; повторный вызов повторно выполняет тело.'),
        ('project', 'Проверка результата одной попытки в итоговой игре', 'В данном проекте число сравнивается с заранее заданным секретом. После сообщения программа завершается; повторная попытка требует нового запуска.'),
    ]
    for lesson in lessons:
        doc.add_heading(f"5.{int(lesson['id'])} {lesson['web']['title'].replace(':', '')}", 2)
        paragraph(doc, lesson['goal'], 'Планируемый результат:')
        for j, section in enumerate(lesson['scientificSections'], 1):
            doc.add_heading(f"5.{int(lesson['id'])}.{j} {section['title']}", 3)
            paragraph(doc, section['text'])
        suffix, title, explanation = figures[int(lesson['id'])-1]
        scientific_figure(doc, int(lesson['id'])+3, f"lesson-{lesson['id']}-{suffix}.png", title, explanation)
        doc.add_heading(f"5.{int(lesson['id'])}.{len(lesson['scientificSections'])+1} Пример для демонстрации", 3)
        run_block(doc, lesson)
        doc.add_heading(f"5.{int(lesson['id'])}.{len(lesson['scientificSections'])+2} Практическая работа и возможное решение", 3)
        paragraph(doc, lesson['practice'])
        run_block(doc, lesson, solution=True)
    doc.add_heading('6 Контроль результатов и план апробации', 1)
    paragraph(doc, 'Техническая проверка включает доменные правила, сохранение и восстановление прогресса, начисление наград, соответствие данных сайта исходникам, исполнение примеров и защиту материалов преподавателя. Отдельно проверяются навигация клавиатурой, отображение на узком экране и обе цветовые темы. Успешное прохождение тестов не заменяет педагогическую оценку.')
    paragraph(doc, 'Для последующей апробации предлагается зафиксировать исходное умение читать короткий код, затем провести одинаковую итоговую практическую задачу. Учитываются доля самостоятельно выполненных заданий, виды ошибок, число подсказок и способность объяснить изменение результата. При сравнении групп необходимо описать состав, условия проведения и ограничения сопоставимости. Численные выводы в настоящем пособии не приводятся, поскольку измерения не выполнялись.')
    scientific_table(doc, 'Предлагаемые критерии формирующего оценивания', ['Критерий', 'Наблюдаемое действие', 'Уровни'], [
        ('Корректность', 'Программа выполняет условие', '0 не выполнено; 1 после помощи; 2 самостоятельно'),
        ('Объяснение', 'Ученик объясняет ключевую команду', '0 отсутствует; 1 частично; 2 обоснованно'),
        ('Проверка', 'Ученик проверяет результат и варианты', '0 не проверяет; 1 один пример; 2 нужные случаи'),
    ], [3.1, 6.3, 7.1])
    paragraph(doc, 'Шкала является предложением для формирующего оценивания и не проходила психометрическую проверку. Сумма баллов не интерпретируется как стандартизированная оценка способности к программированию.')
    doc.add_heading('7 Эксплуатация и развитие комплекса', 1)
    paragraph(doc, 'Локальный запуск выполняется командой npm start после установки Node.js. Для контейнерного размещения применяется docker compose up --build -d. Контейнер запускает Node.js от непривилегированного пользователя. При изменении файлов образ пересобирается. Порт 8080 используется по умолчанию. Для HTTPS за обратным прокси задаются PUBLIC_ORIGIN и COOKIE_SECURE.')
    paragraph(doc, 'К дальнейшим направлениям развития относятся наблюдение за проведением занятий, корректировка сложности по данным апробации и подготовка иллюстрированного руководства установки для разных операционных систем. В представленном комплекте отсутствующие скриншоты не заменяются синтетическими изображениями интерфейса. При добавлении многопользовательской аналитики потребуется отдельная модель хранения и обработки данных.')
    structural_heading(doc, 'ЗАКЛЮЧЕНИЕ')
    paragraph(doc, 'Разработанный комплекс объединяет учебный маршрут из восьми тем, локальную практику Python, браузерную самопроверку и комплект материалов преподавателя. Общие источники содержания уменьшают риск расхождения формулировок и примеров между форматами. Серверная проверка доступа распространяется на скачивание файлов, а настройки темы и прогресс сохраняются в браузере. Педагогическая эффективность должна оцениваться по результатам последующей апробации с описанием условий и ограничений.')
    structural_heading(doc, 'СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ')
    references = [
        'Лаборатория Питона : исходные материалы учебного комплекса / LaimOr127. — URL: https://github.com/LaimOr127/math_politeh (дата обращения: 12.11.2026). — Текст : электронный.',
        'ГОСТ 7.32–2017. Система стандартов по информации, библиотечному и издательскому делу. Отчет о научно-исследовательской работе. Структура и правила оформления : введён 2018-07-01. — URL: https://internet-law.ru/documents/dop_documents/1/gost_11847/0/gost.html (дата обращения: 12.11.2026). — Текст : электронный.',
        'ГОСТ Р 7.0.100–2018. Система стандартов по информации, библиотечному и издательскому делу. Библиографическая запись. Библиографическое описание. Общие требования и правила составления : введён 2019-07-01. — URL: https://rags.ru/documents/prod/gost-r_gosudarstvennyj-standart/28/gost_13147.html (дата обращения: 12.11.2026). — Текст : электронный.',
        'Node.js v24 documentation / Node.js. — URL: https://nodejs.org/docs/latest-v24.x/api/ (дата обращения: 12.11.2026). — Текст : электронный.',
        'Getting Started with Python in VS Code / Microsoft. — URL: https://code.visualstudio.com/docs/python/python-tutorial (дата обращения: 12.11.2026). — Текст : электронный.',
        'The Python Tutorial / Python Software Foundation. — URL: https://docs.python.org/3/tutorial/ (дата обращения: 12.11.2026). — Текст : электронный.',
        'Built-in Functions / Python Software Foundation. — URL: https://docs.python.org/3/library/functions.html (дата обращения: 12.11.2026). — Текст : электронный.',
    ]
    for i, reference in enumerate(references, 1):
        p = paragraph(doc, f'{i}. {reference}')
        p.paragraph_format.keep_together = True
    appendix_heading(doc, 'А', 'Вопросы и ответы')
    for lesson in lessons:
        doc.add_heading(f"А.{int(lesson['id'])} {lesson['web']['title'].replace(':', '')}", 2)
        questions(doc, lesson)
    appendix_heading(doc, 'Б', 'Планирование занятий')
    paragraph(doc, 'Каждая таблица содержит 18 слайдов и 45 минут занятия. Полные сценарии представлены в приложении В.')
    for lesson in lessons:
        heading = doc.add_heading(f"Б.{int(lesson['id'])} {lesson['web']['title'].replace(':', '')}", 2)
        heading.paragraph_format.page_break_before = int(lesson['id']) > 1
        elapsed = 0
        rows = []
        for i, slide in enumerate(lesson['slides'], 1):
            rows.append((f'{i}', f"{elapsed}–{elapsed+slide['minutes']}", slide['title']))
            elapsed += slide['minutes']
        scientific_table(doc, f"План занятия {int(lesson['id'])}", ['Слайд', 'Минуты', 'Тема'], rows, [1.9, 2.2, 12.4])
    appendix_heading(doc, 'В', 'Сценарии проведения занятий')
    paragraph(doc, 'Приложение объединяет все сценарии преподавателя. Речь, вопросы, ответы и действия воспроизводятся по исходникам уроков. Прямая речь адресована детям и сохраняет разговорный учебный регистр; аналитические разделы пособия написаны в научном стиле. Вместе с программами раздела 5, вопросами приложения А и планами приложения Б эти материалы позволяют провести весь курс без обращения к отдельным Word-файлам.')
    for lesson in lessons:
        p = doc.add_heading(f"В.{int(lesson['id'])} {lesson['web']['title'].replace(':', '')}", 2)
        p.paragraph_format.page_break_before = int(lesson['id']) > 1
        paragraph(doc, lesson['goal'], 'Цель занятия:')
        elapsed = 0
        for i, slide in enumerate(lesson['slides'], 1):
            doc.add_heading(f"В.{int(lesson['id'])}.{i} {slide['title'].replace(':', '')}", 3)
            paragraph(doc, f"{elapsed}–{elapsed+slide['minutes']} мин", 'Время:').paragraph_format.keep_with_next = True
            paragraph(doc, slide['teacher'], 'Речь преподавателя:')
            paragraph(doc, slide['action'], 'Действие преподавателя:')
            if slide.get('code'):
                code(doc, slide['code'])
            paragraph(doc, slide['question'], 'Вопрос:').paragraph_format.keep_with_next = True
            paragraph(doc, slide['answer'], 'Ожидаемый ответ:')
            if slide.get('output'):
                paragraph(doc, 'Вывод демонстрационного примера').paragraph_format.keep_with_next = True
                code(doc, slide['output'])
            if slide['animation']:
                paragraph(doc, 'После обсуждения один щелчок в режиме показа раскрывает ответ. В печатной версии ответ доступен сразу.')
            elapsed += slide['minutes']
    doc.save(OUT / 'scientific-methodical-guide.docx')


def main():
    """Generate the ten published documents; fail if a lesson is incomplete."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scientific-only', action='store_true', help='Rebuild only the unified illustrated guide')
    args = parser.parse_args()
    lessons = [json.loads(p.read_text(encoding='utf-8')) for p in sorted((ROOT / 'lessons/content').glob('lesson-*.json'))]
    assert len(lessons) == 8
    for lesson in lessons:
        assert sum(slide['minutes'] for slide in lesson['slides']) == 45
    OUT.mkdir(parents=True, exist_ok=True)
    if not args.scientific_only:
        for lesson in lessons:
            teacher_script(lesson)
        student_guide(lessons)
    scientific_guide(lessons)
    print('Built scientific guide; render and materialise contents before publication.')


if __name__ == '__main__':
    main()
