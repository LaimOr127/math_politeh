import { applyTheme } from '/site/src/ui/theme.js';

const form = document.querySelector('#login-form');
const status = document.querySelector('#login-status');
const button = document.querySelector('#login-button');
const loginPanel = document.querySelector('#login-panel');
const materialsPanel = document.querySelector('#materials-panel');
const course = location.pathname.match(/^\/(python|java)\/teacher\/(?:index\.html)?$/)?.[1] ?? '';
const courseHome = course ? '/'+course+'/' : '/python/';
for (const a of document.querySelectorAll('[data-course-home]')) a.href=courseHome;
if (course) {
  const java=course === 'java';
  const title=java ? 'Орбита Java' : 'Лаборатория Питона';
  document.title='Преподавателю · '+title;
  document.querySelector('#course-name').textContent=title;
  document.querySelector('#course-intro').textContent='Презентации, сценарии и пособия по '+(java ? 'Java для 10–11 классов.' : 'Python для 5–6 классов.');
  document.querySelector('#materials-heading').textContent='Материалы курса '+(java ? 'Java' : 'Python');
  document.querySelector('#course-summary').textContent=(java ? '10 занятий по 90 минут.' : '8 занятий по 45 минут.')+' Презентации и сценарии расположены по порядку.';
  document.querySelector('#course-runtime').textContent='Примеры выполняются локально в '+(java ? 'JDK 21.' : 'Python 3.')+' Ответы и решения находятся в сценариях преподавателя.';
  document.querySelector('#course-footer').textContent=title;
}


/** @param {string} text Caption. @param {string} url Protected file URL. @returns {HTMLAnchorElement} Detached download link. */
function link(text,url) {const a=document.createElement('a');a.textContent=text;a.href=url;a.download='';return a;}

/** @param {boolean} focus Focus heading. @returns {Promise<void>} Loads protected catalogue into the page. */
async function showMaterials(focus = true) {
  const response=await fetch('/api/teacher/materials'+(course ? '?course='+course : ''),{cache:'no-store'});
  if (!response.ok) throw new Error('Сессия завершилась. Введите код ещё раз.');
  const data=await response.json();
  const catalog=course ? data : {guides:[...data.guides,...(data.javaCourse?.guides ?? [])],lessons:[...data.lessons,...(data.javaCourse?.lessons ?? [])]};
  document.querySelector('#guide-links').replaceChildren(...catalog.guides.map(guide => {const a=link(guide.title+' ↓',guide.url);a.className='guide-download';return a;}));
  document.querySelector('#lesson-links').replaceChildren(...catalog.lessons.map(lesson => {
    const article=document.createElement('article');article.className='material-item';
    const info=document.createElement('div');const number=document.createElement('p');number.className='eyebrow';number.textContent=`${lesson.duration ? 'Java · Занятие' : 'Python · Миссия'} ${lesson.id} · ${lesson.duration ?? 45} минут`;
    const title=document.createElement('h3');title.textContent=lesson.title;info.append(number,title);
    const links=document.createElement('div');links.className='material-links';links.append(link('Презентация ↓',lesson.presentation),link('Сценарий Word ↓',lesson.script));
    article.append(info,links);return article;
  }));
  loginPanel.hidden=true;materialsPanel.hidden=false;form.reset();status.textContent='';
  if(focus) document.querySelector('#materials-heading').focus();
}
form.addEventListener('submit',async event => {
  event.preventDefault();button.disabled=true;status.textContent='Проверяем код…';
  try {
    const response=await fetch('/api/teacher/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({code:form.elements.code.value})});
    const data=await response.json();
    if(!response.ok) throw new Error(data.message);
    await showMaterials();
  } catch(error) {status.textContent=error.message || 'Не удалось связаться с сервером.';form.elements.code.focus();}
  finally {button.disabled=false;}
});
document.querySelector('#logout-button').addEventListener('click',async event => {
  event.target.disabled=true;
  try {
    const response=await fetch('/api/teacher/logout',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});
    if(!response.ok) throw Error('Не удалось выйти. Повторите попытку.');
    materialsPanel.hidden=true;loginPanel.hidden=false;form.elements.code.focus();
  } catch(error) {window.alert(error.message);} finally {event.target.disabled=false;}
});
applyTheme();
fetch('/api/teacher/session',{cache:'no-store'}).then(response => {if(response.ok) return showMaterials(false);}).catch(() => {status.textContent='Проверьте соединение с сервером.';});
