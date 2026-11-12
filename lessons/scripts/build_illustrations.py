"""Draw original explanatory figures for the scientific Word guide, not UI mockups."""
import ast
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'lessons/illustrations'
FONT = next((p for p in [Path('C:/Windows/Fonts/times.ttf'),
             Path('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf')] if p.exists()), None)


class Drawing:
    """A small print-oriented canvas with coordinates expressed as percentages."""

    def __init__(self, height):
        self.image = Image.new('RGB', (1950, round(height*300)), 'white')
        self.draw = ImageDraw.Draw(self.image)

    def point(self, x, y):
        return (25+x*(self.image.width-50)/100, 20+(100-y)*(self.image.height-40)/100)

    def text(self, x, y, label, ha='left', va='center', fontsize=11, **kwargs):
        font = ImageFont.truetype(str(FONT), round(fontsize*300/72)) if FONT else ImageFont.load_default()
        bounds = self.draw.multiline_textbbox((0, 0), label, font=font, spacing=10, align='center')
        px, py = self.point(x, y)
        width, height = bounds[2]-bounds[0], bounds[3]-bounds[1]
        px -= width/2 if ha == 'center' else 0
        py -= height/2 + bounds[1]
        self.draw.multiline_text((px, py), label, fill='#111111', font=font,
                                 spacing=10, align='center' if ha == 'center' else 'left')


def canvas(height=3.2):
    """Return a monochrome 165 mm wide drawing canvas for print."""
    drawing = Drawing(height)
    return drawing, drawing


def box(ax, x, y, width, height, label, size=11):
    """Draw one labelled process or value; coordinates are figure-relative."""
    top_left = ax.point(x-width/2, y+height/2)
    bottom_right = ax.point(x+width/2, y-height/2)
    ax.draw.rectangle((top_left, bottom_right), fill='#f4f4f4', outline='#222222', width=3)
    ax.text(x, y, label, ha='center', va='center', fontsize=size, linespacing=1.3)


def arrow(ax, start, end, label=None, offset=(0, 0)):
    """Draw a directed relationship and optional label."""
    a, b = ax.point(*start), ax.point(*end)
    ax.draw.line((a, b), fill='#222222', width=3)
    angle = math.atan2(b[1]-a[1], b[0]-a[0])
    head = [b, (b[0]-18*math.cos(angle-.45), b[1]-18*math.sin(angle-.45)),
            (b[0]-18*math.cos(angle+.45), b[1]-18*math.sin(angle+.45))]
    ax.draw.polygon(head, fill='#222222')
    if label:
        ax.text((start[0]+end[0])/2+offset[0], (start[1]+end[1])/2+offset[1], label,
                ha='center', va='center', fontsize=10, backgroundcolor='white')


def save(fig, name):
    """Save a deterministic, high-resolution PNG and release the canvas."""
    OUT.mkdir(parents=True, exist_ok=True)
    fig.image.save(OUT/name, dpi=(300, 300))


def build_course_figures(lessons):
    """Build eleven source-aligned figures without fetching images or calling APIs."""
    fig, ax = canvas(2.0)
    stages = ['Вывод текста', 'Переменные', 'Ввод и числа', 'Условия',
              'Циклы', 'Списки', 'Функции', 'Мини-проект']
    for i, label in enumerate(stages):
        col, row = i % 4, i // 4
        x, y = 12.5 + col*25, 76-row*52
        box(ax, x, y, 22, 25, f'{i+1}\n{label}', 10.5)
        if col:
            arrow(ax, (x-14, y), (x-11.5, y))
    arrow(ax, (87.5, 62), (87.5, 51))
    arrow(ax, (87.5, 51), (12.5, 51))
    arrow(ax, (12.5, 51), (12.5, 38))
    save(fig, 'course-sequence.png')

    fig, ax = canvas(3.4)
    box(ax, 50, 83, 54, 21, 'Единый источник\nlessons/content/lesson-XX.json')
    for x, label in [(17, 'Сайт\ncourse.js'), (50, 'Презентации\nPPTX'), (83, 'Пособия\nDOCX')]:
        box(ax, x, 39, 29, 24, label)
        arrow(ax, (50, 71), (x, 52))
    ax.text(50, 8, 'Проверяются одни и те же программы, вопросы и ожидаемые результаты',
            ha='center', va='center', fontsize=10)
    save(fig, 'shared-content.png')

    fig, ax = canvas(2.6)
    box(ax, 24, 82, 43, 23, 'Браузер учащегося\nИнтерфейс и Mission')
    box(ax, 24, 40, 43, 23, 'ProgressStore\nПрогресс и настройки')
    arrow(ax, (24, 69), (24, 53))
    ax.text(24, 12, 'Сохранение в браузере\nбез передачи ответов серверу', ha='center', fontsize=10)
    box(ax, 77, 82, 42, 23, 'Браузер преподавателя\nВвод кода доступа')
    box(ax, 77, 42, 42, 23, 'Сервер Node.js\nПроверка сессии')
    box(ax, 77, 8, 42, 13, 'Разрешённые DOCX и PPTX')
    arrow(ax, (77, 69), (77, 55), 'HTTP', (10, 0))
    arrow(ax, (77, 29), (77, 16))
    save(fig, 'application-architecture.png')

    fig, ax = canvas(3.6)
    lines = lessons[0]['code'].splitlines()
    for y, command, result in zip((76, 31), lines, lessons[0]['output'].splitlines()):
        box(ax, 34, y, 63, 24, command, 11)
        box(ax, 86, y, 22, 24, result.replace('Пытик на связи', 'Пытик\nна связи'), 10.5)
        arrow(ax, (66, y), (74, y))
    arrow(ax, (34, 63), (34, 44), 'следующая команда', (20, 0))
    save(fig, 'lesson-01-sequence.png')

    fig, ax = canvas(2.7)
    tree = ast.parse(lessons[1]['code'])
    assignments = [n for n in tree.body if isinstance(n, ast.Assign)]
    for y, statement in zip((75, 25), assignments):
        name = statement.targets[0].id
        value = ast.literal_eval(statement.value)
        box(ax, 26, y, 32, 31, name)
        box(ax, 76, y, 36, 31, repr(value))
        arrow(ax, (43, y), (57, y), 'связано с', (0, 14))
    ax.text(3, 75, '1', va='center'); ax.text(3, 25, '2', va='center')
    save(fig, 'lesson-02-binding.png')

    fig, ax = canvas(2.4)
    for x, label in [(15, 'input\nстрока "3"'), (50, 'int\nцелое число 3'), (85, 'stars + 1\nцелое число 4')]:
        box(ax, x, 55, 28, 46, label)
    arrow(ax, (30, 55), (35, 55)); arrow(ax, (65, 55), (70, 55))
    ax.text(50, 12, 'Показано преобразование значений, а не полный поток вывода', ha='center', fontsize=10)
    save(fig, 'lesson-03-conversion.png')

    def branching(name, condition, left, right, initial=None):
        fig, ax = canvas(4.3 if initial else 3.5)
        if initial:
            box(ax, 50, 91, 75, 15, initial, 10.5)
            arrow(ax, (50, 83), (50, 73))
        points = [ax.point(*point) for point in [(50, 73), (75, 53), (50, 33), (25, 53)]]
        ax.draw.polygon(points, fill='#f4f4f4', outline='#222222', width=3)
        ax.text(50, 53, condition, ha='center', va='center', fontsize=11)
        box(ax, 22, 12, 40, 20, left, 10.5)
        box(ax, 78, 12, 40, 20, right, 10.5)
        arrow(ax, (30, 48), (22, 23), 'да', (-5, 0))
        arrow(ax, (70, 48), (78, 23), 'нет', (6, 0))
        save(fig, name)

    branching('lesson-04-branch.png', 'Условие if\nистинно?', 'Выполнить блок if', 'Выполнить блок else')

    fig, ax = canvas(2.5)
    loop = next(n for n in ast.parse(lessons[4]['code']).body if isinstance(n, ast.For))
    values = list(range(*[ast.literal_eval(n) for n in loop.iter.args]))
    ax.text(50, 91, ast.unparse(loop.iter), ha='center', fontsize=12)
    gap = 88 / max(len(values), 1)
    for i, value in enumerate(values):
        x = 6+gap*(i+.5)
        box(ax, x, 52, min(gap-4, 21), 30, str(value), 12)
        if i:
            arrow(ax, (x-gap/2+1, 52), (x-min(gap-4,21)/2-1, 52))
    ax.text(50, 12, 'На каждой итерации тело цикла выполняется с очередным значением', ha='center', fontsize=10)
    save(fig, 'lesson-05-range.png')

    fig, ax = canvas(2.6)
    assignment = next(n for n in ast.parse(lessons[5]['code']).body
                      if isinstance(n, ast.Assign) and isinstance(n.value, ast.List))
    items = ast.literal_eval(assignment.value)
    gap = 88/len(items)
    for i, value in enumerate(items):
        x = 6+gap*(i+.5)
        box(ax, x, 51, gap-3, 30, str(value), 10.5)
        ax.text(x, 81, f'Индекс {i}', ha='center', fontsize=11)
    ax.text(50, 10, 'Порядок элементов сохраняется; первый допустимый индекс равен нулю', ha='center', fontsize=10)
    save(fig, 'lesson-06-index.png')

    fig, ax = canvas(3.3)
    box(ax, 25, 79, 45, 25, 'Определение\ndef say_hello():', 11)
    box(ax, 77, 79, 41, 25, 'Тело функции\nprint("Привет!")', 11)
    arrow(ax, (48, 79), (55, 79))
    box(ax, 25, 27, 45, 25, 'Вызов\nsay_hello()', 11)
    box(ax, 77, 27, 41, 25, 'Выполнение тела\nВывод «Привет!»', 11)
    arrow(ax, (48, 27), (55, 27))
    ax.text(50, 52, 'Определение само по себе не выполняет тело', ha='center', fontsize=10.5)
    save(fig, 'lesson-07-call.png')

    branching('lesson-08-project.png', 'guess == secret', 'Вывод «Угадал!»',
              'Сообщение о неудаче', 'secret = 7; guess = int(input(...))')
    return OUT
