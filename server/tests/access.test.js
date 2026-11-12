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
