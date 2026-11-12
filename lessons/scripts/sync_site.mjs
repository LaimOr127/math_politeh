import fs from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = fileURLToPath(new URL('../../',import.meta.url));
const lessons = [];
for (let number=1;number<=8;number++) {
  const lesson=JSON.parse(await fs.readFile(path.join(root,`lessons/content/lesson-${String(number).padStart(2,'0')}.json`),'utf8'));
  const sections=structuredClone(lesson.web.sections);
  sections.push({title:'Практика занятия',paragraphs:[lesson.practice,...(lesson.stdin ? [`Для проверки введи: ${lesson.stdin.trim()}. В блоке результата показан вывод программы без эха клавиатуры.`] : [])],code:lesson.code,output:lesson.output.trimEnd()});
  lessons.push({id:lesson.missionId,title:lesson.web.title,concept:lesson.concept,goal:lesson.goal,sections,exercises:lesson.exercises});
}
const content='/** Generated from lessons/content by npm run sync:site. Edit the JSON sources. */\nexport const courseLessons = '+JSON.stringify(lessons,null,2)+';\n';
const target=path.join(root,'site/src/data/course.js');
if(process.argv.includes('--check')) {
  if(await fs.readFile(target,'utf8')!==content) throw Error('Course data is stale. Run npm run sync:site.');
} else {await fs.writeFile(target,content);console.log('Synchronized 8 lessons.');}
