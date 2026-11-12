import http from 'node:http';
import { setTimeout } from 'node:timers/promises';
import test from 'node:test';
import assert from 'node:assert/strict';
import { createApp } from '../app.js';

test('teacher access protects files, expires and revokes sessions, rejects cross-origin writes', async t => {
  let now = 1000;
  const server = createApp({codes:['lesson','teacher-42'], now:() => now, sessionMs:10000});
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  t.after(() => new Promise(resolve => server.close(resolve)));
  const base = `http://127.0.0.1:${server.address().port}`;
  const request = (path, options = {}) => fetch(base + path, options);
  const post = (path, code, cookie, origin = base) => request(path, {method:'POST', headers:{'Content-Type':'application/json', Origin:origin, ...(cookie ? {Cookie:cookie} : {})}, body:JSON.stringify({code})});
  assert.equal((await request('/site/')).status, 200);
  assert.equal((await request('/teacher/')).status, 200);
  assert.equal((await request('/lessons/output/new-learning-guide.docx')).status, 401);
  assert.equal((await request('/api/teacher/materials')).status, 401);
  assert.equal((await post('/api/teacher/login','lesson',null,'https://evil.example')).status, 403);
  assert.equal((await post('/api/teacher/login','wrong')).status, 401);
  const login = await post('/api/teacher/login','teacher-42');
  assert.equal(login.status, 200);
  const cookie = login.headers.get('set-cookie').split(';')[0];
  assert.match(login.headers.get('set-cookie'), /HttpOnly/);
  assert.match(login.headers.get('set-cookie'), /SameSite=Strict/);
  assert.equal((await request('/api/teacher/session',{headers:{Cookie:cookie}})).status, 200);
  const files = await request('/api/teacher/materials',{headers:{Cookie:cookie}});
  assert.equal(files.status, 200);
  const catalogue = await files.json();
  assert.equal(catalogue.lessons.length, 8);
  for (const url of [...catalogue.guides.map(guide => guide.url),...catalogue.lessons.flatMap(lesson => [lesson.presentation,lesson.script])]) {
    const file = await request(url,{method:'HEAD',headers:{Cookie:cookie}});
    assert.equal(file.status,200,url);
    assert.match(file.headers.get('content-disposition'),/attachment/);
    assert.match(file.headers.get('cache-control'),/no-store/);
    assert.equal(await file.text(),'');
  }
  assert.equal((await request('/lessons/output/new-learning-guide.docx',{headers:{Cookie:cookie}})).status, 200);
  assert.equal((await request('/lessons/output/lesson-01-visual-candidate.pptx',{headers:{Cookie:cookie}})).status, 404);
  for (const path of ['/.git/config','/lessons/content/lesson-01.json','/server/app.js','/site/%2e%2e%5cserver/app.js']) assert.notEqual((await request(path)).status, 200, path);
  assert.equal((await post('/api/teacher/logout',null,cookie)).status, 200);
  assert.equal((await request('/api/teacher/materials',{headers:{Cookie:cookie}})).status, 401);
  const again = await post('/api/teacher/login','lesson');
  const expired = again.headers.get('set-cookie').split(';')[0];
  now += 11000;
  assert.equal((await request('/api/teacher/materials',{headers:{Cookie:expired}})).status, 401);
});

test('login limits repeated attempts and recovers after the window', async t => {
  let now = 0;
  const server = createApp({codes:['lesson'], now:() => now, maxAttempts:2, attemptWindowMs:100});
  await new Promise(resolve => server.listen(0,'127.0.0.1',resolve));
  t.after(() => new Promise(resolve => server.close(resolve)));
  const base = `http://127.0.0.1:${server.address().port}`;
  const login = code => fetch(base+'/api/teacher/login',{method:'POST',headers:{Origin:base,'Content-Type':'application/json'},body:JSON.stringify({code})});
  await login('bad'); await login('bad');
  assert.equal((await login('lesson')).status,429);
  now = 101;
  assert.equal((await login('lesson')).status,200);
});

// Exercise the actual HTTP parser, including JSON type and UTF-8 boundaries.
test('login rejects invalid JSON shapes and oversized request bodies', async t => {
  const server = createApp({codes:['lesson'], maxAttempts:30});
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  t.after(() => new Promise(resolve => server.close(resolve)));
  const base = `http://127.0.0.1:${server.address().port}`;
  const headers = {'Content-Type':'application/json', Origin:base};
  for (const body of ['null','[]','true','42','"lesson"','{}','{"code":42}','{']) {
    const response = await fetch(base+'/api/teacher/login', {method:'POST',headers,body});
    assert.equal(response.status,400,body);
    assert.equal(response.headers.get('set-cookie'),null);
  }
  const large = await fetch(base+'/api/teacher/login',{method:'POST',headers,body:JSON.stringify({code:'a'.repeat(2048)})});
  assert.equal(large.status,413);
  assert.equal((await fetch(base+'/health')).status,200);
});

test('login decodes a Cyrillic code after all UTF-8 chunks arrive', async t => {
  const code = 'учитель-42';
  const server = createApp({codes:[code]});
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  t.after(() => new Promise(resolve => server.close(resolve)));
  const base = `http://127.0.0.1:${server.address().port}`;
  const body = Buffer.from(JSON.stringify({code}));
  const split = body.indexOf(Buffer.from('у')) + 1;
  const response = await new Promise((resolve,reject) => {
    const request = http.request(base+'/api/teacher/login',{method:'POST',headers:{'Content-Type':'application/json',Origin:base}},resolve);
    request.on('error',reject);
    request.write(body.subarray(0,split));
    setTimeout(25).then(() => request.end(body.subarray(split))).catch(reject);
  });
  response.resume();
  assert.equal(response.statusCode,200);
  assert.match(response.headers['set-cookie'][0],/HttpOnly/);
});
test('HTTPS proxy configuration protects writes and serves local brand assets with strict headers', async t => {
  const origin = 'https://school.example';
  const server = createApp({codes:['lesson'],secureCookies:true,publicOrigin:origin});
  await new Promise(resolve => server.listen(0,'127.0.0.1',resolve));
  t.after(() => new Promise(resolve => server.close(resolve)));
  const base = `http://127.0.0.1:${server.address().port}`;
  const login = headers => fetch(base+'/api/teacher/login',{method:'POST',headers,body:'{"code":"lesson"}'});
  assert.equal((await login({'Content-Type':'application/json',Origin:base})).status,403);
  assert.equal((await login({'Content-Type':'text/plain',Origin:origin})).status,403);
  const response = await login({'Content-Type':'application/json',Origin:origin});
  assert.equal(response.status,200);
  assert.match(response.headers.get('set-cookie'),/; Secure/);
  for (const [asset,type] of [['iskra.webp','image/webp'],['genesis-mark.svg','image/svg+xml'],['fonts/onest-cyrillic.woff2','font/woff2']]) {
    const assetResponse = await fetch(base+'/site/assets/'+asset,{method:'HEAD'});
    assert.equal(assetResponse.status,200);
    assert.equal(assetResponse.headers.get('content-type'),type);
    assert.equal(assetResponse.headers.get('x-content-type-options'),'nosniff');
    assert.match(assetResponse.headers.get('content-security-policy'),/script-src 'self'/);
    assert.doesNotMatch(assetResponse.headers.get('content-security-policy'),/unsafe-inline|unsafe-eval/);
  }
});

test('Java materials share teacher protection while retaining Python catalogue', async t=>{
 const server=createApp({codes:['lesson']});await new Promise(r=>server.listen(0,'127.0.0.1',r));t.after(()=>new Promise(r=>server.close(r)));
 const base='http://127.0.0.1:'+server.address().port;
 const file='/java-course/output/lesson-01-presentation.pptx';
 assert.equal((await fetch(base+file)).status,401);
 const login=await fetch(base+'/api/teacher/login',{method:'POST',headers:{Origin:base,'Content-Type':'application/json'},body:JSON.stringify({code:'lesson'})});
 const cookie=login.headers.get('set-cookie').split(';')[0];
 const catalog=await (await fetch(base+'/api/teacher/materials',{headers:{Cookie:cookie}})).json();
 assert.equal(catalog.lessons.length,8);assert.equal(catalog.javaCourse.lessons.length,10);assert.equal(catalog.javaCourse.guides.length,2);
 for(const url of [...catalog.javaCourse.lessons.flatMap(x=>[x.presentation,x.script]),...catalog.javaCourse.guides.map(x=>x.url)])assert.equal((await fetch(base+url,{method:'HEAD',headers:{Cookie:cookie}})).status,200,url);
 assert.equal((await fetch(base+'/java-course/content/course.json',{headers:{Cookie:cookie}})).status,404);
 assert.equal((await fetch(base+'/java-course/project/Main.java',{headers:{Cookie:cookie}})).status,404);
 const head=await fetch(base+file,{method:'HEAD',headers:{Cookie:cookie}});assert.equal(head.headers.get('cache-control'),'private, no-store');assert.match(head.headers.get('content-disposition'),/^attachment/);
 assert.equal((await fetch(base+'/site/java/')).status,200);
 await fetch(base+'/api/teacher/logout',{method:'POST',headers:{Origin:base,'Content-Type':'application/json',Cookie:cookie},body:'{}'});
 for(const url of [...catalog.javaCourse.lessons.flatMap(x=>[x.presentation,x.script]),...catalog.javaCourse.guides.map(x=>x.url)])assert.equal((await fetch(base+url,{method:'HEAD',headers:{Cookie:cookie}})).status,401,url);
});
