"""Build Java teacher scripts and the combined scientific guide from canonical content."""
import json, re, sys
from pathlib import Path
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'lessons/scripts'))
from build_documents import table as shared_table
C=json.loads((ROOT/'java-course/content/course.json').read_text(encoding='utf-8'))
OUT=ROOT/'java-course/output';OUT.mkdir(parents=True,exist_ok=True)
REVIEW=ROOT/'.build/java-review';REVIEW.mkdir(parents=True,exist_ok=True)

def para(doc,text,style=None):
    p=doc.add_paragraph(text,style)
    if '\n' in text:p.paragraph_format.alignment=WD_ALIGN_PARAGRAPH.LEFT
    return p
def code(doc,value):
    lines=value.rstrip().splitlines()
    for index,line in enumerate(lines):
        p=doc.add_paragraph();p.paragraph_format.first_line_indent=Cm(0);p.paragraph_format.left_indent=Cm(.15)
        p.paragraph_format.alignment=WD_ALIGN_PARAGRAPH.LEFT;p.paragraph_format.line_spacing=1.05
        p.paragraph_format.space_after=Pt(0);p.paragraph_format.keep_with_next=len(lines)<=30 and index<len(lines)-1;r=p.add_run(line or ' ');r.font.name='Consolas';r.font.size=Pt(10)

def newdoc(title,subtitle,scientific=False):
    doc=Document();sec=doc.sections[0];sec.page_width=Cm(21);sec.page_height=Cm(29.7)
    sec.left_margin=Cm(3 if scientific else 2.3);sec.right_margin=Cm(1.5 if scientific else 1.8)
    sec.top_margin=sec.bottom_margin=Cm(2);sec.different_first_page_header_footer=scientific
    for name in ('Normal','Title','Subtitle','Heading 1','Heading 2','Heading 3'):
        s=doc.styles[name]
        for border in s.element.xpath('./w:pPr/w:pBdr'):border.getparent().remove(border)
        s.font.name='Times New Roman' if scientific else 'Arial';s.font.color.rgb=RGBColor(0,0,0)
        rf=s.element.get_or_add_rPr().get_or_add_rFonts()
        for attr in list(rf.attrib):
            if 'theme' in attr.lower():del rf.attrib[attr]
        for attr in ('ascii','hAnsi','eastAsia','cs'):rf.set(qn('w:'+attr),s.font.name)
    normal=doc.styles['Normal'];normal.font.size=Pt(14 if scientific else 11)
    normal.paragraph_format.line_spacing=1.5 if scientific else 1.15
    normal.paragraph_format.space_after=Pt(0 if scientific else 7)
    normal.paragraph_format.first_line_indent=Cm(1.25 if scientific else 0)
    normal.paragraph_format.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY if scientific else WD_ALIGN_PARAGRAPH.LEFT
    for n,size in [('Title',18 if scientific else 25),('Heading 1',14 if scientific else 18),('Heading 2',14 if scientific else 14),('Heading 3',14 if scientific else 12)]:
        doc.styles[n].font.size=Pt(size);doc.styles[n].paragraph_format.first_line_indent=Cm(0)
        doc.styles[n].paragraph_format.keep_with_next=True
    doc.styles['Heading 1'].paragraph_format.page_break_before=scientific
    footer=sec.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.CENTER;footer.paragraph_format.first_line_indent=Cm(0)
    field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)
    doc.styles['Footer'].font.name='Times New Roman' if scientific else 'Arial';doc.styles['Footer'].font.size=Pt(14 if scientific else 10)
    if scientific:
        p=para(doc,'Учебно-методическое пособие');p.alignment=1;p.paragraph_format.first_line_indent=Cm(0);p.paragraph_format.space_after=Cm(4)
    p=para(doc,title,'Title');p.alignment=1 if scientific else 0;p.paragraph_format.first_line_indent=Cm(0)
    p=para(doc,subtitle);p.paragraph_format.first_line_indent=Cm(0)
    if scientific:
        p.alignment=1
        p=para(doc,'Курс для 10–11 классов\nДесять занятий по 90 минут');p.alignment=1;p.paragraph_format.first_line_indent=Cm(0);p.paragraph_format.space_before=Cm(2)
        p=para(doc,'2026');p.alignment=1;p.paragraph_format.first_line_indent=Cm(0);p.paragraph_format.space_before=Cm(5)
    return doc

def table(doc,caption,headers,rows,widths):
    p=para(doc,caption);p.paragraph_format.first_line_indent=Cm(0);p.paragraph_format.keep_with_next=True
    t=shared_table(doc,headers,rows,widths)
    if doc.styles['Normal'].font.name=='Times New Roman':
        for row in t.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    for r in p.runs:r.font.size=Pt(12)

def figure(doc,name,number,caption):
    p=doc.add_paragraph();p.paragraph_format.first_line_indent=Cm(0);p.paragraph_format.keep_with_next=True;p.alignment=1
    picture=p.add_run().add_picture(str(ROOT/'java-course/illustrations'/f'{name}.png'),width=Cm(16));picture._inline.docPr.set('descr',caption)
    p=para(doc,f'Рисунок {number} — {caption}');p.alignment=1;p.paragraph_format.first_line_indent=Cm(0)

def script_body(doc,lesson,scientific=False):
    elapsed=0
    for i,s in enumerate(lesson['slides'],1):
        doc.add_heading(f'{i} {s["title"]}',3 if scientific else 2)
        para(doc,f'Время {elapsed}–{elapsed+s["minutes"]} мин. Продолжительность {s["minutes"]} мин.').paragraph_format.keep_with_next=True
        para(doc,'Речь преподавателя. '+s['teacher'])
        para(doc,'Вопрос классу. '+s['question'])
        para(doc,'Ожидаемый ответ. '+s['answer'])
        if s.get('code'):code(doc,s['code'])
        if s.get('diagram'):para(doc,'Покажите схему '+s['diagram']+'. Попросите связать каждый переход со строкой трассировки.')
        para(doc,'Действие. '+('Выполнить эксперимент в парах и сопоставить прогноз с результатом.' if i==9 else 'Выслушать объяснение, попросить проверить его на одном изменённом входе.'))
        elapsed+=s['minutes']

for number,lesson in enumerate([] if '--scientific-only' in sys.argv else C['lessons'],1):
    doc=newdoc(f'Java {number} {lesson["title"]}','Сценарий преподавателя к презентации из 15 слайдов')
    para(doc,'90 минут. Можно разделить на два школьных урока: после этапа 7 сохранить прогноз и код, на следующем уроке продолжить с границ алгоритма.')
    para(doc,'Цель. '+lesson['goal']);para(doc,'Предварительные знания. '+('Работа с папкой и текстовым редактором; программирование не требуется.' if number==1 else 'Материал предыдущих занятий курса; готовность читать короткий Java код.'))
    para(doc,'Материалы. JDK 21, редактор, сайт курса, Main.java текущего занятия. Для занятия 10 дополнительно папка project. Ответы на слайдах доступны преподавателю; перед раскрытием предложите собственный прогноз.')
    table(doc,'План занятия',['Этап','Минуты'],[[str(i+1)+' '+s['title'],s['minutes']] for i,s in enumerate(lesson['slides'])],[13,3])
    script_body(doc,lesson)
    doc.add_heading('Полный эталонный пример',1);code(doc,lesson['code']);para(doc,'Ожидаемый stdout');code(doc,lesson['stdout'])
    for extra in lesson.get('extraExamples',[]):
        doc.add_heading('Дополнительный пример '+extra['file'],2);code(doc,extra['code']);para(doc,'Вход: '+(extra['stdin'] or 'weights.txt содержит 12'));para(doc,'Ожидаемый stdout');code(doc,extra['stdout'])
    doc.add_heading('Самостоятельная работа и оценивание',1);para(doc,lesson['homework']);para(doc,'Защита. '+lesson['defense'])
    para(doc,'Рубрика 0–8 баллов: модель 0–2, алгоритм и код 0–2, тесты 0–2, объяснение 0–2. Баллы являются предложенной методикой, а не шкалой ЕГЭ. Числовой ответ без объяснения не подтверждает самостоятельность.')
    doc.save(OUT/f'lesson-{number:02d}-teacher-script.docx')

doc=newdoc('Обучение программированию на Java с применением алгоритмов на графах','Согласованный учебный комплекс для 10–11 классов',True)
doc.add_heading('Реферат',1)
para(doc,'Представлен учебный комплекс из десяти занятий по 90 минут, интерактивного сайта, десяти презентаций и десяти сценариев преподавателя. Изучаются типы данных Java, логические выражения, циклы, массивы, строки, динамическое программирование, поиск в ширину и оптимизация пути в ориентированном ациклическом графе. Итоговым результатом является локальное Java приложение с веб-интерфейсом для расчёта маршрута.')
para(doc,'Цель разработки состоит в обеспечении согласованного перехода от чтения короткой программы к обоснованию алгоритма и реализации прикладного проекта. Материалы связываются через единый машиночитаемый источник. Числовые результаты примеров проверяются исполнением, а формат входных данных и ошибки HTTP проверяются отдельными тестами. Эффективность обучения экспериментально не измерялась; приведённая рубрика является предложением для педагогической апробации.')
para(doc,'Ключевые слова: Java, школьная информатика, граф, алгоритм, инвариант, динамическое программирование, тестирование, проектное обучение.')
para(doc,'Оформление основного текста: A4, поля 30 мм слева, 15 мм справа, 20 мм сверху и снизу, Times New Roman 14 пт, межстрочный интервал 1,5, абзац 1,25 см. Использованы требования ГОСТ 7.32–2017 к структуре и оформлению и ГОСТ Р 7.0.100–2018 к библиографическому описанию [6, 7]. Код выделен моноширинным шрифтом для сохранения читаемости. Реквизиты организации и автора не выдумываются; локальные требования учебного заведения проверяются отдельно.')
entries=[('Введение','Введение'),('1 Методические основания','1 Методические основания'),('2 Среда разработки','2 Среда разработки'),('3 Содержание занятий','3 Содержание занятий')]
for i,l in enumerate(C['lessons'],1):entries.append((f'3.{i} {l["title"]}',f'3.{i} {l["title"]}'))
entries += [('4 Итоговый проект','4 Итоговый проект'),('5 Проверка и оценивание','5 Проверка и оценивание'),('Заключение','Заключение'),('Список использованных источников','Список использованных источников'),('Приложение А Сценарии преподавателя','Приложение А Сценарии преподавателя'),('Приложение Б Исходники итогового проекта','Приложение Б Исходники итогового проекта')]
doc.add_heading('Содержание',1)
for i,(title,target) in enumerate(entries):
    p=doc.add_paragraph();p.paragraph_format.first_line_indent=Cm(0);p.paragraph_format.line_spacing=1.1;p.paragraph_format.space_after=Pt(4)
    p.paragraph_format.tab_stops.add_tab_stop(Cm(16.4),WD_TAB_ALIGNMENT.RIGHT,WD_TAB_LEADER.DOTS)
    start=OxmlElement('w:bookmarkStart');start.set(qn('w:id'),str(1000+i));start.set(qn('w:name'),f'_course_toc_{i}');p._p.append(start)
    p.add_run(title);p.add_run('	');p.add_run('0');end=OxmlElement('w:bookmarkEnd');end.set(qn('w:id'),str(1000+i));p._p.append(end)
(REVIEW/'toc-entries.json').write_text(json.dumps(entries,ensure_ascii=False),encoding='utf-8')
doc.add_heading('Введение',1)
for t in [
'Курс предназначен для учащихся 10–11 классов, начинающих систематическое изучение Java или переходящих с другого языка. Базовые навыки работы с файлами предполагаются, предыдущий опыт объектно-ориентированного программирования не требуется. Продолжительность комплекса составляет 900 минут аудиторной работы; самостоятельные задания выполняются дополнительно. При расписании по 45 минут каждое занятие делится на две встречи.',
'Проблема проектирования состоит в согласовании трёх представлений учебного материала: самостоятельной работы на сайте, объяснения преподавателя на слайдах и развёрнутого печатного изложения. Раздельное редактирование этих представлений создаёт риск расхождения программ и результатов. В предложенной архитектуре содержательные данные задаются единожды и используются генераторами разных форматов.',
'В качестве сквозной предметной модели принят маршрутный центр орбитальной станции. Вершины соответствуют отсекам, направленные рёбра — разрешённым переходам, а веса — времени движения. Эта модель позволяет последовательно различать достижимость, число переходов, количество путей и суммарную стоимость. Каждая из этих величин имеет собственный алгоритм и область применимости.',
'Связь с ЕГЭ устанавливается по спецификации ФИПИ 2027, проверенной 12 ноября 2026 года [1]. В разделе 9 среди сред программирования указан Java. В разделе 11 и обобщённом плане тематика задания 23 связана с оптимальными путями и количеством путей в простом ориентированном ациклическом графе. Поэтому графовые темы рассматриваются содержательно, без переноса устаревшего описания задания 23. Точный набор программ в пункте проведения экзамена уточняется отдельно.',
'Комплекс охватывает выбранные темы логики, обработки последовательностей и графов. Он не является полной программой подготовки к ЕГЭ: электронные таблицы, сети, кодирование информации, игровые стратегии и другие разделы требуют дополнительных занятий. Веб проект служит переносом алгоритмических умений в программную разработку и не заявляется обязательным содержанием экзамена.'
]:para(doc,t)
doc.add_heading('1 Методические основания',1)
for title,text in [
('1.1 Прогноз и наблюдение','Каждая практическая работа начинается с письменного прогноза результата на определённом входе. Затем учащийся запускает программу и фиксирует первое расхождение. Такой порядок делает наблюдаемой собственную модель выполнения программы и позволяет обсуждать причину ошибки. Прогноз не оценивается как экзаменационный ответ: его назначение состоит в выявлении понимания до получения машинного результата.'),
('1.2 Инвариант и контрпример','Объяснение корректности строится через состояние, которое сохраняет смысл после каждого шага. Для частотного подсчёта это сведения только о предыдущих элементах, для BFS — неубывание расстояний в очереди, для DAG — завершённость расчёта предшественников. Контрпример выбирается минимальным, чтобы локализовать нарушенное условие. Случайный набор тестов дополняет, но не заменяет такое рассуждение.'),
('1.3 Самостоятельность и использование инструментов','Нельзя гарантировать невозможность внешнего решения или использования нейросети. Поэтому задания предполагают изменяемые веса, собственные тесты и устную защиту нового условия. Учащийся может использовать справочник или генератор кода, но обязан указать вклад инструмента и проверить результат. Содержательным результатом считается способность предсказать поведение при изменении входа и обосновать ограничение алгоритма.'),
('1.4 Дифференциация','Базовый уровень предусматривает чтение готового каркаса и заполнение трассировки. Основной уровень включает самостоятельное изменение условия и тесты. Углублённый уровень требует сравнения двух алгоритмов и доказательства границ применимости. Объём программы увеличивают только после проверки базового случая; более длинный исходник сам по себе не является признаком более высокого результата.')]:doc.add_heading(title,2);para(doc,text)
table(doc,'Таблица 1 — Учебные результаты и свидетельства',['Результат','Наблюдаемое свидетельство'],[['Моделирование','Вход, результат, единицы и ограничения названы явно'],['Корректность','Трассировка и объяснение инварианта'],['Тестирование','Обычный случай, граница, ошибка ввода и контрпример'],['Перенос','Верный прогноз при изменении одного условия']],[5,11.5])
doc.add_heading('2 Среда разработки',1)
para(doc,'Базовая среда — JDK 21 без preview возможностей. Поддерживаемые стандартные средства включают javac, java, коллекции java.util, файловый API и модуль jdk.httpserver [2–4]. Редактор VS Code удобен для начинающих, но команды запуска остаются независимыми от редактора [5]. Установка дополнительных фреймворков не требуется.')
for i,item in enumerate(C['setup'],1):doc.add_heading(f'2.{i} {item["title"]}',2);para(doc,item['text'])
code(doc,'java -version\njavac -version\njavac -encoding UTF-8 Main.java\njava Main')
figure(doc,'pipeline',1,'Последовательность компиляции и выполнения Java программы')
para(doc,'Схема показывает действия, а не имитирует снимок установщика. Точные команды приведены в тексте. В разных версиях редактора расположение кнопок может отличаться; устойчивыми остаются имя файла Main.java и команды компилятора. Если системная команда не найдена, проверяют PATH и наличие JDK, затем открывают новый терминал.')
doc.add_heading('3 Содержание занятий',1)
table(doc,'Таблица 2 — Последовательность курса',['№','Тема','Результат'],[[i,l['subtitle'],l['goal']] for i,l in enumerate(C['lessons'],1)],[.8,5.7,10])
for i,l in enumerate(C['lessons'],1):
    h=doc.add_heading(f'3.{i} {l["title"]}',2)
    para(doc,'Цель занятия. '+l['goal']);para(doc,'Проблемная ситуация. '+l['hook']);para(doc,l['ege'])
    for j,t in enumerate(l['theory'],1):doc.add_heading(f'3.{i}.{j} {t["title"]}',3);para(doc,t['text'])
    if i>1:figure(doc,l['diagram'],i,l['subtitle'])
    para(doc,'Трассировка. '+l['trace'])
    doc.add_heading('Эталонный пример и результат',3);code(doc,l['code']);para(doc,'Ожидаемый stdout');code(doc,l['stdout'])
    for extra in l.get('extraExamples',[]):
        doc.add_heading('Дополнительный пример '+extra['file'],3);code(doc,extra['code']);para(doc,'Вход: '+(extra['stdin'] or 'weights.txt содержит 12'));para(doc,'Ожидаемый stdout');code(doc,extra['stdout'])
    doc.add_heading('Эксперимент и интерпретация',3);para(doc,l['lab']);para(doc,'Разбор. '+l['solution']);para(doc,'Типичная ошибка. '+l['trap'])
    table(doc,f'Таблица {i+2} — Проверочные вопросы занятия {i}',['Вопрос','Ответ и объяснение'],[[t['prompt'],t['answer']+'. '+t['explanation']] for t in l['tasks']],[8,8.5])
    para(doc,'Шаг проекта. '+l['project']);para(doc,'Защита. '+l['defense']);para(doc,'Самостоятельная работа. '+l['homework'])
doc.add_heading('4 Итоговый проект',1)
for text in [
'Итоговый проект представляет локальное приложение «Маршрутный центр». Пользователь меняет стоимость линии C→B и получает минимальную стоимость и один оптимальный путь A→D. Интерфейс показывает ограничения задачи; расчёт выполняется Java, а браузер отображает результат. Исходники полностью приведены в приложении Б и поставляются в папке java-course/project.',
'Граф содержит вершины в порядке A,C,B,D. Рёбра A→C, A→B, A→D, C→B, C→D и B→D направлены от меньшего индекса к большему. Веса равны 2,4,12,w,7,3 соответственно; w принимает значения 1–99. Топологический порядок задан самой моделью данных. Это позволяет использовать динамическое программирование, не реализуя отдельную сортировку.',
'Метод plan принимает квадратную матрицу, проверяет размер до 50 вершин, положительные веса до 99 и отсутствие обратных рёбер. Нуль обозначает отсутствие ребра. Максимальная конечная стоимость не превосходит 49 × 99 = 4851, поэтому INF = 1 000 000 безопасно отделяет недостижимость. Для недостижимой цели возвращаются стоимость −1 и пустой путь. Переданная матрица не изменяется.',
'HTTP сервер использует стандартный HttpServer и слушает только 127.0.0.1:8090 [3]. Обработчик разрешает GET для точного списка маршрутов. Параметр /route?w=1 проверяется до расчёта. Лишние, повторные и некорректные параметры отклоняются кодом 400; неизвестный путь получает 404, иной метод — 405. Ответ содержит только вычисленные числа и фиксированные названия станций. Произвольный код и пользовательские файловые пути не принимаются.',
'Архитектура имеет учебную границу: это локальная демонстрация одного пользователя. Публикация Java сервера в интернете не является частью данной версии. Для такого размещения необходимы отдельные решения о времени запросов, ограничении нагрузки, завершении процесса и TLS. Наличие веб-интерфейса само по себе не означает готовности к внешней эксплуатации.'
]:para(doc,text)
table(doc,'Таблица 13 — Модули итогового проекта',['Файл','Ответственность'],[['RoutePlanner.java','Чистый расчёт, проверка графа и парсер веса'],['RoutePlannerTest.java','Контракты, границы и сравнение со 100 эталонными DAG'],['Main.java','Loopback HTTP, статический интерфейс и JSON API']],[6,10.5])
code(doc,'javac -encoding UTF-8 RoutePlanner.java RoutePlannerTest.java Main.java\njava RoutePlannerTest\njava Main')
para(doc,'Ожидается строка OK от тестов. После запуска Main откройте http://127.0.0.1:8090. Для остановки нажмите Ctrl+C в терминале сервера. Если порт занят, определите собственный ранее запущенный процесс; не завершайте неизвестные программы.')
figure(doc,'project-screen',11,'Экран реально запущенного локального приложения при w равном 1')
para(doc,'Снимок получен при запуске поставляемого Main.java. Он фиксирует результат 6 минут и путь A-C-B-D; прочие состояния подтверждаются тестами, а не изображением.')
doc.add_heading('5 Проверка и оценивание',1)
para(doc,'Верификация материалов включает согласованность исходника Java с каноническим содержанием, компиляцию с --release 21 и проверку ожидаемого stdout. Для финального проекта используется полный перебор путей как независимый эталон на ста воспроизводимых DAG с генератором Random(42). Дополнительно проверяются недостижимость, совпадение старта и цели, нарушение структуры графа и ошибочные HTTP запросы. Автоматическая проверка не является измерением учебной эффективности.')
table(doc,'Таблица 14 — Контрольные случаи проекта',['Условие','Ожидаемый результат'],[['w=1','6, A-C-B-D'],['w=2','7, один из двух оптимальных путей'],['w=3 или w=99','7, A-B-D'],['Линия C→B закрыта в чистом расчёте','7, A-B-D'],['Недостижимая цель','−1, пустой путь'],['Старт совпадает с целью','0, путь из одной вершины'],['w=0, 100, 01, -1 или повтор параметра','HTTP 400'],['POST /route?w=1','HTTP 405'],['Неизвестный путь','HTTP 404']],[9,7.5])
para(doc,'Предлагаемая рубрика оценивает четыре стороны результата по 0–2 балла. Ноль означает отсутствие проверяемого свидетельства, один — частично верное решение или объяснение с помощью преподавателя, два — самостоятельное воспроизводимое решение. Итог 0–8 относится только к данному проекту и не переводится в баллы ЕГЭ.')
table(doc,'Таблица 15 — Рубрика защиты',['Критерий','Признак уровня 2'],[['Модель','Явно указаны DAG, направления, веса и границы'],['Алгоритм','Объяснены порядок и релаксация, верен новый прогноз'],['Проверки','Есть граница, ошибка ввода и независимый эталон'],['Объяснение','Автор находит контрпример и защищает изменение']],[5,11.5])
para(doc,'Педагогическая апробация может сравнивать входную и выходную задачи одинаковой сложности, не совпадающие дословно с материалами курса. Для анализа следует заранее определить критерии, объём выборки и правила обезличивания. В текущем комплексе такие наблюдения не проводились; график числа операций в занятии 4 построен по формулам n и n(n−1)/2 и не изображает экспериментальные данные.')
doc.add_heading('Заключение',1)
para(doc,'Разработанная последовательность связывает базовые средства Java с задачами логики, обработки последовательностей и анализа графов. Учащийся получает возможность пройти полный цикл: сформулировать модель, предсказать результат, выполнить программу, проверить границы и объяснить корректность. Сквозной проект показывает применение динамического программирования в локальном веб приложении.')
para(doc,'Единый источник снижает риск расхождения сайта, презентаций и сценариев. Технические проверки подтверждают воспроизводимость заданных примеров в проверенной среде; они не доказывают усвоение материала каждым учеником. Дальнейшее развитие предполагает педагогическую апробацию, задачи на другие типы графов и отдельную подготовку по остальным темам экзамена.')
doc.add_heading('Список использованных источников',1)
for i,s in enumerate(C['sources'],1):
    p=para(doc,f'{i}. {s["title"]}. URL: {s["url"]} (дата обращения: 12.11.2026). Текст: электронный.');p.paragraph_format.first_line_indent=Cm(0)
doc.add_heading('Приложение А Сценарии преподавателя',1)
para(doc,'Сценарии соответствуют презентациям из 15 слайдов. Номера этапов, время, вопросы и ответы сохранены из общего источника. Они предназначены для адаптации преподавателем к темпу группы. В каждой паре школьных уроков возможна остановка после слайда 7.')
for i,l in enumerate(C['lessons'],1):
    h=doc.add_heading(f'А.{i} {l["title"]}',2);h.paragraph_format.page_break_before=True
    script_body(doc,l,True)
doc.add_heading('Приложение Б Исходники итогового проекта',1)
para(doc,'Следующие листинги являются полными исходниками проверяемого проекта. Для воспроизведения сохраните каждый в файл с указанным именем в одной папке. Учебный сервер запускается локально; публичное размещение не подразумевается.')
for file in ['RoutePlanner.java','RoutePlannerTest.java','Main.java']:
    doc.add_heading(file.replace('.java',''),2);para(doc,'Файл '+file);code(doc,(ROOT/'java-course/project'/file).read_text(encoding='utf-8'))
doc.save(OUT/'scientific-methodical-guide.docx')
print('Built scientific guide; render and materialise contents before delivery.' if '--scientific-only' in sys.argv else 'Built 10 scripts and scientific guide; render and materialise contents before delivery.')
