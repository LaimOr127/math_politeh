/** Optional UI regression checks using external Playwright; no site dependencies. */
const {createRequire}=require('node:module');
const fs=require('node:fs/promises');
const path=require('node:path');
const assert=require('node:assert/strict');
if(!process.env.RUNTIME_NODE_MODULES) throw Error('Set RUNTIME_NODE_MODULES to the external tooling directory.');
const {chromium}=createRequire(path.join(process.env.RUNTIME_NODE_MODULES,'playwright/package.json'))('playwright');
const root=path.resolve(__dirname,'../..');
const base=(process.env.BASE_URL||'http://127.0.0.1:8080').replace(/[/]$/,'');
const out=path.join(root,'.build/python-browser');

(async()=>{
  const browser=await chromium.launch({headless:true});
  const context=await browser.newContext({viewport:{width:360,height:900},reducedMotion:'reduce'});
  const page=await context.newPage(),errors=[];
  page.on('pageerror',error=>errors.push(error.message));
  page.on('dialog',dialog=>dialog.accept());
  let assertions=0;
  /** @param {unknown} actual Observed value. @param {unknown} expected Expected value. @param {string} message Context. @returns {void} Counts a passing assertion, throws on failure. */
  const check=(actual,expected,message)=>{assert.deepEqual(actual,expected,message);assertions++;};
  const lessons=await Promise.all(Array.from({length:8},(_,i)=>fs.readFile(path.join(root,'lessons/content/lesson-'+String(i+1).padStart(2,'0')+'.json'),'utf8').then(JSON.parse)));
  /** @param {string} hash Course route. @returns {Promise<void>} Waits for the application heading. */
  async function open(hash){await page.goto(base+'/python/#'+hash);await page.locator('h1').waitFor();}
  try{
    await fs.mkdir(out,{recursive:true});
    await open('home');
    await page.locator('.guide-close').waitFor();
    check(await page.locator('[role=dialog]').getAttribute('aria-modal'),'true');
    await page.keyboard.press('Shift+Tab');
    check(await page.locator('[data-action=skip-intro]').last().evaluate(e=>e===document.activeElement),true,'intro focus trap');
    await page.keyboard.press('Escape');
    await page.reload();await page.keyboard.press('Tab');
    check(await page.locator('.skip-link').evaluate(e=>e===document.activeElement),true);
    await page.keyboard.press('Enter');
    check(await page.locator('#content').evaluate(e=>e===document.activeElement),true);
    await open('test/variables');
    check(await page.locator('input[name=answer]').count(),0,'locked lesson');
    for(const [index,lesson] of lessons.entries()){
      await open('lesson/'+lesson.missionId);
      check(await page.locator('.reading-section').count(),lesson.web.sections.length+1);
      await page.locator('.ready-card a').click();
      for(const [i,exercise] of lesson.exercises.entries()){
        await page.locator('[data-exercise="'+i+'"]').click();
        await page.locator('[data-action=check]').click();
        check(await page.locator('.feedback').innerText(),'Сначала выбери один ответ.');
        const wrong=exercise.options.find(([id])=>id!==exercise.answer)[0];
        await page.locator('input[value="'+wrong+'"]').check();
        await page.locator('[data-action=check]').click();
        check(await page.locator('.feedback').getAttribute('class'),'feedback is-error');
        await page.locator('input[value="'+exercise.answer+'"]').check();
        await page.locator('[data-action=check]').focus();await page.keyboard.press('Enter');
        check(await page.locator('.feedback').getAttribute('class'),'feedback is-correct');
        const score=await page.locator('.score').innerText();
        await page.locator('input[value="'+exercise.answer+'"]').check();
        await page.locator('[data-action=check]').click();
        check(await page.locator('.score').innerText(),score,'repeat never awards twice');
        if(i===0){await page.reload();await page.locator('#test-heading').waitFor();check(await page.locator('#test-heading').innerText(),'Задание 2 из 3');}
      }
      check((await page.locator('.score').innerText()).trim(),'✦ '+(index+1)+' / 8');
    }
    for(const width of [320,360,768,1440]){
      await page.setViewportSize({width,height:900});
      for(const theme of ['light','dark']){
        await open('home');
        if(await page.locator('html').getAttribute('data-theme')!==theme) await page.locator('[data-action=theme]').click();
        await page.reload();check(await page.locator('html').getAttribute('data-theme'),theme,'saved theme');
        for(const hash of ['home',...lessons.flatMap(l=>['lesson/'+l.missionId,'test/'+l.missionId])]){
          await open(hash);
          check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,width+' '+theme+' '+hash);
          check(await page.locator('img').evaluateAll(images=>Promise.all(images.map(image=>image.decode().then(()=>image.naturalWidth>0,()=>false))).then(results=>results.every(Boolean))),true,'images '+hash);
          check(await page.locator('h1').count(),1);
        }
        await open('home');await page.screenshot({path:path.join(out,theme+'-'+width+'.png')});
      }
    }
    await page.locator('[data-action=reset]').click();
    check((await page.locator('.score').innerText()).trim(),'✦ 0 / 8');
    await page.reload();check((await page.locator('.score').innerText()).trim(),'✦ 0 / 8');
    check(await page.locator('[role=dialog]').count(),0,'reset preserves intro preference');
    check(await page.locator('html').getAttribute('data-theme'),'dark','reset preserves theme');
    check(errors,[]);
    // A separate context has no user data; emulate a browser that blocks storage.
    const restricted=await browser.newContext();
    await restricted.addInitScript(()=>Object.defineProperty(window,'localStorage',{get(){throw new DOMException('Blocked','SecurityError');}}));
    const privatePage=await restricted.newPage();
    await privatePage.goto(base+'/python/#home');await privatePage.locator('.guide-close').click();
    check(await privatePage.locator('.storage-notice').isVisible(),true);
    await privatePage.goto(base+'/python/#test/hello');await privatePage.locator('#test-heading').waitFor();
    for(const [i,exercise] of lessons[0].exercises.entries()){
      await privatePage.locator('[data-exercise="'+i+'"]').click();
      await privatePage.locator('input[value="'+exercise.answer+'"]').check();
      await privatePage.locator('[data-action=check]').click();
    }
    check((await privatePage.locator('.score').innerText()).trim(),'✦ 1 / 8','in-memory progress');
    await restricted.close();
    await fs.writeFile(path.join(out,'result.json'),JSON.stringify({base,assertions,errors,lessons:8,questions:24,widths:[320,360,768,1440],themes:['light','dark']},null,2));
    console.log('Python browser checks passed: '+assertions+' assertions');
  }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
