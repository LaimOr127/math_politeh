"""Build published Word materials from the same sources as the website and decks.

Run with the document runtime supplied by Codex, then render every output with
the Documents skill. No generated screenshots or experimental claims are used.
"""
import json
from pathlib import Path
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'lessons/output'
SOURCES = [
    ('Python Software Foundation', 'Учебник Python 3', 'https://docs.python.org/3/tutorial/'),
    ('Python Software Foundation', 'Встроенные функции Python', 'https://docs.python.org/3/library/functions.html'),
    ('Microsoft', 'Python в Visual Studio Code', 'https://code.visualstudio.com/docs/python/python-tutorial'),
    ('Node.js', 'Документация HTTP и Crypto', 'https://nodejs.org/docs/latest-v24.x/api/'),
]


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
    sec.top_margin = sec.bottom_margin = Cm(1.8)
    sec.left_margin, sec.right_margin = Cm(2.4), Cm(1.8)
    for name in ('Normal', 'Title', 'Subtitle', 'Heading 1', 'Heading 2', 'Heading 3'):
        style = doc.styles[name]
        style.font.name = 'Times New Roman' if scientific else 'Arial'
        style.font.color.rgb = RGBColor(0, 0, 0)
        for border in style.element.xpath('./w:pPr/w:pBdr'):
            border.getparent().remove(border)
    normal = doc.styles['Normal']
    normal.font.size = Pt(12 if scientific else 10.5)
    normal.paragraph_format.line_spacing = 1.2 if scientific else 1.12
    normal.paragraph_format.space_after = Pt(7)
    doc.styles['Title'].font.size = Pt(25)
    for name, size in [('Heading 1', 18), ('Heading 2', 14), ('Heading 3', 11.5)]:
        style = doc.styles[name]
        style.font.size = Pt(size)
        style.font.bold = True
        style.paragraph_format.space_before = Pt(14)
        style.paragraph_format.space_after = Pt(7)
        style.paragraph_format.keep_with_next = True
    footer = sec.footer.paragraphs[0]
    footer.alignment = 2
    footer.add_run('Лаборатория Питона   ·   ')
    field = OxmlElement('w:fldSimple')
    field.set(qn('w:instr'), 'PAGE')
    footer._p.append(field)
    for run in footer.runs:
        run.font.size = Pt(9)
    doc.add_paragraph(title, style='Title')
    paragraph(doc, subtitle)
    return doc


def code(doc, value):
    """Append editable, unwrapped code preserving indentation."""
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(.3)
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(9)
    p.paragraph_format.line_spacing = 1.05
    p.paragraph_format.keep_together = True
    r = p.add_run(value.rstrip())
    r.font.name = 'Consolas'
    r.font.size = Pt(9.5)
    return p


def table(doc, headers, rows, widths):
    """Add a repeatable header table with explicit widths and visible borders."""
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
                p.paragraph_format.space_after = Pt(3)
                p.paragraph_format.line_spacing = 1.05
                for r in p.runs:
                    r.font.size = Pt(9)
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
    for title, text in entries:
        doc.add_heading(title, 2)
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


def scientific_guide(lessons):
    """Compile an evidence-bounded scientific and methodical report for the course."""
    doc = document('Разработка учебного комплекса по основам Python', 'Описание разработки и методика организации занятий в 5–6 классах', scientific=True)
    doc.add_heading('Аннотация', 1)
    paragraph(doc, 'В пособии описан учебный комплекс «Лаборатория Питона», включающий восемь занятий по основам Python, веб-приложение с последовательным прохождением заданий, презентации и сценарии преподавателя. Рассматриваются модель содержания, организация практической деятельности, архитектура программной части и способы проверки знаний. Представлены программы, входные данные, ожидаемый вывод и критерии оценки. Документ объединяет учебную и техническую составляющие проекта и предназначен для преподавателей и разработчиков образовательных ресурсов.')
    paragraph(doc, 'Python, обучение программированию, основная школа, учебный комплекс, формирующее оценивание, веб-приложение.', 'Ключевые слова:')
    doc.add_heading('Содержание', 1)
    for text in ['1 Цель и границы разработки', '2 Методика и организация обучения', '3 Программная архитектура', '4 Подготовка рабочего места', '5 Содержание восьми занятий', '6 Контроль результатов и план апробации', '7 Эксплуатация и развитие комплекса', 'Заключение', 'Источники', 'Приложение А Вопросы и ответы', 'Приложение Б Планирование занятий']:
        paragraph(doc, text)
    doc.add_heading('1 Цель и границы разработки', 1).paragraph_format.page_break_before = True
    paragraph(doc, 'Цель разработки состоит в создании согласованного комплекта материалов для первоначального освоения Python учащимися 5–6 классов. Объектом рассмотрения является организация начального обучения программированию. Предметом разработки выступает взаимодействие текстового объяснения, демонстрации, самостоятельной работы и обратной связи в рамках одного учебного маршрута.')
    paragraph(doc, 'Проект решает задачи последовательного введения базовых конструкций, обеспечения воспроизводимости примеров и сохранения результатов прохождения. Курс включает восемь занятий по 45 минут, то есть 360 минут учебной работы. Предварительная установка программ проводится отдельно. Для завершения курса не требуется создание учётной записи ученика.')
    paragraph(doc, 'Пособие описывает реализованные технические решения и предлагаемый порядок проведения занятий. Данные педагогического эксперимента отсутствуют. Поэтому положения о вовлечённости, мотивации и образовательной эффективности рассматриваются как направления последующей проверки, а не как установленные результаты.')
    doc.add_heading('2 Методика и организация обучения', 1)
    paragraph(doc, 'Материал организован по принципу наращивания сложности. Вывод текста предшествует переменным, переменные используются при вводе данных, сравнение подготавливает изучение ветвления. Циклы, списки и функции расширяют набор действий. Итоговый мини-проект объединяет уже рассмотренные средства без введения новой обязательной конструкции.')
    paragraph(doc, 'Рекомендуемая последовательность работы с примером включает прогноз результата, запуск сохранённой программы, сравнение фактического вывода с прогнозом и объяснение обнаруженного расхождения. Такая последовательность направлена на формирование представления об исполнении команд. Её результативность для конкретной группы требует наблюдения в ходе занятий.')
    paragraph(doc, 'Сюжет космической лаборатории и робот Пытик задают общий контекст. За успешное выполнение трёх вопросов урока приложение начисляет одну деталь робота. Награда показывает продвижение по маршруту. Практическое умение преподаватель оценивает отдельно по программе ученика, её результату и устному объяснению.')
    paragraph(doc, 'При затруднениях преподаватель сначала предлагает проверить парные знаки, отступы, имя переменной и сохранение файла. Далее ученик повторяет запуск. При быстром выполнении основного задания предлагается изменение данных или проверка дополнительного случая. Ученики, которым требуется больше времени, завершают обязательный пример и краткое объяснение его работы.')
    table(doc, ['Этап', 'Действие учащегося', 'Основание для обратной связи'], [
        ('Объяснение', 'Читает и прогнозирует вывод', 'Называет ожидаемый результат'),
        ('Практика', 'Создаёт и запускает файл', 'Код соответствует условию'),
        ('Проверка', 'Сопоставляет результат с условием', 'Объясняет ошибку или подтверждает прогноз'),
        ('Закрепление', 'Решает вопросы на сайте', 'Использует пояснение для следующей попытки'),
    ], [2.6, 6.3, 7.8])
    doc.add_heading('3 Программная архитектура', 1)
    paragraph(doc, 'Клиентская часть реализована средствами HTML, CSS и JavaScript без внешних зависимостей времени выполнения. Слой данных содержит сгенерированное представление уроков. Предметный слой Mission проверяет ответы и доступность следующего урока. ProgressStore валидирует снимок прогресса, выполняет миграцию старых данных и ограничивает доступ к браузерному хранилищу. Интерфейс передаёт действия пользователя этим слоям.')
    paragraph(doc, 'Единым источником содержания служат JSON-файлы lessons/content. Они содержат объяснения для сайта, программы, вопросы, слайды и сценарий преподавателя. Генератор синхронизирует данные сайта, а сборщики создают PPTX и DOCX. Автоматическая проверка обнаруживает устаревшее представление курса и выполняет основные примеры Python с заданным вводом.')
    paragraph(doc, 'Сервер Node.js обеспечивает проверку кода преподавателя и выдачу учебных файлов. При успешном входе создаётся случайный идентификатор сессии в cookie с атрибутами HttpOnly и SameSite Strict. Сессия действует восемь часов, прекращается при выходе и теряется при перезапуске сервера. Проверка выполняется также при прямом обращении к файлу, поэтому скрытие ссылки в интерфейсе не является механизмом защиты.')
    paragraph(doc, 'Коды задаются конфигурацией сервера. Кодовое слово lesson предназначено для простого общего доступа по требованию владельца. Такое слово не обеспечивает индивидуальную идентификацию преподавателя и не должно использоваться для защиты персональных данных. Для ограничения доступа к реальным закрытым материалам администратор задаёт собственные коды и использует HTTPS. Ограничение частоты попыток снижает возможность автоматического перебора.')
    paragraph(doc, 'Прогресс учащегося остаётся в конкретном браузере. Сервер не получает ответы на тесты и не запускает произвольный Python-код. При недоступности хранилища приложение продолжает работу в памяти вкладки. Ответы проверяются на клиенте, поэтому этот механизм подходит для самопроверки, но не для защищённого экзамена.')
    doc.add_heading('4 Подготовка рабочего места', 1)
    setup(doc, formal=True)
    doc.add_heading('5 Содержание восьми занятий', 1)
    paragraph(doc, 'Для каждой темы представлены ожидаемое действие учащегося, объяснение, единый пример и практическая работа. Подробная речь преподавателя находится в отдельных сценариях. В приложениях приведены вопросы самопроверки и все этапы слайдового планирования. Программы рассчитаны на Python 3; значения input вводятся в терминале. Преподаватель оценивает запуск файла, соответствие вывода условию и объяснение конструкции. В программе с вводом проверяются разные допустимые значения, в игре — оба исхода.')
    paragraph(doc, 'Описание синтаксиса и поведения стандартных функций опирается на официальную документацию Python [1, 2]. Порядок настройки редактора соответствует документации VS Code [3]. Первичным источником сведений о реализации комплекса служит репозиторий проекта [5].')
    for lesson in lessons:
        doc.add_heading(f"5 {int(lesson['id'])} {lesson['web']['title'].replace(':', '')}", 2)
        paragraph(doc, lesson['goal'], 'Планируемый результат:')
        for section in lesson['scientificSections']:
            doc.add_heading(section['title'], 3)
            paragraph(doc, section['text'])
        doc.add_heading('Пример для демонстрации', 3)
        run_block(doc, lesson)
        doc.add_heading('Практическая работа и возможное решение', 3)
        paragraph(doc, lesson['practice'])
        run_block(doc, lesson, solution=True)
    doc.add_heading('6 Контроль результатов и план апробации', 1)
    paragraph(doc, 'Техническая проверка включает доменные правила, сохранение и восстановление прогресса, начисление наград, соответствие данных сайта исходникам, исполнение примеров и защиту материалов преподавателя. Отдельно проверяются навигация клавиатурой, отображение на узком экране и обе цветовые темы. Успешное прохождение тестов не заменяет педагогическую оценку.')
    paragraph(doc, 'Для последующей апробации предлагается зафиксировать исходное умение читать короткий код, затем провести одинаковую итоговую практическую задачу. Учитываются доля самостоятельно выполненных заданий, виды ошибок, число подсказок и способность объяснить изменение результата. При сравнении групп необходимо описать состав, условия проведения и ограничения сопоставимости. Численные выводы в настоящем пособии не приводятся, поскольку измерения не выполнялись.')
    table(doc, ['Критерий', 'Наблюдаемое действие', 'Уровни'], [
        ('Корректность', 'Программа выполняет условие', '0 не выполнено; 1 после помощи; 2 самостоятельно'),
        ('Объяснение', 'Ученик объясняет ключевую команду', '0 отсутствует; 1 частично; 2 обоснованно'),
        ('Проверка', 'Ученик проверяет результат и варианты', '0 не проверяет; 1 один пример; 2 нужные случаи'),
    ], [2.5, 6.5, 7.7])
    paragraph(doc, 'Шкала является предложением для формирующего оценивания и не проходила психометрическую проверку. Сумма баллов не интерпретируется как стандартизированная оценка способности к программированию.')
    doc.add_heading('7 Эксплуатация и развитие комплекса', 1)
    paragraph(doc, 'Локальный запуск выполняется командой npm start после установки Node.js. Для контейнерного размещения применяется docker compose up --build -d. Контейнер запускает Node.js от непривилегированного пользователя. При изменении файлов образ пересобирается. Порт 8080 используется по умолчанию. Для HTTPS за обратным прокси задаются PUBLIC_ORIGIN и COOKIE_SECURE.')
    paragraph(doc, 'К дальнейшим направлениям развития относятся наблюдение за проведением занятий, корректировка сложности по данным апробации и подготовка иллюстрированного руководства установки для разных операционных систем. В представленном комплекте отсутствующие скриншоты не заменяются синтетическими изображениями интерфейса. При добавлении многопользовательской аналитики потребуется отдельная модель хранения и обработки данных.')
    doc.add_heading('Заключение', 1)
    paragraph(doc, 'Разработанный комплекс объединяет учебный маршрут из восьми тем, локальную практику Python, браузерную самопроверку и комплект материалов преподавателя. Общие источники содержания уменьшают риск расхождения формулировок и примеров между форматами. Серверная проверка доступа распространяется на скачивание файлов, а настройки темы и прогресс сохраняются в браузере. Педагогическая эффективность должна оцениваться по результатам последующей апробации с описанием условий и ограничений.')
    doc.add_heading('Источники', 1)
    for i, (author, title, url) in enumerate(SOURCES, 1):
        paragraph(doc, f'{i}. {author}. {title}. Электронный ресурс. URL: {url}')
    paragraph(doc, '5. Исходные материалы комплекса «Лаборатория Питона». Репозиторий проекта. URL: https://github.com/LaimOr127/math_politeh. JSON-файлы уроков, программный код и архитектурные решения являются первичными источниками описания реализации.')
    doc.add_heading('Приложение А Вопросы и ответы', 1).paragraph_format.page_break_before = True
    for lesson in lessons:
        doc.add_heading(f"Урок {int(lesson['id'])} {lesson['web']['title'].replace(':', '')}", 2)
        questions(doc, lesson)
    doc.add_heading('Приложение Б Планирование занятий', 1).paragraph_format.page_break_before = True
    paragraph(doc, 'Таблицы охватывают все 18 слайдов каждого занятия. Интервалы суммируются до 45 минут. Полная речь, действия и ответы приведены в сценариях соответствующих уроков.')
    for lesson in lessons:
        doc.add_heading(f"Урок {int(lesson['id'])} {lesson['web']['title'].replace(':', '')}", 2)
        elapsed = 0
        rows = []
        for i, slide in enumerate(lesson['slides'], 1):
            rows.append((f'{i}', f"{elapsed}–{elapsed+slide['minutes']}", slide['title']))
            elapsed += slide['minutes']
        table(doc, ['Слайд', 'Минуты', 'Тема'], rows, [1.4, 2.2, 13.1])
    doc.save(OUT / 'scientific-methodical-guide.docx')


def main():
    """Generate the ten published documents; fail if a lesson is incomplete."""
    lessons = [json.loads(p.read_text(encoding='utf-8')) for p in sorted((ROOT / 'lessons/content').glob('lesson-*.json'))]
    assert len(lessons) == 8
    for lesson in lessons:
        assert sum(slide['minutes'] for slide in lesson['slides']) == 45
    OUT.mkdir(parents=True, exist_ok=True)
    for lesson in lessons:
        teacher_script(lesson)
    student_guide(lessons)
    scientific_guide(lessons)
    print('Built eight teacher scripts, student guide and scientific methodical guide.')


if __name__ == '__main__':
    main()
