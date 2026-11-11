"""Create the short, printable companion for the introductory web lessons."""
from pathlib import Path
from docx import Document
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'lessons/output/new-learning-guide.docx'
LESSONS = [
 ('Первая программа', 'print показывает текст на экране. Текст помещают в одинаковые кавычки; скобки показывают, что мы вызываем команду.', 'print("Привет, мир!")', 'Привет, мир!', 'Поприветствуй себя по имени.', 'print("Привет, Маша!")', 'Если пропустить закрывающую кавычку или скобку, Python сообщит о синтаксической ошибке.'),
 ('Переменные и строки', 'Переменная хранит значение под именем. Знак = записывает значение в переменную. Имена чувствительны к регистру: name и Name различаются.', 'name = "Маша"\nprint(name)', 'Маша', 'Создай переменную color и выведи любимый цвет.', 'color = "синий"\nprint(color)', 'В print(name) кавычки вокруг имени не нужны: с кавычками напечатается слово name.'),
 ('Ввод и числа', 'input задаёт вопрос и возвращает строку. Чтобы прибавить число, преобразуем введённую строку функцией int. Человек вводит ответ в терминале и нажимает Enter.', 'age = int(input("Сколько тебе лет? "))\nprint(age + 1)', 'Сколько тебе лет? 11\n12', 'Попроси количество звёзд и выведи на одну больше.', 'stars = int(input("Сколько звёзд? "))\nprint(stars + 1)', 'int не преобразует слово «три»: для этого примера введи цифры, например 3.'),
 ('Условия', 'Условие помогает выбрать действие. Сравнение >= означает «больше или равно». После if и else ставят двоеточие, а команды внутри записывают с отступом в четыре пробела.', 'coins = 5\nif coins >= 5:\n    print("Дверь открыта")\nelse:\n    print("Нужно ещё монет")', 'Дверь открыта', 'Измени coins на 3 и предскажи результат.', 'coins = 3\nif coins >= 5:\n    print("Дверь открыта")\nelse:\n    print("Нужно ещё монет")', 'Один знак = присваивает значение, а == сравнивает значения.'),
 ('Цикл for', 'Цикл повторяет действия. range(3) последовательно даёт числа 0, 1 и 2: всего три значения. Команды с отступом принадлежат циклу.', 'for number in range(3):\n    print("Флажок")', 'Флажок\nФлажок\nФлажок', 'Выведи своё имя пять раз.', 'for number in range(5):\n    print("Маша")', 'Двоеточие и одинаковые отступы внутри цикла обязательны.'),
 ('Списки', 'Список хранит несколько значений в квадратных скобках. Нумерация начинается с нуля: items[1] — второй элемент. append добавляет значение в конец.', 'items = ["ключ", "карта", "фонарь"]\nprint(items[1])\nitems.append("компас")', 'карта', 'Создай список из трёх игр и выведи вторую.', 'games = ["шахматы", "лото", "домино"]\nprint(games[1])', 'Если обратиться к номеру, которого нет, возникнет IndexError.'),
 ('Функции', 'Функция объединяет действие под именем. Сначала опиши её с помощью def, затем вызови по имени со скобками. Команды функции записывают с отступом.', 'def say_hello():\n    print("Привет!")\n\nsay_hello()', 'Привет!', 'Создай функцию, которая выводит любимое приветствие.', 'def greet():\n    print("Здравствуйте!")\n\ngreet()', 'Одно определение функции ещё не выполняет её тело: нужен вызов.'),
 ('Проект Угадай число', 'Объедини переменную, ввод и условие. Эта версия игры даёт одну попытку. Если хочешь попробовать ещё раз, запусти программу заново.', 'secret = 7\nguess = int(input("Назови число: "))\nif guess == secret:\n    print("Угадал!")\nelse:\n    print("Попробуй ещё")', 'Назови число: 7\nУгадал!', 'Измени секретное число, запусти программу и проверь оба ответа.', 'secret = 4\nguess = int(input("Назови число: "))\nif guess == secret:\n    print("Угадал!")\nelse:\n    print("Попробуй ещё")', 'Сравни ввод с секретом через ==. При вводе слова int сообщит об ошибке.')]

def code(doc, value):
    p = doc.add_paragraph(style='No Spacing')
    p.paragraph_format.left_indent = Cm(.4)
    run = p.add_run(value)
    run.font.name = 'Courier New'
    run.font.size = Pt(10)
    p.paragraph_format.space_after = Pt(7)


def build():
    doc = Document()
    sec = doc.sections[0]
    sec.top_margin = sec.bottom_margin = Cm(1.8)
    sec.left_margin = sec.right_margin = Cm(2)
    normal = doc.styles['Normal']
    normal.font.name = 'Arial'
    normal.font.size = Pt(11)
    normal.paragraph_format.space_after = Pt(6)
    for style in ('Title', 'Heading 1', 'Heading 2'):
        doc.styles[style].font.name = 'Arial'
        doc.styles[style].font.color.rgb = RGBColor(0,0,0)
    title_style = doc.styles['Title']
    borders = title_style.element.pPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pBdr')
    if borders is not None:
        title_style.element.pPr.remove(borders)
    doc.add_heading('Python и VS Code', 0)
    doc.add_paragraph('Краткое пособие для учеников 5–6 классов: настройка рабочего места, восемь тем, примеры и задания с решениями.')
    doc.add_heading('Подготовка рабочего места', level=1)
    for s in [
      '1. Открой python.org/downloads и скачай установщик Python для своей операционной системы. На Windows в установщике отметь Add Python to PATH, если этот пункт показан. Установку выполняй со взрослым.',
      '2. Открой code.visualstudio.com/download и скачай VS Code для своей системы. Установи программу, следуя указаниям установщика.',
      '3. Запусти VS Code. Нажми значок Extensions слева или Ctrl+Shift+X (на Mac Cmd+Shift+X). Найди Python от Microsoft и нажми Install.',
      '4. Выбери File → Open Folder и открой подготовленную папку для занятий. При запросе доверия убедись, что это твоя папка, и подтверди доверие.',
      '5. В Explorer нажми New File и назови файл hello.py. Впиши print("Привет, мир!") и сохрани файл: Ctrl+S или Cmd+S.',
      '6. Нажми Ctrl+Shift+P или Cmd+Shift+P, найди Python: Select Interpreter и выбери установленный Python 3. Нажми кнопку ▶ Run Python File справа вверху. Внизу в Terminal появится результат.'
    ]: doc.add_paragraph(s)
    doc.add_paragraph('Если интерпретатор не найден, проверь установку Python, перезапусти VS Code и повтори выбор. Если кнопки запуска нет, проверь расширение Python и то, что файл сохранён с расширением .py.')
    for index,(title,explain,example,output,practice,solution,tip) in enumerate(LESSONS,1):
      doc.add_page_break()
      doc.add_heading(f'Урок {index}. {title}', level=1)
      doc.add_paragraph(explain)
      doc.add_heading('Пример',level=2)
      code(doc,example)
      doc.add_paragraph('Ожидаемый результат:')
      code(doc,output)
      doc.add_heading('Попробуй самостоятельно',level=2)
      doc.add_paragraph(practice)
      doc.add_heading('Возможное решение',level=2)
      code(doc,solution)
      doc.add_heading('На что обратить внимание',level=2)
      doc.add_paragraph(tip)
      doc.add_paragraph('После выполнения задания открой соответствующий урок на сайте и проверь себя.')
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)

if __name__ == '__main__':
    build()
