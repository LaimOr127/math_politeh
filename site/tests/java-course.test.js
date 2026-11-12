import test from 'node:test';
import assert from 'node:assert/strict';
import {javaCourse} from '../java/course.js';
import {readFileSync} from 'node:fs';
const canonical=JSON.parse(readFileSync(new URL('../../java-course/content/course.json',import.meta.url),'utf8'));
import {shortestPath,checkAnswer} from '../java/domain.js';
import {ProgressStore} from '../src/storage/ProgressStore.js';
test('Java canonical course has ten complete independent lessons',()=>{
 assert.equal(javaCourse.lessons.length,10);
 assert.deepEqual(javaCourse.lessons.map(l=>l.tasks),canonical.lessons.map(l=>l.tasks));assert.ok(javaCourse.lessons.every(l=>!('slides' in l)&&!('defenseAnswer' in l)));
 for(const l of canonical.lessons){assert.equal(l.tasks.length,3);assert.equal(l.slides.length,15);assert.equal(l.slides.reduce((n,s)=>n+s.minutes,0),90);assert.ok(l.theory.length>=3);for(const q of l.tasks){assert.ok(checkAnswer(q,q.answer));assert.ok(!checkAnswer(q,'unrelated'));}}
});
test('graph lab computes weighted routes, closed edges and unreachable targets',()=>{
 const edges=[['A','B',4],['A','C',2],['C','B',1],['B','D',3],['C','D',7]];
 assert.deepEqual(shortestPath(edges,'A','D'),{distance:6,path:['A','C','B','D']});
 assert.equal(shortestPath(edges.filter(e=>e[0]!=='C'),'A','D').distance,7);
 assert.equal(shortestPath([],'A','D').distance,Infinity);
 assert.deepEqual(shortestPath(edges,'A','A'),{distance:0,path:['A']});
 assert.throws(()=>shortestPath([['A','B',-1]],'A','B'));
 assert.throws(()=>shortestPath([['A','B',NaN]],'A','B'));
});
test('Java progress cannot overwrite Python progress and repeat awards are idempotent',()=>{
 const values=new Map([['python-lab-progress','keep']]);const storage={getItem:k=>values.get(k),setItem:(k,v)=>values.set(k,v),removeItem:k=>values.delete(k)};
 const course=javaCourse.lessons.map(l=>({id:l.id,exercises:l.tasks}));const p=new ProgressStore(storage,course,'java-orbit-progress');
 for(const q of course[0].exercises){p.completeExercise(course[0].id,q.id);p.completeExercise(course[0].id,q.id);}
 assert.equal(p.load().stars,1);assert.equal(values.get('python-lab-progress'),'keep');assert.equal(new ProgressStore(storage,course,'java-orbit-progress').load().stars,1);p.reset();assert.equal(values.get('python-lab-progress'),'keep');
});

import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
test('Java Office artifacts retain all canonical examples, teacher notes and linked contents',()=>{
 const run=spawnSync(process.env.PYTHON||(process.platform==='win32'?'python':'python3'),['-I','-X','utf8',fileURLToPath(new URL('../../java-course/scripts/verify_materials.py',import.meta.url))],{encoding:'utf8',timeout:20000});
 assert.equal(run.status,0,run.stderr||String(run.error));
});
