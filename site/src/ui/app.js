import { courseLessons } from '../data/course.js';
import { Mission, nextMission } from '../domain/Mission.js';
import { ProgressStore } from '../storage/ProgressStore.js';
import { applyTheme, preferences } from './theme.js';

const missions = courseLessons.map(definition => new Mission(definition));
const store = new ProgressStore(() => window.localStorage, missions);
const app = document.querySelector('#app');
let snapshot = store.load();
let introStep = 0;
let introOpen = !preferences.load().introSeen;
let exerciseIndex = 0;
let feedback = null;

/** Escape course text before placing it in HTML. @param {unknown} value Text. @returns {string} Safe HTML. */
function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
}
/** @param {Mission} mission Lesson. @returns {boolean} Whether previous lesson is complete. */
function unlocked(mission) {
  const index = missions.indexOf(mission);
  return mission.isUnlocked(snapshot.completedIds, missions[index - 1] ?? null);
}
/** @returns {{page:string,mission:Mission|null}} Current hash route, validated against the course. */
function route() {
  const [page = 'home', id] = location.hash.slice(1).split('/');
  return {page, mission: missions.find(item => item.id === id) ?? null};
}
/** @param {Mission} mission Lesson. @returns {string} Rendered status. */
function status(mission) {
  return snapshot.completedIds.includes(mission.id) ? 'Пройдено ✓' : unlocked(mission) ? 'Доступен' : 'Пока закрыт';
}
/** @returns {string} Course map and progress. */
function home() {
  const next = nextMission(missions, snapshot.completedIds);
  return `<section class="hero-home"><div><p class="eyebrow">Python для 5–6 классов</p><span class="orbit-label">8 МИССИЙ · ОДИН БОЛЬШОЙ СТАРТ</span><h1>Твой первый код.<br><em>Вселенная открытий.</em></h1><p class="lead">Привет, я Пытик! Отправимся в путешествие по Python: напишем первые программы, соберём робота и создадим свою игру.</p><a class="primary-button" href="#lesson/${escapeHtml(next.id)}">${snapshot.stars ? 'Продолжить обучение' : 'Начать первый урок'} <span aria-hidden="true">→</span></a><button class="text-button" data-action="intro">Как здесь всё устроено?</button></div><div class="hero-universe" aria-label="Пытик на учебной орбите"><span class="orbit orbit-one" aria-hidden="true"></span><span class="orbit orbit-two" aria-hidden="true"></span><span class="planet" aria-hidden="true"></span><span class="space-star star-one" aria-hidden="true">✦</span><span class="space-star star-two" aria-hidden="true">✧</span><img src="assets/pytik-mascot.png" class="home-mascot" alt="Пытик — робот-помощник с карточкой кода"><span class="code-satellite" aria-hidden="true">print("Поехали!")</span></div></section>
    <section class="progress-panel"><div><p class="eyebrow">Бортовой журнал</p><h2>${snapshot.stars === missions.length ? 'Пытик собран!' : 'Собираем Пытика вместе'}</h2><p>За каждый пройденный тест ты получишь одну деталь. Собрано ${snapshot.stars} из ${missions.length}.</p><progress max="${missions.length}" value="${snapshot.stars}" aria-label="Собрано деталей">${snapshot.stars} из ${missions.length}</progress></div><div class="parts" aria-label="Детали робота">${missions.map((m,i) => `<span class="part ${snapshot.completedIds.includes(m.id) ? 'earned' : ''}" title="${escapeHtml(m.title)}">${snapshot.completedIds.includes(m.id) ? '✓' : i+1}</span>`).join('')}</div></section>
    <section class="course-map"><div class="section-header"><div><p class="eyebrow">Путь исследователя</p><h2>Карта миссий</h2></div><span>От первого сообщения до собственной игры</span></div><ol class="course-list">${missions.map((m,i) => `<li class="course-card ${unlocked(m) ? '' : 'locked'}"><span class="course-number">${String(i+1).padStart(2,'0')}</span><div><p class="course-status">${status(m)}</p><h3>${escapeHtml(m.title)}</h3><p>${escapeHtml(m.goal)}</p>${unlocked(m) ? `<a href="#lesson/${escapeHtml(m.id)}">Открыть урок →</a>` : '<span class="locked-label">Сначала пройди предыдущий урок</span>'}</div></li>`).join('')}</ol></section>`;
}
/** @param {Mission} mission Available lesson. @returns {string} Full reading and test link. */
function lesson(mission) {
  const index = missions.indexOf(mission);
  return `<article class="reading"><a class="back-link" href="#home">← Карта миссий</a><header class="reading-header"><p class="eyebrow">Урок ${index+1} из ${missions.length} · ${escapeHtml(mission.concept)}</p><h1>${escapeHtml(mission.title)}</h1><p class="lead">${escapeHtml(mission.goal)}</p></header><div class="reading-layout"><aside class="reading-aside"><img src="assets/pytik-mascot.png" alt="" width="110"><p><strong>Пытик подсказывает</strong></p><p>Читай по порядку и запускай примеры в VS Code. Ошибаться можно — это часть обучения!</p><a href="#test/${escapeHtml(mission.id)}">Перейти к проверке ↓</a></aside><div class="reading-sections">${mission.sections.map((s,i) => `<section class="reading-section"><p class="section-index">${String(i+1).padStart(2,'0')}</p><h2>${escapeHtml(s.title)}</h2>${s.paragraphs.map(p => `<p>${escapeHtml(p)}</p>`).join('')}${s.code ? `<figure><figcaption>Пример Python</figcaption><pre><code>${escapeHtml(s.code)}</code></pre></figure>` : ''}${s.output ? `<figure class="output"><figcaption>Результат</figcaption><pre><code>${escapeHtml(s.output)}</code></pre></figure>` : ''}</section>`).join('')}<section class="ready-card"><h2>Готов проверить себя?</h2><p>В тесте три задания. Если ошибёшься, Пытик поможет подсказкой.</p><a class="primary-button" href="#test/${escapeHtml(mission.id)}">Перейти к тесту →</a></section></div></div></article>`;
}
/** @param {Mission} mission Available lesson. @returns {string} Current question and feedback. */
function test(mission) {
  const exercise = mission.exercises[exerciseIndex];
  const solved = (snapshot.solved[mission.id] ?? []).includes(exercise.id);
  const complete = snapshot.completedIds.includes(mission.id);
  const next = missions[missions.indexOf(mission)+1];
  return `<section class="test-page"><a class="back-link" href="#lesson/${escapeHtml(mission.id)}">← Вернуться к уроку</a><div class="test-heading"><p class="eyebrow">Проверка · ${escapeHtml(mission.title)}</p><h1 id="test-heading" tabindex="-1">Задание ${exerciseIndex+1} из ${mission.exercises.length}</h1><p>Реши все задания, чтобы получить деталь для Пытика.</p></div><div class="test-layout"><article class="challenge"><h2>${escapeHtml(exercise.prompt)}</h2><fieldset class="answers"><legend class="sr-only">Выбери один ответ</legend>${exercise.options.map(([id,label]) => `<label class="answer"><input type="radio" name="answer" value="${escapeHtml(id)}"><span>${escapeHtml(label)}</span></label>`).join('')}</fieldset><button class="primary-button" data-action="check">Проверить ответ</button><p class="feedback ${feedback ? feedback.correct ? 'is-correct' : 'is-error' : ''}" role="status" tabindex="-1">${escapeHtml(feedback?.message ?? (solved ? 'Это задание уже решено. Можешь попробовать ещё раз.' : 'Выбери ответ и нажми «Проверить ответ».'))}</p>${solved && exerciseIndex < mission.exercises.length-1 ? '<button class="primary-button next-question" data-action="next-exercise">Следующее задание →</button>' : ''}${complete ? `<div class="earned-message"><h3>Деталь получена!</h3><p>Ты прошёл тест и помог Пытику. Теперь в коллекции ${snapshot.stars} из ${missions.length} деталей.</p>${next ? `<a class="primary-button" href="#lesson/${escapeHtml(next.id)}">К следующему уроку →</a>` : '<a class="primary-button" href="#home">На карту уроков →</a>'}</div>` : ''}<nav class="exercise-navigation" aria-label="Задания теста">${mission.exercises.map((item,i) => `<button class="question-number ${i===exerciseIndex ? 'active' : ''}" data-exercise="${i}" ${i===exerciseIndex ? 'aria-current="step"' : ''} aria-label="Задание ${i+1}${(snapshot.solved[mission.id]??[]).includes(item.id) ? ', решено' : ''}">${i+1}${(snapshot.solved[mission.id]??[]).includes(item.id) ? ' ✓' : ''}</button>`).join('')}</nav></article><aside class="test-hint"><img src="assets/pytik-mascot.png" alt="" width="180"><p>Не спеши. Если ответ не подошёл, прочитай подсказку и попробуй ещё раз.</p><a href="#lesson/${escapeHtml(mission.id)}">Повторить урок</a></aside></div></section>`;
}
/** @returns {string} Entry point to the password-protected teacher section. */
function materials() {
  return `<section class="materials-page"><a class="back-link" href="#home">← Карта миссий</a><p class="eyebrow">Для преподавателя</p><h1>Кабинет преподавателя</h1><p class="lead">Учебные файлы находятся в закрытом разделе. Для входа потребуется код преподавателя или кодовое слово.</p><p><a class="primary-button" href="../teacher/">Войти в кабинет →</a></p></section>`;
}
const intro = [
  ['Привет, я Пытик!', 'Я помогу тебе освоить Python. В мастерской ты будешь читать уроки, писать код в VS Code и получать детали для моего робота.'],
  ['Выбери урок на карте', 'Начни с первого урока. Прочитай объяснение и попробуй примеры. После успешного теста откроется следующий урок.'],
  ['Проверь себя', 'В конце урока тебя ждут вопросы. Выбери ответ, посмотри подсказку и попробуй снова, если нужно. За все верные ответы ты получишь деталь.'],
  ['Всё готово!', 'Материалы для преподавателя находятся в отдельном разделе. Твой прогресс сохраняется в этом браузере. Приступим?']
];
/** @returns {string} Introductory guide. */
function guide() {
  if (!introOpen) return '';
  const [title,body] = intro[introStep];
  return `<div class="guide-shade"><section class="guide-card" role="dialog" aria-modal="true" aria-labelledby="guide-title"><button class="guide-close" data-action="skip-intro" aria-label="Закрыть знакомство">×</button><img src="assets/pytik-mascot.png" alt="" width="165"><div><p class="eyebrow">Знакомство · ${introStep+1} / ${intro.length}</p><h2 id="guide-title">${title}</h2><p>${body}</p><div class="guide-actions"><button class="primary-button" data-action="next-intro">${introStep===intro.length-1 ? 'К карте уроков' : 'Дальше →'}</button><button class="text-button" data-action="skip-intro">Пропустить</button></div></div></section></div>`;
}
/** Render current route and restore visible feedback after an answer. */
function render() {
  const current=route();
  let content;
  if (current.page === 'materials') content=materials();
  else if (['lesson','test'].includes(current.page) && current.mission && unlocked(current.mission)) content=current.page==='lesson' ? lesson(current.mission) : test(current.mission);
  else if (['lesson','test'].includes(current.page)) content='<section class="empty-page"><h1>Этот урок пока закрыт</h1><p>Сначала пройди предыдущий урок на карте.</p><a href="#home">Вернуться к карте</a></section>';
  else content=home();
  document.querySelector('#content')?.removeAttribute('inert');
  app.innerHTML=`<a class="skip-link" href="#content">К содержимому</a><header class="topbar"><a class="brand" href="#home"><span class="brand-mark">P</span><span>Лаборатория Питона<small>Учимся открывать новое</small></span></a><nav class="main-nav" aria-label="Главное меню"><a href="#home">Уроки</a><a href="../teacher/">Преподавателю</a><button class="text-button" data-action="intro">Помощь</button></nav><span class="score" aria-label="Пройдено миссий: ${snapshot.stars} из ${missions.length}">✦ ${snapshot.stars} / ${missions.length}</span><button class="theme-button" data-action="theme" type="button">Сменить тему</button></header><main id="content" tabindex="-1"><div class="storage-notice" role="status" ${store.persistent?'hidden':''}>Браузер не разрешил сохранить прогресс. Продолжать можно, но при перезагрузке новые результаты могут потеряться.</div>${content}</main><footer><span>Лаборатория Питона · учимся шаг за шагом</span><button class="text-button" data-action="reset">Сбросить прогресс</button></footer>${guide()}`;
  for (const node of app.querySelectorAll('.topbar, main, footer')) node.inert = introOpen;
  applyTheme();
}
/** @param {Mission} mission Current mission. Restore first unsolved question. */
function resumeExercise(mission) {
  const index=mission.exercises.findIndex(e => !(snapshot.solved[mission.id]??[]).includes(e.id));
  exerciseIndex=index < 0 ? 0 : index;
  feedback=null;
}
window.addEventListener('hashchange', () => {
  const current=route();
  if (current.page==='test' && current.mission) resumeExercise(current.mission);
  render();
  document.querySelector('#content')?.focus({preventScroll:true});
  window.scrollTo({top:0,behavior:'auto'});
});
app.addEventListener('click', event => {
  const button=event.target.closest('button');
  if (!button || button.disabled) return;
  const action=button.dataset.action;
  if (action==='intro') { introStep=0; introOpen=true; render(); document.querySelector('.guide-close')?.focus(); }
  if (action==='skip-intro') { preferences.dismissIntro(); introOpen=false; render(); document.querySelector('[data-action="intro"]')?.focus(); }
  if (action==='next-intro') { if (introStep < intro.length-1) introStep++; else { introOpen=false; preferences.dismissIntro(); } render(); document.querySelector(introOpen?'[data-action="next-intro"]':'[data-action="intro"]')?.focus(); }
  if (action==='reset' && window.confirm('Стереть весь прогресс в этом браузере?')) { snapshot=store.reset(); feedback=null; location.hash='#home'; render(); }
  const current=route();
  if (current.page!=='test' || !current.mission || !unlocked(current.mission)) return;
  if (button.dataset.exercise!==undefined) { exerciseIndex=Number(button.dataset.exercise); feedback=null; render(); document.querySelector('#test-heading')?.focus(); }
  if (action==='next-exercise') { exerciseIndex=Math.min(exerciseIndex+1,current.mission.exercises.length-1); feedback=null; render(); document.querySelector('#test-heading')?.focus(); }
  if (action==='check') {
    const answer=document.querySelector('input[name="answer"]:checked')?.value;
    const exercise=current.mission.exercises[exerciseIndex];
    feedback=answer===undefined ? {correct:false,message:'Сначала выбери один ответ.'} : current.mission.validate(answer,exercise.id);
    if (feedback.correct) { snapshot=store.completeExercise(current.mission.id,exercise.id); render(); }
    else { const node=document.querySelector('.feedback'); node.textContent=feedback.message; node.className='feedback is-error'; }
    document.querySelector('.feedback')?.focus({preventScroll:true});
  }
});
if (route().page === 'test' && route().mission) resumeExercise(route().mission);
render();

// Keep keyboard navigation within the open introductory dialog.
app.addEventListener('keydown', event => {
  const dialog=app.querySelector('[role="dialog"]');
  if (!dialog) return;
  if (event.key==='Escape') {
    introOpen=false;
    preferences.dismissIntro();
    render();
    document.querySelector('[data-action="intro"]')?.focus();
    return;
  }
  if (event.key!=='Tab') return;
  const controls=[...dialog.querySelectorAll('button:not(:disabled), a[href]')];
  if (!controls.length) return;
  const first=controls[0], last=controls.at(-1);
  if (event.shiftKey && document.activeElement===first) { event.preventDefault(); last.focus(); }
  else if (!event.shiftKey && document.activeElement===last) { event.preventDefault(); first.focus(); }
});
if (introOpen) document.querySelector('.guide-close')?.focus({preventScroll:true});
