/** Build visually structured lesson decks from the shared lesson JSON files. */
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {spawnSync} from 'node:child_process';
import {Presentation,PresentationFile} from '@oai/artifact-tool';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const skill=process.env.PRESENTATIONS_SKILL_DIR, python=process.env.RUNTIME_PYTHON;
if(!skill||!python) throw Error('Set PRESENTATIONS_SKILL_DIR and RUNTIME_PYTHON.');
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')));
const C={ink:'#18343A',accent:'#176B6A',paper:'#FAFAF4',muted:'#52686C',code:'#142C35'};
function text(s,v,x,y,w,h,size=27,color=C.ink,name='',font='Arial'){
 const sh=s.shapes.add({geometry:'textbox',name,position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 sh.text=v;sh.text.style={fontFamily:font,fontSize:size,color};return sh;
}
function rect(s,x,y,w,h,fill){s.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:h},fill,line:{fill:'none',width:0}});}
async function build(lesson){
 if(lesson.slides.length>30||lesson.slides.reduce((n,s)=>n+s.minutes,0)!==45)throw Error(`Invalid lesson ${lesson.id}`);
 const illustration=await fs.readFile(path.join(ROOT,'site/assets/pytik-mascot.png'));
 const screenshot=await fs.readFile(path.join(ROOT,'site/assets/screenshots/setup-07-open-folder.png'));
 const p=Presentation.create({slideSize:{width:1280,height:720}});let elapsed=0;
 lesson.slides.forEach((d,i)=>{
  const s=p.slides.add(), cover=i===0;s.background.fill=cover?'#173F49':C.paper;
  const ink=cover?'#FFFFFF':C.ink, muted=cover?'#C7E5DF':C.muted;
  text(s,`УРОК ${Number(lesson.id)}   ·   ${elapsed}–${elapsed+d.minutes} МИН`,60,28,850,25,16,muted);
  text(s,d.title,60,70,1120,76,d.title.length>42?36:44,ink);
  if(cover){
   text(s,lesson.concept.toUpperCase(),60,175,640,32,20,'#A6E6D4');
   d.body.forEach((line,j)=>{text(s,String(j+1).padStart(2,'0'),60,238+j*69,48,36,22,'#F9C865');text(s,line,116,235+j*69,600,56,26,'#FFFFFF');});
   s.images.add({blob:illustration,contentType:'image/png',alt:'Пытик, робот-помощник',fit:'contain',position:{left:800,top:175,width:370,height:330}});
  }else if(lesson.id==='01'&&i===2){
   s.images.add({blob:screenshot,contentType:'image/png',alt:'Окно выбора папки в macOS: кнопка «Открыть» справа внизу',fit:'contain',position:{left:60,top:170,width:700,height:310}});
   d.body.forEach((line,j)=>{text(s,String(j+1),792,175+j*91,45,32,20,C.accent);text(s,line,842,172+j*91,378,80,23,C.ink);});
   text(s,'Пример окна выбора папки в macOS',60,484,700,25,16,C.muted);
  }else if((lesson.id==='05'&&i===8)||(lesson.id==='06'&&[3,8].includes(i))||(lesson.id==='02'&&[2,8].includes(i))||(lesson.id==='01'&&i===4)||(lesson.id==='03'&&i===7)||(lesson.id==='04'&&i===4)||(lesson.id==='07'&&i===4)||(lesson.id==='08'&&i===5)){
   // These are editable teaching diagrams, not representations of an editor.
   rect(s,60,170,520,196,C.code);text(s,'КОД PYTHON',80,185,470,22,16,'#9FD9CB');
   const diagramLines=d.code.split('\n');
   const diagramCodeSize=Math.max(14,Math.min(24,Math.floor(480/(Math.max(...diagramLines.map(line=>line.length))*.62)),Math.floor(100/diagramLines.length)));
   text(s,d.code,80,225,480,135,diagramCodeSize,'#FFFFFF','Code','Consolas');
   if(lesson.id==='05'){
    text(s,'КАК ИДЁТ ЦИКЛ',635,175,540,28,19,C.accent);
    ['1-й шаг: number = 0  ·  вывод 0','2-й шаг: number = 1  ·  вывод 1','3-й шаг: number = 2  ·  вывод 2'].forEach((v,j)=>{rect(s,635,216+j*68,545,54,['#DDEDE5','#F9E6C4','#E0E9F3'][j]);text(s,v,655,227+j*68,510,38,21,C.ink);});
    text(s,'После третьего шага цикл заканчивается.',60,410,1100,48,23,C.ink);
   }else if(lesson.id==='06'&&i===3){
    text(s,'ИНДЕКСЫ НАЧИНАЮТСЯ С НУЛЯ',60,391,1100,28,19,C.accent);
    ['0   ключ','1   карта','2   фонарь'].forEach((v,j)=>{rect(s,60+j*365,435,335,58,['#DDEDE5','#F9E6C4','#E0E9F3'][j]);text(s,v,80+j*365,446,300,38,23,C.ink);});
   }else if(lesson.id==='02'&&i===2){
    text(s,'ИМЯ ПЕРЕМЕННОЙ',635,180,470,28,17,C.accent);text(s,'name',635,218,470,50,34,C.ink);
    text(s,'ЗНАЧЕНИЕ',635,290,470,28,17,C.accent);text(s,'"Маша"',635,328,470,50,34,C.ink);
    text(s,'Знак = связывает имя и значение.',60,420,1100,48,23,C.ink);
   }else if(lesson.id==='01'){
    text(s,'ИЗ ЧЕГО СОСТОИТ КОМАНДА',635,175,545,28,19,C.accent);
    ['print  ·  команда вывода','( )  ·  обрамляют сообщение','" "  ·  обозначают текст'].forEach((v,j)=>{rect(s,635,216+j*68,545,54,['#DDEDE5','#F9E6C4','#E0E9F3'][j]);text(s,v,655,227+j*68,510,38,21,C.ink);});
    text(s,'В терминале останется только сообщение.',60,410,1100,48,23,C.ink);
   }else if(lesson.id==='02'){
    text(s,'ИЗМЕНЕНИЕ ЗНАЧЕНИЯ',635,175,545,28,19,C.accent);
    ['1. name хранит «Маша»','2. print выводит Маша','3. name теперь хранит «Саша»','4. print выводит Саша'].forEach((v,j)=>{rect(s,635,210+j*61,545,49,['#DDEDE5','#E4EFE9','#F9E6C4','#E4EFE9'][j]);text(s,v,655,219+j*61,510,34,20,C.ink);});
   }else if(lesson.id==='06'){
    text(s,'ДО ДОБАВЛЕНИЯ',635,175,545,28,19,C.accent);
    text(s,'ключ  ·  карта  ·  фонарь',635,211,545,40,23,C.ink);
    text(s,'ПОСЛЕ append("компас")',635,275,545,28,19,C.accent);
    text(s,'ключ  ·  карта  ·  фонарь  ·  компас',635,311,545,64,21,C.ink);
    text(s,'У нового элемента индекс 3.',60,420,1100,48,23,C.ink);
   }else if(lesson.id==='03'){
    text(s,'ПУТЬ ОТВЕТА',635,175,545,28,19,C.accent);
    ['1. input: игрок вводит 3','2. int: текст превращается в число','3. print: число + 1 = ?'].forEach((v,j)=>{rect(s,635,216+j*68,545,54,['#DDEDE5','#F9E6C4','#E0E9F3'][j]);text(s,v,655,227+j*68,510,38,21,C.ink);});
    text(s,'Сначала предскажи вывод, затем проверь.',60,420,1100,48,23,C.ink);
   }else if(lesson.id==='04'){
    text(s,'ВЫБИРАЕМ ОДИН ПУТЬ',635,175,545,28,19,C.accent);
    ['Проверка: 9 >= 10 ?','Если верно: «Дверь открыта»','Иначе: «Нужна зарядка»'].forEach((v,j)=>{rect(s,635,216+j*68,545,54,['#DDEDE5','#F9E6C4','#E0E9F3'][j]);text(s,v,655,227+j*68,510,38,21,C.ink);});
    text(s,'Какой путь выберет Python?',60,420,1100,48,23,C.ink);
   }else if(lesson.id==='07'){
    text(s,'ОПРЕДЕЛЕНИЕ И ВЫЗОВ',635,175,545,28,19,C.accent);
    ['1. def: запомнить инструкцию','2. say_hello(): вызвать её','3. Выполнить print внутри'].forEach((v,j)=>{rect(s,635,216+j*68,545,54,['#DDEDE5','#F9E6C4','#E0E9F3'][j]);text(s,v,655,227+j*68,510,38,21,C.ink);});
    text(s,'Когда появится приветствие?',60,420,1100,48,23,C.ink);
   }else{
    text(s,'СРАВНИВАЕМ ДВА ЧИСЛА',635,175,545,28,19,C.accent);
    ['Секретное число: 7','Догадка: 3','Проверка: 3 == 7 ?'].forEach((v,j)=>{rect(s,635,216+j*68,545,54,['#DDEDE5','#F9E6C4','#E0E9F3'][j]);text(s,v,655,227+j*68,510,38,21,C.ink);});
    text(s,'Предскажи True или False.',60,420,1100,48,23,C.ink);
   }
  }else if(d.code){
   const lines=d.code.split('\n'), longest=Math.max(...lines.map(x=>x.length));
   const size=Math.max(14,Math.min(30,Math.floor(605/(Math.max(longest,1)*.62)),Math.floor((d.output?115:175)/Math.max(lines.length,1))));
   rect(s,60,170,690,d.output?210:300,C.code);
   text(s,'КОД PYTHON',80,184,600,24,16,'#9FD9CB');
   text(s,d.code,80,220,650,d.output?145:230,size,'#FFFFFF','Code','Consolas');
   if(d.output&&!d.animation){const out=d.output.trimEnd(), count=out.split('\n').length;rect(s,60,394,690,105,'#E4EFE9');text(s,'ВЫВОД ПРОГРАММЫ',80,403,640,22,15,C.accent);text(s,out,80,428,640,68,count>4?12:count>2?15:20,C.ink,'Output','Consolas');}
   text(s,'РАЗБИРАЕМ',790,174,420,25,16,C.accent);
   d.body.forEach((line,j)=>{text(s,String(j+1),790,222+j*79,43,32,18,C.accent);text(s,line,839,219+j*79,370,75,line.length>85?20:23,C.ink);});
  }else{
   const colors=['#DDEDE5','#F9E6C4','#E0E9F3'];
   d.body.forEach((line,j)=>{const y=174+j*100;rect(s,60,y,70,64,colors[j%colors.length]);text(s,String(j+1),76,y+14,44,36,23,C.accent);text(s,line,154,y+8,1020,82,line.length>95?24:29,C.ink);});
  }
  const prompt=d.question||'Что получилось?', bottomInk=cover?'#FFFFFF':C.ink;
  text(s,'ОБСУДИМ',60,531,140,25,15,cover?'#A6E6D4':C.accent);
  text(s,prompt,205,526,1010,52,prompt.length>100?20:23,bottomInk);
  const answer=`Ответ: ${d.answer}`+(d.animation&&d.output?`\nРезультат примера: ${d.output.trimEnd().split('\n').join(' / ')}`:'');
  text(s,answer,60,595,1140,82,answer.length>180?17:answer.length>110?19:22,bottomInk,d.animation?'reveal-answer':'answer');
  text(s,`${i+1} / ${lesson.slides.length}`,1140,690,85,20,13,muted);
  s.speakerNotes.text=[`Слайд ${i+1}. ${elapsed}–${elapsed+d.minutes} мин (${d.minutes} мин)`,d.teacher,`Действия: ${d.action}`,`Вопрос: ${d.question}`,`Ожидаемый ответ: ${d.answer}`,d.animation?'Анимация: один щелчок открывает ответ. До щелчка выслушайте предположения.':'Анимации нет.'].join('\n\n');
  elapsed+=d.minutes;
 });
 const stamp=Date.now().toString(), staging=path.join(ROOT,'.build/artifacts',`lesson-${lesson.id}`);await fs.mkdir(staging,{recursive:true});
 const candidate=path.join(staging,`visual-${stamp}.pptx`);await(await PresentationFile.exportPptx(p)).save(candidate);
 const patch=spawnSync(python,[path.join(ROOT,'lessons/scripts/animate_pptx.py'),candidate],{encoding:'utf8'});if(patch.status!==0)throw Error(patch.stderr||patch.stdout);
 const review=path.join(ROOT,'.build/review');await fs.mkdir(review,{recursive:true});const checked=path.join(review,`visual-lesson-${lesson.id}-${stamp}.pptx`);
 await finalizePresentation({workspaceDir:ROOT,candidatePath:candidate,finalPath:checked,pythonExecutable:python,integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000'],explicitTotalSlideCount:lesson.slides.length,requiredNativeTableOwnerSlides:[],fontPolicy:{basis:'design',families:['Arial','Consolas']},verifyArtifactToolImport:true,receiptPath:path.join(staging,`visual-validation-${stamp}.json`)});
 if(process.env.RENDER_SLIDES!=='0')for(const [i,s] of p.slides.items.entries()){const png=await p.export({slide:s,format:'png',scale:1});await fs.writeFile(path.join(staging,`visual-slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await png.arrayBuffer()));}
 console.log(`Validated: ${checked}; ${lesson.slides.length} slides; 45 minutes.`);
}
const files=(await fs.readdir(path.join(ROOT,'lessons/content'))).filter(x=>/^lesson-\d\d\.json$/.test(x)).sort();
for(const file of files){const lesson=JSON.parse(await fs.readFile(path.join(ROOT,'lessons/content',file),'utf8'));if(!process.env.LESSON_ID||process.env.LESSON_ID===lesson.id)await build(lesson);}
