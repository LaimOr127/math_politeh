import test from 'node:test';
import assert from 'node:assert/strict';
import { courseLessons } from '../src/data/course.js';
import { Mission } from '../src/domain/Mission.js';

test('each course lesson has readable sections and three valid questions', () => {
  assert.deepEqual(courseLessons.map(lesson => lesson.id), ['hello','variables','input','condition','loop','list','function','project']);
  for (const lesson of courseLessons) {
    assert.ok(lesson.sections.length >= 3, lesson.id);
    assert.ok(lesson.sections.every(section => section.title && section.paragraphs.length), lesson.id);
    assert.equal(lesson.exercises.length, 3, lesson.id);
    const mission = new Mission(lesson);
    for (const exercise of lesson.exercises) {
      assert.equal(mission.validate(exercise.answer, exercise.id).correct, true);
      assert.equal(mission.validate(undefined, exercise.id).correct, false);
    }
  }
});
