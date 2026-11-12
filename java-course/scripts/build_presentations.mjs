/** Build editable Java decks using the existing artifact runtime and finalizer. */
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {spawnSync} from 'node:child_process';
import {Presentation,PresentationFile} from '@oai/artifact-tool';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const SKILL=process.env.PRESENTATIONS_SKILL_DIR,python=process.env.RUNTIME_PYTHON;
if(!SKILL||!python)throw Error('Set PRESENTATIONS_SKILL_DIR and RUNTIME_PYTHON');
const {finalizePresentation}=await import(pathToFileURL(path.join(SKILL,'container_tools/artifact_tool_utils.mjs')));
const course=JSON.parse(await fs.readFile(path.join(ROOT,'java-course/content/course.json'),'utf8'));
function text(slide,value,x,y,w,h,size=30,color='#EAF1F5',name='',font='Arial'){
 const box=slide.shapes.add({geometry:'textbox',name,position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 box.text=value;box.text.style={fontFamily:font,fontSize:size,color};return box;
}
for(const [li,lesson] of course.lessons.entries()){
 if(process.env.LESSON_ID&&Number(process.env.LESSON_ID)!==li+1)continue;
 const id=String(li+1).padStart(2,'0'),stamp=Date.now();
 const staging=path.join(ROOT,'.build/java-slides',id);await fs.mkdir(staging,{recursive:true});
 const p=Presentation.create({slideSize:{width:1280,height:720}});let elapsed=0;
 for(const [i,data] of lesson.slides.entries()){
  const s=p.slides.add();s.background.fill='#101C2B';
  if(data.diagram){
   s.images.add({blob:await fs.readFile(path.join(ROOT,'site/java/figures',data.diagram+'.png')),contentType:'image/png',alt:lesson.trace,fit:'contain',position:{left:0,top:0,width:1280,height:720}});
  }else{
   text(s,'Орбита Java / занятие '+(li+1)+' / '+elapsed+'–'+(elapsed+data.minutes)+' мин',52,24,1150,28,17,'#B5C8D9');
   text(s,data.title,52,78,1176,95,42);
   if(data.code){
    const code=data.code.split('\n'),max=Math.max(...code.map(x=>x.length)),size=Math.min(29,Math.floor(1120/(max*.61)),Math.floor(320/code.length));
    text(s,data.code,64,183,1150,335,size,'#EAF1F5','Code','Consolas');
   }else{
    const value=data.screen.join('\n\n');text(s,value,52,193,1176,315,value.length>430?28:32);
   }
   const prompt=data.question; text(s,prompt,52,524,1176,71,prompt.length>115?23:26,'#FFC58B');
   const parts=data.answer.split(/(?<=[.!?])\s+(?=[А-ЯЁA-Z])/u);const answer=parts.slice(0,2).join(' ').length<260?parts.slice(0,2).join(' '):parts[0];
   text(s,answer,52,604,1176,76,answer.length>190||answer.split('\n').length>2?21:24,'#9EEAF0','reveal-answer');
  }
  text(s,(i+1)+' / 15',1175,691,85,20,13,'#B5C8D9');
  s.speakerNotes.text=['Слайд '+(i+1)+'. '+data.title,elapsed+'–'+(elapsed+data.minutes)+' мин',data.teacher,'Вопрос: '+data.question,'Ответ: '+data.answer,'Полный материал: '+data.body.join('\n'),i===14?'Источники: '+course.sources.slice(0,5).map(s=>s.url).join('; '):'',data.diagram?'Схема является авторской иллюстрацией модели, не снимком экрана.':'Один щелчок раскрывает ответ внизу. Сначала выслушайте прогноз.'].join('\n\n');
  elapsed+=data.minutes;
 }
 if(elapsed!==90)throw Error('Invalid duration');
 const candidate=path.join(staging,'candidate-'+stamp+'.pptx');await(await PresentationFile.exportPptx(p)).save(candidate);
 const patch=spawnSync(python,[path.join(ROOT,'lessons/scripts/animate_pptx.py'),candidate],{encoding:'utf8'});if(patch.status!==0)throw Error(patch.stderr||patch.stdout);
 const checkedDir=path.join(ROOT,'.build/java-checked');await fs.mkdir(checkedDir,{recursive:true});
 const checked=path.join(checkedDir,id+'-'+stamp+'.pptx');
 await finalizePresentation({workspaceDir:ROOT,candidatePath:candidate,finalPath:checked,pythonExecutable:python,integrityValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000'],explicitTotalSlideCount:15,requiredNativeTableOwnerSlides:[],fontPolicy:{basis:'design',families:['Arial','Consolas']},verifyArtifactToolImport:true,receiptPath:path.join(staging,'validation-'+stamp+'.json')});
 for(const [i,s] of p.slides.items.entries()){
  const png=await p.export({slide:s,format:'png',scale:1});await fs.writeFile(path.join(staging,'slide-'+String(i+1).padStart(2,'0')+'.png'),new Uint8Array(await png.arrayBuffer()));
 }
 await fs.copyFile(checked,path.join(ROOT,'java-course/output/lesson-'+id+'-presentation.pptx'));
 console.log('Java '+id+': 15 slides, 90 minutes, validated and rendered');
}
