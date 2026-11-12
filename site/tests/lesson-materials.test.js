import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { courseLessons } from '../src/data/course.js';

test('lesson sources describe complete 45-minute lessons with runnable examples', () => {
  for (let number = 1; number <= 8; number++) {
    const id = String(number).padStart(2, '0');
    const lesson = JSON.parse(readFileSync(new URL(`../../lessons/content/lesson-${id}.json`, import.meta.url)));
    assert.equal(lesson.id, id);
    assert.deepEqual(lesson.exercises, courseLessons[number-1].exercises, `${id}: website questions must match teacher materials`);
    assert.ok(courseLessons[number-1].sections.some(section => section.code === lesson.code && section.output === lesson.output.trimEnd()), `${id}: shared main example`);
    assert.ok(lesson.slides.length > 0 && lesson.slides.length <= 30, id);
    assert.equal(lesson.slides.reduce((sum, slide) => sum + slide.minutes, 0), 45, id);
    for (const slide of lesson.slides) {
      assert.ok(slide.title && slide.teacher && slide.action && slide.question && slide.answer, `${id}: ${slide.title}`);
      assert.ok(Number.isFinite(slide.minutes) && slide.minutes > 0, `${id}: ${slide.title}`);
    }
    for (const [code, input, expected] of [
      [lesson.code, lesson.stdin, lesson.output],
      [lesson.solution, lesson.solutionStdin, lesson.solutionOutput],
    ]) {
      const run = spawnSync(process.env.PYTHON || (process.platform === 'win32' ? 'python' : 'python3'), ['-I', '-X', 'utf8', '-c', code], { input, encoding: 'utf8', timeout: 5000 });
      assert.equal(run.status, 0, `${id}: ${run.stderr || run.error}`);
      assert.equal(run.stdout.replace(/\r\n/g, '\n'), expected, id);
    }
  }
});

test('published Office materials match the current lesson sources', () => {
  const script = new URL('../../lessons/scripts/verify_materials.py',import.meta.url);
  const run = spawnSync(process.env.PYTHON || (process.platform === 'win32' ? 'python' : 'python3'), ['-I','-X','utf8',fileURLToPath(script)], {encoding:'utf8',timeout:15000});
  assert.equal(run.status,0,run.stderr || String(run.error));
});
