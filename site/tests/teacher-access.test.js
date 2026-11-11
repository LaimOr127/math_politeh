import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

test('teacher resources are linked from the protected page, not the student app', async () => {
  const app = await readFile(new URL('../src/ui/app.js', import.meta.url), 'utf8');
  const teacher = await readFile(new URL('../../teacher/index.html', import.meta.url), 'utf8');
  assert.match(app, /href="\.\.\/teacher\/"/);
  assert.doesNotMatch(app, /lessons\/output/);
  assert.match(teacher, /lessons\/output\/new-learning-guide\.docx/);
  for (let i = 1; i <= 8; i++) {
    const id = String(i).padStart(2, '0');
    assert.ok(teacher.includes(`lesson-${id}-teacher-script.docx`));
  }
});
