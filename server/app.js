import http from 'node:http';
import { createHash, randomBytes, timingSafeEqual } from 'node:crypto';
import { readFile, stat } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { courseLessons } from '../site/src/data/course.js';

const ROOT = fileURLToPath(new URL('../', import.meta.url));
const COOKIE = 'python_lab_teacher';
const MIME = {'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'text/javascript; charset=utf-8','.json':'application/json; charset=utf-8','.webp':'image/webp','.png':'image/png','.svg':'image/svg+xml','.woff2':'font/woff2','.ico':'image/x-icon','.docx':'application/vnd.openxmlformats-officedocument.wordprocessingml.document','.pptx':'application/vnd.openxmlformats-officedocument.presentationml.presentation'};
const digest = value => createHash('sha256').update(value).digest();

/** @param {object} options Server settings; codes stay on the server. @returns {http.Server} Unbound HTTP server. Sessions are held in memory until logout, expiry or restart. */
export function createApp({codes = (process.env.TEACHER_CODES ?? 'lesson').split(',').map(s => s.trim()).filter(Boolean), now = Date.now, sessionMs = 8*60*60*1000, maxAttempts = 10, attemptWindowMs = 15*60*1000, secureCookies = process.env.COOKIE_SECURE === 'true', publicOrigin = process.env.PUBLIC_ORIGIN} = {}) {
  if (!codes.length || codes.some(code => typeof code !== 'string' || !code.length)) throw new Error('Set at least one teacher code.');
  if (publicOrigin) publicOrigin = new URL(publicOrigin).origin;
  const hashes = codes.map(digest), sessions = new Map(), attempts = new Map();
  const lessons = courseLessons.map((lesson,i) => {
    const id = String(i+1).padStart(2,'0');
    return {id, title:lesson.title, presentation:`/lessons/output/lesson-${id}-presentation.pptx`, script:`/lessons/output/lesson-${id}-teacher-script.docx`};
  });
  const guides = [{title:'Краткое пособие ученика',url:'/lessons/output/new-learning-guide.docx'},{title:'Научно методическое пособие',url:'/lessons/output/scientific-methodical-guide.docx'}];
  const allowedFiles = new Set([...lessons.flatMap(l => [l.presentation,l.script]),...guides.map(g => g.url)]);

  const server = http.createServer(async (req,res) => {
    res.setHeader('X-Content-Type-Options','nosniff');
    res.setHeader('Referrer-Policy','same-origin');
    res.setHeader('X-Frame-Options','DENY');
    res.setHeader('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'");
    const json = (status, value, headers = {}) => {res.writeHead(status,{'Content-Type':MIME['.json'],'Cache-Control':'no-store',...headers});res.end(JSON.stringify(value));};
    try {
      const url = new URL(req.url,'http://localhost');
      let pathname;
      try { pathname = decodeURIComponent(url.pathname); } catch {return json(400,{message:'Некорректный адрес.'});}
      if (pathname.includes('\\') || pathname.includes('\0') || pathname.split('/').some(p => p === '..' || p.startsWith('.'))) return json(404,{message:'Страница не найдена.'});
      const timestamp = now();
      // Bound retained state and discard expired entries on every request.
      for (const [key,value] of sessions) if (value <= timestamp) sessions.delete(key);
      for (const [key,value] of attempts) if (value.until <= timestamp) attempts.delete(key);
      const token = req.headers.cookie?.split(';').map(s => s.trim()).find(s => s.startsWith(COOKIE+'='))?.slice(COOKIE.length+1);
      const authenticated = token && sessions.has(token);
      if (req.method === 'POST') {
        const expectedOrigin = publicOrigin || `${req.socket.encrypted ? 'https' : 'http'}://${req.headers.host}`;
        if (req.headers.origin !== expectedOrigin || req.headers['content-type']?.split(';')[0] !== 'application/json') return json(403,{message:'Откройте форму на сайте и повторите попытку.'});
      }
      const cookie = (value,maxAge) => `${COOKIE}=${value}; Path=/; HttpOnly; SameSite=Strict; Max-Age=${maxAge}${secureCookies ? '; Secure' : ''}`;
      if (pathname === '/api/teacher/login' && req.method === 'POST') {
        const ip = req.socket.remoteAddress;
        const attempt = attempts.get(ip) ?? {count:0,until:timestamp+attemptWindowMs};
        if (attempt.count >= maxAttempts) return json(429,{message:'Слишком много попыток. Попробуйте позже.'},{'Retry-After':String(Math.ceil((attempt.until-timestamp)/1000))});
        if (!attempts.has(ip) && attempts.size >= 10000) return json(503,{message:'Попробуйте позже.'});
        attempt.count++; attempts.set(ip,attempt);
        const chunks = [];
        let bytes = 0;
        for await (const chunk of req) {
          bytes += chunk.length;
          if (bytes > 2048) return json(413,{message:'Слишком длинный код.'});
          chunks.push(chunk);
        }
        let value;
        try {value = JSON.parse(Buffer.concat(chunks).toString('utf8'));} catch {return json(400,{message:'Некорректный запрос.'});}
        if (!value || typeof value !== 'object' || Array.isArray(value) || typeof value.code !== 'string') return json(400,{message:'Некорректный запрос.'});
        const candidate = digest(value.code.trim());
        if (!hashes.some(hash => timingSafeEqual(candidate,hash))) return json(401,{message:'Код не подошёл. Проверьте его и попробуйте снова.'});
        if (sessions.size >= 10000) return json(503,{message:'Попробуйте позже.'});
        if (token) sessions.delete(token);
        const session = randomBytes(32).toString('hex');
        sessions.set(session,timestamp+sessionMs);
        return json(200,{authenticated:true},{'Set-Cookie':cookie(session,Math.floor(sessionMs/1000))});
      }
      if (pathname === '/api/teacher/logout' && req.method === 'POST') {
        sessions.delete(token);
        return json(200,{authenticated:false},{'Set-Cookie':cookie('',0)});
      }
      if (!['GET','HEAD'].includes(req.method)) return json(405,{message:'Метод не поддерживается.'},{Allow:'GET, HEAD, POST'});
      if (pathname.startsWith('/api/teacher/')) {
        if (!authenticated) return json(401,{message:'Введите код преподавателя.'});
        if (pathname === '/api/teacher/session') return json(200,{authenticated:true});
        if (pathname === '/api/teacher/materials') return json(200,{lessons,guides});
        return json(404,{message:'Страница не найдена.'});
      }
      if (pathname.startsWith('/lessons/')) {
        if (!authenticated) return json(401,{message:'Для скачивания войдите в кабинет преподавателя.'});
        if (!allowedFiles.has(pathname)) return json(404,{message:'Файл не найден.'});
      } else if (!pathname.startsWith('/site/') && !['/teacher/','/teacher/index.html','/teacher/app.js'].includes(pathname)) {
        if (pathname === '/' || pathname === '/site' || pathname === '/teacher') {res.writeHead(302,{Location:pathname === '/teacher' ? '/teacher/' : '/site/'});return res.end();}
        if (pathname === '/health') return json(200,{status:'ok'});
        return json(404,{message:'Страница не найдена.'});
      }
      if (pathname.endsWith('/')) pathname += 'index.html';
      const filename = path.resolve(ROOT,'.'+pathname);
      if (!filename.startsWith(ROOT)) return json(404,{message:'Файл не найден.'});
      const info = await stat(filename).catch(() => null);
      if (!info?.isFile()) return json(404,{message:'Файл не найден.'});
      res.setHeader('Content-Type',MIME[path.extname(filename)] || 'application/octet-stream');
      res.setHeader('Cache-Control', pathname.startsWith('/lessons/') ? 'private, no-store' : 'no-cache');
      res.setHeader('Content-Length',info.size);
      if (pathname.startsWith('/lessons/')) res.setHeader('Content-Disposition',`attachment; filename="${path.basename(filename)}"`);
      if (req.method === 'HEAD') return res.end();
      res.end(await readFile(filename));
    } catch (error) {
      console.error('Request failed:', error.message);
      if (!res.headersSent) json(500,{message:'Не удалось выполнить запрос. Повторите позже.'});
      else res.end();
    }
  });
  server.requestTimeout = 15000;
  server.headersTimeout = 10000;
  return server;
}
