/** Build editable lesson decks. Runtime dependencies are supplied by the caller. */
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {spawnSync} from 'node:child_process';
import {Presentation, PresentationFile} from '@oai/artifact-tool';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const skill=process.env.PRESENTATIONS_SKILL_DIR;
const python=process.env.RUNTIME_PYTHON;
if(!skill||!python) throw Error('Set PRESENTATIONS_SKILL_DIR and RUNTIME_PYTHON; see lessons/scripts/README.md.');
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')));
const stamp=Date.now().toString();
const COLOR={ink:'#18343A',accent:'#176B6A',paper:'#FAFAF4',muted:'#52686C',code:'#142C35'};
function text(slide,value,x,y,w,h,size=27,color=COLOR.ink,name='',font='Arial'){
 const shape=slide.shapes.add({geometry:'textbox',name,position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 shape.text=value; shape.text.style={fontFamily:font,fontSize:size,color}; return shape;
}
function rect(slide,x,y,w,h,fill){slide.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:h},fill,line:{fill:'none',width:0}});}
async function build(lesson){
 if(lesson.slides.length>30||lesson.slides.reduce((s,x)=>s+x.minutes,0)!==45) throw Error(`Invalid lesson ${lesson.id} duration/size`);
 const illustration=await fs.readFile(path.join(ROOT,'site/assets/pytik-mascot.png'));
 const p=Presentation.create({slideSize:{width:1280,height:720}});
 let elapsed=0;
 lesson.slides.forEach((data,index)=>{
  const slide=p.slides.add();slide.background.fill=COLOR.paper;
  text(slide,`Урок ${Number(lesson.id)}   ${elapsed}–${elapsed+data.minutes} мин`,56,24,1130,26,16,COLOR.muted);
  text(slide,data.title,56,70,1168,96,data.title.length>60?34:40);
  const code=data.code;
  const visual=index===0;
  if(code){
   const count=code.split('\n').length;
   const longest=Math.max(...code.split('\n').map(x=>x.length));
   const size=Math.min(31,Math.floor(290/Math.max(count,1)),Math.floor(660/(Math.max(longest,1)*.61)));
   rect(slide,56,174,700,340,COLOR.code);
   text(slide,code,76,194,660,300,Math.max(17,size),'#F7FAEF','Code','Consolas');
   text(slide,data.body.join('\n\n'),790,174,432,340,24);
  }else if(visual){
   text(slide,data.body.join('\n\n'),56,174,600,340,27);
   slide.images.add({blob:illustration,contentType:'image/png',alt:'Пытик, робот-помощник',fit:'contain',position:{left:690,top:174,width:534,height:340}});
  }else{
   data.body.forEach((line,i)=>{
    text(slide,String(i+1).padStart(2,'0'),56,177+i*85,60,45,24,COLOR.accent);
    text(slide,line,135,174+i*85,1060,80,28);
   });
  }
  const prompt=data.question||'Что получилось?';
  text(slide,prompt,56,535,1168,54,prompt.length>110?22:26,COLOR.accent);
  const reveal=data.output?`Результат: ${data.output.trimEnd()}`:`Ответ: ${data.answer}`;
  const revealLines=reveal.split('\n').length;
  text(slide,reveal,56,590,1168,100,revealLines>4?16:revealLines>2||reveal.length>210?18:22,COLOR.ink,data.animation?'reveal-answer':'answer');
  text(slide,`${index+1} / ${lesson.slides.length}`,1140,688,85,20,13,COLOR.muted);
  slide.speakerNotes.text=[`Слайд ${index+1}. ${elapsed}–${elapsed+data.minutes} мин (${data.minutes} мин)`,data.teacher,`Действия: ${data.action}`,`Вопрос: ${data.question}`,`Ожидаемый ответ: ${data.answer}`,data.animation?'Анимация: один щелчок открывает нижний блок ответа или результата. До щелчка выслушайте предположения.':'Анимации нет.'].join('\n\n');
  elapsed+=data.minutes;
 });
 const staging=path.join(ROOT,'.build/artifacts',`lesson-${lesson.id}`);await fs.mkdir(staging,{recursive:true});
 const candidate=path.join(staging,`candidate-${stamp}.pptx`);
 await (await PresentationFile.exportPptx(p)).save(candidate);
 const patch=spawnSync(python,[path.join(ROOT,'lessons/scripts/animate_pptx.py'),candidate],{encoding:'utf8'});
 if(patch.status!==0)throw Error(patch.stderr||patch.stdout);
 const review=path.join(ROOT,'.build/review'); await fs.mkdir(review,{recursive:true});
 const checked=path.join(review,`lesson-${lesson.id}-${stamp}.pptx`);
 await finalizePresentation({workspaceDir:ROOT,candidatePath:candidate,finalPath:checked,pythonExecutable:python,integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000'],explicitTotalSlideCount:lesson.slides.length,requiredNativeTableOwnerSlides:[],fontPolicy:{basis:'design',families:['Arial','Consolas']},verifyArtifactToolImport:true,receiptPath:path.join(staging,`validation-${stamp}.json`)});
 if(process.env.RENDER_SLIDES!=='0'){
  for(const [i,slide] of p.slides.items.entries()){
   const png=await p.export({slide,format:'png',scale:1});
   await fs.writeFile(path.join(staging,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await png.arrayBuffer()));
  }
 }
 console.log(`Validated candidate for review: ${checked}`);
 console.log(`Lesson ${lesson.id}: ${lesson.slides.length} slides, 45 minutes.`);
}
const files=(await fs.readdir(path.join(ROOT,'lessons/content'))).filter(x=>/^lesson-\d\d\.json$/.test(x)).sort();
if(!files.length)throw Error('No lesson JSON files found.');
for(const file of files){const lesson=JSON.parse(await fs.readFile(path.join(ROOT,'lessons/content',file),'utf8'));if(!process.env.LESSON_ID||process.env.LESSON_ID===lesson.id)await build(lesson);}
