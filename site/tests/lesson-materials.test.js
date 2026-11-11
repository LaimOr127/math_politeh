import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';

test('lesson sources describe complete 45-minute lessons with runnable examples', () => {
  for (let number = 1; number <= 8; number++) {
    const id = String(number).padStart(2, '0');
    const lesson = JSON.parse(readFileSync(new URL(`../../lessons/content/lesson-${id}.json`, import.meta.url)));
    assert.equal(lesson.id, id);
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
      const run = spawnSync(process.env.PYTHON || 'python3', ['-I', '-c', code], { input, encoding: 'utf8', timeout: 5000 });
      assert.equal(run.status, 0, `${id}: ${run.stderr || run.error}`);
      assert.equal(run.stdout, expected, id);
    }
  }
});
