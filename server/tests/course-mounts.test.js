import test from 'node:test';
import assert from 'node:assert/strict';
import {createApp} from '../app.js';

test('Python and Java have independent same-origin entry points and working assets', async t => {
  const server=createApp({codes:['lesson']});
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  t.after(()=>new Promise(resolve=>server.close(resolve)));
  const base='http://127.0.0.1:'+server.address().port;
  for (const course of ['python','java']) {
    for (const suffix of ['', '/teacher']) {
      const response=await fetch(base+'/'+course+suffix+'?from=main',{redirect:'manual'});
      assert.equal(response.status,308);
      assert.equal(response.headers.get('location'),'/'+course+suffix+'/?from=main');
    }
    assert.equal((await fetch(base+'/'+course+'/')).status,200);
    for (const page of ['/teacher/','/teacher/index.html']) {
      const response=await fetch(base+'/'+course+page);
      assert.equal(response.status,200);
      assert.match(response.headers.get('content-security-policy'),/script-src 'self'/);
    }
  }
  for (const asset of ['/python/styles.css','/python/src/ui/app.js','/python/assets/iskra.webp','/java/style.css','/java/app.js','/java/course.js','/java/figures/bfs.png']) {
    assert.equal((await fetch(base+asset,{method:'HEAD'})).status,200,asset);
  }
  assert.equal((await fetch(base+'/python/java/')).status,404);
  assert.equal((await fetch(base+'/java/project/Main.java')).status,404);
  for (const old of ['/site/','/site/java/','/teacher/']) assert.equal((await fetch(base+old)).status,200);
  const python=await (await fetch(base+'/python/src/ui/app.js')).text();
  const java=await (await fetch(base+'/java/')).text();
  assert.match(python,/href="\/python\/teacher\/"/);
  assert.doesNotMatch(python,/href="(?:\/site\/java\/|\/java\/)"/);
  assert.match(java,/href="\/java\/teacher\/"/);
  assert.doesNotMatch(java,/href="(?:\/site\/|\/python\/)"/);
  assert.match(await (await fetch(base+'/java/app.js')).text(),/from '\/site\/src\/storage\/ProgressStore.js'/);
});

test('Course-specific teacher catalogues contain only the selected course', async t => {
  const server=createApp({codes:['lesson']});
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  t.after(()=>new Promise(resolve=>server.close(resolve)));
  const base='http://127.0.0.1:'+server.address().port;
  assert.equal((await fetch(base+'/api/teacher/materials?course=java')).status,401);
  const login=await fetch(base+'/api/teacher/login',{method:'POST',headers:{Origin:base,'Content-Type':'application/json'},body:'{"code":"lesson"}'});
  const cookie=login.headers.get('set-cookie').split(';')[0];
  for (const [course,total,prefix] of [['python',8,'/lessons/output/'],['java',10,'/java-course/output/']]) {
    const response=await fetch(base+'/api/teacher/materials?course='+course,{headers:{Cookie:cookie}});
    assert.equal(response.status,200);
    const catalog=await response.json();
    assert.equal(catalog.course,course);
    assert.equal(catalog.lessons.length,total);
    assert.equal(catalog.javaCourse,undefined);
    const urls=[...catalog.lessons.flatMap(x=>[x.presentation,x.script]),...catalog.guides.map(x=>x.url)];
    for (const url of urls) {
      assert.ok(url.startsWith(prefix),url);
      const file=await fetch(base+url,{method:'HEAD',headers:{Cookie:cookie}});
      assert.equal(file.status,200,url);
      assert.match(file.headers.get('cache-control'),/private, no-store/);
    }
  }
  for (const query of ['course=','course=ruby','course=java&course=python']) {
    assert.equal((await fetch(base+'/api/teacher/materials?'+query,{headers:{Cookie:cookie}})).status,400,query);
  }
  const legacy=await (await fetch(base+'/api/teacher/materials',{headers:{Cookie:cookie}})).json();
  assert.equal(legacy.lessons.length,8);assert.equal(legacy.javaCourse.lessons.length,10);
});