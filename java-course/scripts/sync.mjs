import fs from 'node:fs/promises';
const course=JSON.parse(await fs.readFile(new URL('../content/course.json',import.meta.url),'utf8'));
const publicCourse={...course,lessons:course.lessons.map(({slides,openingAnswer,defenseAnswer,...lesson})=>lesson)};
const outputs=[[new URL('../../site/java/course.js',import.meta.url),'// Generated from java-course/content/course.json; do not edit.\nexport const javaCourse = '+JSON.stringify(publicCourse,null,2)+';\n']];
for(const [i,lesson] of course.lessons.entries()){
 const base=new URL('../examples/lesson-'+String(i+1).padStart(2,'0')+'/',import.meta.url);
 outputs.push([new URL('Main.java',base),lesson.code+'\n']);
 for(const extra of lesson.extraExamples||[]){outputs.push([new URL(extra.file,base),extra.code+'\n']);for(const [name,value] of Object.entries(extra.files||{}))outputs.push([new URL(name,base),value]);}
}
for(const [file,content] of outputs){
 if(process.argv.includes('--check')){if(await fs.readFile(file,'utf8').catch(()=>null)!==content)throw Error('Stale generated file '+file+'; run npm run sync:java');}
 else{await fs.mkdir(new URL('.',file),{recursive:true});await fs.writeFile(file,content);}
}
