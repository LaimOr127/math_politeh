"""Original explanatory diagrams and theoretical operation-count plot, not screenshots."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math
ROOT=Path(__file__).resolve().parents[2]
DARK=ROOT/'site/java/figures'; PRINT=ROOT/'java-course/illustrations'
DARK.mkdir(parents=True,exist_ok=True);PRINT.mkdir(parents=True,exist_ok=True)
FONT='C:/Windows/Fonts/arial.ttf'
def build(name,dark):
    bg,ink,muted,accent,line=('#101c2b','#eaf1f5','#c7d6e4','#ffc58b','#71889b') if dark else ('white','#162638','#344c62','#81410c','#61758a')
    im=Image.new('RGB',(1600,900),bg);d=ImageDraw.Draw(im)
    def text(x,y,value,size=33,color=None):d.text((x,y),value,font=ImageFont.truetype(FONT,size),fill=color or ink)
    def arrow(a,b,label=''):
        x,y=a;xx,yy=b;d.line((x,y,xx,yy),fill=line,width=5);angle=math.atan2(yy-y,xx-x)
        d.polygon([(xx,yy),(xx-21*math.cos(angle-.45),yy-21*math.sin(angle-.45)),(xx-21*math.cos(angle+.45),yy-21*math.sin(angle+.45))],fill=line)
        if label:text((x+xx)/2+12,(y+yy)/2-38,label,32,accent)
    def node(x,y,label):
        d.ellipse((x-52,y-52,x+52,y+52),fill=bg,outline=accent,width=4);box=d.textbbox((0,0),label,font=ImageFont.truetype(FONT,38));text(x-(box[2]-box[0])/2,y-23,label,38)
    def box(x,y,w,h,label):
        d.rounded_rectangle((x,y,x+w,y+h),radius=14,outline=line,width=3);text(x+22,y+24,label,32)
    titles={'pipeline':'От исходного файла к выполнению','truth':'Открытие шлюза и таблица состояний','binary':'Разряды числа 173','complexity':'Цена перебора и подсчёта частот','automaton':'Состояние допустимого суффикса','dag':'Подсчёт путей шагами +1 и +2','bfs':'Слои поиска в ширину','weighted':'Оптимальный путь на ориентированном графе','contract':'Проверка данных перед расчётом','http':'Поток запроса в Java приложении'}
    text(65,45,titles[name],45)
    if name=='pipeline':
        for x,label in [(75,'Main.java'),(620,'Main.class'),(1160,'stdout')]:box(x,290,330,140,label)
        arrow((410,360),(610,360),'javac');arrow((955,360),(1150,360),'java')
        text(90,545,'Компилятор проверяет типы и структуру программы.',36)
        text(90,610,'JVM выполняет main. Результат сверяем с прогнозом.',36)
        text(90,735,'javac -encoding UTF-8 Main.java     →     java Main',32,accent)
    elif name=='truth':
        headers=['p','s','e','(p && s) || e'];xs=[110,340,570,900]
        for x,h in zip(xs,headers):text(x,150,h,36,accent)
        for row in range(8):
            p,s,e=bool(row&4),bool(row&2),bool(row&1)
            for x,value in zip(xs,[int(p),int(s),int(e),int((p and s)or e)]):text(x,225+row*65,str(value),34)
        text(1130,310,'5 открытых',34);text(1130,365,'состояний',34);text(1130,485,'из 8',42,accent)
    elif name=='binary':
        text(80,155,'Частное',34,accent);text(590,155,'Остаток',34,accent);text(1030,155,'Прочитать снизу',34,accent)
        ns=[173,86,43,21,10,5,2,1]
        for i,n in enumerate(ns):text(100,220+i*65,str(n)+' / 2 = '+str(n//2),34);text(670,220+i*65,str(n%2),34)
        text(1000,365,'10101101',57);text(1010,465,'Основание 2',34);text(1010,550,'5 единиц',42)
    elif name=='complexity':
        x0,y0=160,735;w,h=1250,500
        for power in range(0,9,2):
            y=y0-power/8*h;d.line((x0,y,x0+w,y),fill=line,width=1);text(52,y-20,'10^'+str(power),25)
        arrow((x0,y0),(x0,y0-h-50));arrow((x0,y0),(x0+w+45,y0))
        ns=[10,100,1000,10000];colors=[accent,'#5eb5c3' if dark else '#126778']
        for series,color in [('pairs',colors[0]),('linear',colors[1])]:
            points=[]
            for i,n in enumerate(ns):
                value=n*(n-1)//2 if series=='pairs' else n;x=x0+130+i*330;y=y0-math.log10(value)/8*h;points.append((x,y));d.ellipse((x-9,y-9,x+9,y+9),fill=color)
            d.line(points,fill=color,width=6)
        for i,n in enumerate(ns):text(x0+95+i*330,760,str(n),28)
        text(180,135,'n(n−1)/2 сравнений',32,colors[0]);text(850,135,'n обработок',32,colors[1])
        text(160,825,'Теоретическое число операций. Обе оси логарифмические. Это не замер времени.',27)
    elif name=='automaton':
        text(90,180,'Строка',32,accent);text(90,320,'cur',32,accent);text(90,460,'best',32,accent)
        for i,(c,cur,best) in enumerate(zip('BAAACABAA',[1,2,1,1,2,3,4,5,1],[1,2,2,2,2,3,4,5,5])):
            x=310+i*130;text(x,180,c,44);text(x,320,str(cur),44);text(x,460,str(best),44)
        text(90,660,'AA → cur = 1, поскольку текущее A остаётся допустимым.',36)
        text(90,735,'Самый длинный участок ACABA: 5 символов.',36,accent)
    elif name=='dag':
        for i in range(6):arrow((140+i*215,430),(250+i*215,430),'+1')
        for i in range(5):
            x=90+i*215;points=[(x+15+400*t/30,375-135*math.sin(math.pi*t/30)) for t in range(31)];d.line(points,fill=line,width=4);arrow(points[-2],points[-1]);text(x+170,202,'+2',30,accent)
        for i,value in enumerate([1,1,2,3,5,8,13]):node(90+i*215,430,str(i));text(70+i*215,540,str(value),39,accent)
        text(85,650,'dp[0] = 1;  dp[i] = dp[i−1] + dp[i−2]',40)
        text(85,745,'Нижняя строка — число путей в каждую вершину.',34)
    elif name in ('weighted','bfs'):
        pts={'A':(170,440),'C':(700,250),'B':(700,670),'D':(1400,440)}
        edges=[('A','C','2'),('A','B','4'),('A','D','12'),('C','B','1'),('C','D','7'),('B','D','3')]
        if name=='bfs':edges=[('A','C',''),('A','B',''),('C','B',''),('C','D',''),('B','D','')]
        for a,b,value in edges:
            x,y=pts[a];xx,yy=pts[b]
            if a=='A' and b=='D':
                d.line([(x,y-57),(x,155),(xx,155),(xx,yy-90)],fill=line,width=5);arrow((xx,yy-90),(xx,yy-61));text(800,112,value,32,accent);continue
            length=math.hypot(xx-x,yy-y);ux,uy=(xx-x)/length,(yy-y)/length
            arrow((x+57*ux,y+57*uy),(xx-61*ux,yy-61*uy),value)
        for label,(x,y) in pts.items():node(x,y,label)
        text(85,805,'A → C → B → D: 2 + 1 + 3 = 6' if name=='weighted' else 'Слои BFS:  {A} → {B, C} → {D}. Все рёбра стоят один переход.',34,accent)
    elif name=='contract':
        box(70,220,380,125,'Строка "12"');arrow((450,280),(630,280));box(650,220,385,125,'Формат 1–99');arrow((1035,280),(1190,280));box(1210,220,300,125,'Расчёт')
        arrow((840,350),(840,560));box(610,580,570,125,'Ошибка → ответ 400')
        text(70,755,'"0", "−5", "100", "01" отклоняются до вычисления маршрута.',34)
    elif name=='http':
        for x,label in [(65,'Браузер'),(620,'Java HTTP'),(1170,'Алгоритм')]:box(x,260,320,140,label)
        arrow((390,300),(610,300),'GET');arrow((945,300),(1160,300),'w');arrow((1160,425),(945,425),'Route');arrow((610,485),(390,485),'JSON')
        text(85,630,'/route?w=1 → проверка → cost: 6, path: A-C-B-D',36)
        text(85,725,'Сервер слушает только 127.0.0.1:8090.',36,accent)
    target=(DARK if dark else PRINT)/(name+'.png');im.save(target)
for name in ['pipeline','truth','binary','complexity','automaton','dag','bfs','weighted','contract','http']:
    for dark in (False,True):build(name,dark)
print('20 diagrams generated')
