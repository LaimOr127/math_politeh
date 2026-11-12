# Контракты приложения

## HTTP

API возвращает JSON с Cache-Control no-store. Учебные файлы имеют private no-store. Клиент использует same-origin fetch; HttpOnly cookie JavaScript не читает.

| Метод и путь | Действие | Основные ответы |
| --- | --- | --- |
| GET /health | Проверка процесса | 200 |
| POST /api/teacher/login | JSON с полем code | 200, 400, 401, 403, 413, 429 |
| GET /api/teacher/session | Проверка сессии | 200 или 401 |
| GET /api/teacher/materials | Каталог lessons и guides | 200 или 401 |
| POST /api/teacher/logout | Отзыв сессии | 200, 403 |
| GET /lessons/output/имя | Разрешённый DOCX/PPTX | 200, 401, 404 |

POST требует Content-Type application/json и Origin текущего сайта. За HTTPS-прокси задаётся PUBLIC_ORIGIN. TEACHER_CODES заменяет код по умолчанию lesson; несколько кодов разделяются запятыми.

Cookie python_lab_teacher имеет HttpOnly, SameSite=Strict, Path=/ и срок восемь часов. COOKIE_SECURE=true добавляет Secure. Перезапуск завершает сессии. Лимит — десять попыток за пятнадцать минут на адрес подключения; 429 содержит Retry-After. Старые файлы не выдаются даже после входа.

`createApp({codes, now, sessionMs, maxAttempts, attemptWindowMs, secureCookies, publicOrigin})` возвращает незапущенный http.Server. Параметры времени и лимитов подменяются в тестах. `server/index.js` открывает порт с PORT и HOST.

## Миссии

`new Mission(definition)` валидирует упражнения. `validate(answer, exerciseId)` возвращает `{correct, message}` без побочных эффектов. `isUnlocked(completedIds, previous)` определяет доступность. `nextMission(missions, completedIds)` выбирает первый доступный незавершённый урок, а после курса — последний.

## Прогресс

`new ProgressStore(storage, missions)` получает Storage или функцию адаптера. `load()` возвращает независимую копию `{version:2, completedIds, stars, solved}`. `completeExercise(missionId, exerciseId)` сохраняет ответ и выдаёт деталь после всех упражнений; повтор не увеличивает награду. `reset()` очищает учебный прогресс. `persistent` сообщает о доступности сохранения. При ошибке данные остаются во вкладке.

Версия 1 и прежние завершённые уроки с упражнением main мигрируются. Повреждённые и нарушающие последовательность данные отклоняются.

## Отображение

`PreferencesStore(storage).load()` возвращает `{theme, introSeen}`. `setTheme(theme)` принимает light, dark или system. `dismissIntro()` отмечает просмотр знакомства. Ошибки хранения не мешают работе. `applyTheme()` меняет data-theme и подписи переключателей. До выбора учитывается системная тема.

Маршруты: #home, #lesson/id, #test/id, #materials. После перезагрузки тест открывается на первом нерешённом вопросе. Знакомство удерживает фокус, фон получает inert, Escape закрывает окно.

## Сборка печатных материалов

`build_documents.py [--scientific-only]` читает восемь JSON-уроков и собирает Word-файлы. Флаг ограничивает изменение общим иллюстрированным пособием. `build_illustrations.build_course_figures(lessons)` сохраняет 11 поясняющих PNG из канонических данных в `lessons/illustrations/`; зависимости используются только при авторской сборке.

`update_scientific_contents.py <rendered.pdf> [--docx путь] [--entries путь] [--check]` читает PDF отрисовки и получает реальные страницы 21 пункта содержания. По умолчанию обновляет существующий DOCX через временный ZIP, сохраняя остальные части пакета, и добавляет внутренние ссылки. `--check` сверяет финальную пагинацию без изменения документа. Нужен pdfplumber из Codex runtime.

`verify_materials.py` проверяет все 18 опубликованных Office-файлов по урокам и структуру общего документа: поля, шрифты без подмены темой, интервалы, изображения, подписи, приложения и готовое содержание. `package_materials.py` выполняет проверку и упаковывает ровно эти 18 файлов. Черновики и промежуточные PDF/PNG в поставку не включаются.
