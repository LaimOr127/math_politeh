/** Optional browser QA. Uses the external tooling runtime, not site dependencies. */
const {createRequire}=require('node:module');const fs=require('node:fs/promises');const path=require('node:path');const assert=require('node:assert/strict');
if(!process.env.RUNTIME_NODE_MODULES)throw Error('Set RUNTIME_NODE_MODULES');
const {chromium}=createRequire(path.join(process.env.RUNTIME_NODE_MODULES,'playwright/package.json'))('playwright');
const root=path.resolve(__dirname,'../..'),base=process.env.BASE_URL||'http://localhost:8091';
(async()=>{const browser=await chromium.launch({headless:true});const context=await browser.newContext({viewport:{width:360,height:800},reducedMotion:'reduce'});const page=await context.newPage(),errors=[];let assertions=0;
 page.on('pageerror',e=>errors.push(e.message));page.on('dialog',d=>d.accept());
 const check=(a,b)=>{assert.deepEqual(a,b);assertions++;};
 const course=JSON.parse(await fs.readFile(path.join(root,'java-course/content/course.json'),'utf8'));
 const out=path.join(root,'.build/java-review/browser');await fs.mkdir(out,{recursive:true});
 try{
  await page.goto(base+'/site/java/#java-02');check(await page.locator('form.task button[type=submit]').first().isDisabled(),true);
  await page.locator('#lesson-nav a[href="#java-01"]').click();await page.locator('h1').filter({hasText:'Первый сигнал'}).waitFor();
  await page.keyboard.press('Tab');
  for(const [index,lesson] of course.lessons.entries()){
   await page.locator('#lesson-nav a[href="#'+lesson.id+'"]').click();await page.locator('h1').filter({hasText:lesson.title}).waitFor();
   for(const [i,task] of lesson.tasks.entries()){
    const form=page.locator('form.task').nth(i),answer=form.locator('input'),reason=form.locator('textarea');
    await reason.fill('Мой прогноз основан на последовательном разборе состояния и проверке границы.');
    await answer.fill('999999');await form.locator('button[type=submit]').click();check(await form.locator('.feedback').evaluate(e=>e.classList.contains('correct')),false);
    await answer.fill(task.answer);await answer.focus();await page.keyboard.press('Enter');check(await form.locator('.feedback').evaluate(e=>e.classList.contains('correct')),true);
    const before=await page.locator('#progress-label').textContent();await form.locator('button[type=submit]').click();check(await page.locator('#progress-label').textContent(),before);
   }
   check(await page.locator('#progress-label').textContent(),(index+1)+' из 10');
  }
  await page.reload();check(await page.locator('#progress-label').textContent(),'10 из 10');
  await page.locator('#lesson-nav a[href="#home"]').click();await page.locator('h1').filter({hasText:'От первого сигнала к своей сети'}).waitFor();
  const lab=page.locator('form').filter({has:page.locator('#edge-weight')});
  for(const w of [1,2,3,99]){await page.locator('#edge-weight').fill(String(w));await page.locator('#prediction').fill(w===1?'6':'7');await lab.locator('button[type=submit]').click();check((await lab.locator('[role=status]').textContent()).includes('Прогноз верный'),true);}
  await page.locator('#edge-closed').check();await page.locator('#prediction').fill('7');await lab.locator('button[type=submit]').click();check((await lab.locator('[role=status]').textContent()).includes('7 минут'),true);
  for(const width of [320,360,768,1440]){
   await page.setViewportSize({width,height:900});
   for(const id of ['home',...course.lessons.map(l=>l.id)]){
    await page.locator('#lesson-nav a[href="#'+id+'"]').click();await page.locator('h1').filter({hasText:id==='home'?'От первого сигнала к своей сети':course.lessons.find(l=>l.id===id).title}).waitFor();
    check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
    await page.waitForFunction(()=>Array.from(document.querySelectorAll('main img')).every(i=>i.complete));check(await page.locator('main img').evaluateAll(images=>images.every(i=>i.naturalWidth>0)),true);
   }
  }
  await page.setViewportSize({width:1440,height:1000});await page.locator('#lesson-nav a[href="#home"]').click();await page.locator('h1').filter({hasText:'От первого сигнала к своей сети'}).waitFor();await page.screenshot({path:path.join(out,'home-desktop.png')});
  await page.setViewportSize({width:360,height:800});await page.screenshot({path:path.join(out,'home-mobile.png')});
  await page.locator('#lesson-nav a[href="#java-01"]').click();await page.reload();await page.keyboard.press('Tab');check(await page.locator('.skip').evaluate(e=>e===document.activeElement),true);await page.keyboard.press('Enter');check(await page.locator('main').evaluate(e=>e===document.activeElement),true);check(new URL(page.url()).hash,'#java-01');
  const form=page.locator('form.task').first();await form.locator('textarea').fill('Трассировка: семь сеансов по двенадцать единиц расходуют восемьдесят четыре.');await form.locator('input').fill('7');await form.locator('button[type=submit]').click();
  const downloadPromise=page.waitForEvent('download');await page.locator('#export').click();const download=await downloadPromise;check((await fs.readFile(await download.path(),'utf8')).includes('Трассировка:'),true);
  await page.locator('#reset').click();check(await page.locator('#progress-label').textContent(),'0 из 10');check(await page.locator('#reset').evaluate(e=>e===document.activeElement),true);
  // Complete one whole lesson using keyboard input only, including wrong/repeated answers and reset.
  await page.reload();await page.keyboard.press('Tab');await page.keyboard.press('Enter');
  const tabTo=async predicate=>{for(let i=0;i<25;i++){const active=await page.evaluate(()=>({id:document.activeElement.id,tag:document.activeElement.tagName,href:document.activeElement.getAttribute('href')}));if(predicate(active))return;await page.keyboard.press('Tab');}throw Error('Keyboard target not reached');};
  for(const [i,task] of course.lessons[0].tasks.entries()){
    const id='java-01-'+task.id;await tabTo(a=>a.id===id);
    await page.keyboard.type(i===0?'0':task.answer);await page.keyboard.press('Tab');await page.keyboard.type('Проверяю состояние программы и отдельно рассматриваю граничный вход.');await page.keyboard.press('Tab');await page.keyboard.press('Space');
    if(i===0){check(await page.locator('form.task').first().locator('.feedback').evaluate(e=>e.classList.contains('correct')),false);await page.keyboard.press('Shift+Tab');await page.keyboard.press('Shift+Tab');await page.keyboard.press('Control+A');await page.keyboard.type(task.answer);await page.keyboard.press('Tab');await page.keyboard.press('Tab');await page.keyboard.press('Enter');}
    check(await page.locator('form.task').nth(i).locator('.feedback').evaluate(e=>e.classList.contains('correct')),true);await page.keyboard.press('Enter');
  }
  check(await page.locator('#progress-label').textContent(),'1 из 10');await tabTo(a=>a.href==='#java-02');await page.keyboard.press('Enter');await page.locator('h1').filter({hasText:'Шлюз доверия'}).waitFor();check(await page.locator('main').evaluate(e=>e===document.activeElement),true);
  await page.keyboard.press('Shift+Tab');check(await page.locator('#reset').evaluate(e=>e===document.activeElement),true);await page.keyboard.press('Space');check(await page.locator('#progress-label').textContent(),'0 из 10');
  await page.goto(base+'/teacher/');await page.locator('#login-form input[name=code]').fill('wrong');await page.locator('#login-button').click();await page.locator('#login-status').filter({hasText:'Код не подошёл'}).waitFor();
  await page.locator('#login-form input[name=code]').fill('lesson');await page.locator('#login-button').click();await page.locator('#materials-panel').waitFor({state:'visible'});
  check(await page.locator('.material-item').count(),18);check(await page.locator('.guide-download').count(),4);
  await page.locator('#logout-button').click();await page.locator('#login-panel').waitFor({state:'visible'});
  check(errors,[]);
  await fs.writeFile(path.join(out,'result.json'),JSON.stringify({assertions,errors,widths:[320,360,768,1440],allLessons:true},null,2));console.log('Browser checks passed: '+assertions+' assertions');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
