import test from 'node:test';
import assert from 'node:assert/strict';
import { ProgressStore } from '../src/storage/ProgressStore.js';
import { Mission, nextMission } from '../src/domain/Mission.js';
class MemoryStorage {
  values = new Map();
  getItem(key) { return this.values.get(key) ?? null; }
  setItem(key, value) { this.values.set(key, value); }
  removeItem(key) { this.values.delete(key); }
}
const definitions = ['hello', 'variables'].map(id => ({id, exercises: [{id:'a'}, {id:'b'}, {id:'c'}]}));
test('a part requires all exercises and cannot be awarded twice', () => {
  const store = new ProgressStore(new MemoryStorage(), definitions);
  assert.equal(store.completeExercise('hello', 'a').stars, 0);
  assert.equal(store.completeExercise('hello', 'b').stars, 0);
  assert.equal(store.completeExercise('hello', 'c').stars, 1);
  assert.equal(store.completeExercise('hello', 'c').stars, 1);
  assert.throws(() => store.completeExercise('hello','unknown'), RangeError);
});
test('locked lessons cannot be completed directly', () => {
  const store = new ProgressStore(new MemoryStorage(), definitions);
  assert.throws(() => store.completeExercise('variables','a'), RangeError);
});
test('storage getter, reading, writing and reset failures keep session progress', () => {
  for (const operation of ['provider','getItem','setItem','removeItem']) {
    const storage = new MemoryStorage();
    storage[operation] = () => {throw new Error('unavailable');};
    const provider = operation === 'provider' ? () => {throw new Error('blocked');} : () => storage;
    const store = new ProgressStore(provider, definitions);
    store.completeExercise('hello','a');
    store.completeExercise('hello','b');
    assert.equal(store.completeExercise('hello','c').stars,1);
    assert.equal(store.load().stars,1);
    assert.equal(store.reset().stars,0);
    assert.equal(store.load().stars,0);
    assert.equal(store.persistent,false);
  }
});
test('version 1 progress migrates without losing earned parts', () => {
  const storage = new MemoryStorage();
  storage.setItem('python-lab-progress', JSON.stringify({version:1,completedIds:['hello'],stars:1}));
  const result = new ProgressStore(storage,definitions).load();
  assert.deepEqual(result.completedIds,['hello']);
  assert.deepEqual(result.solved.hello,['a','b','c']);
});
test('legacy single-question completions survive the expanded course', () => {
  const storage = new MemoryStorage();
  storage.setItem('python-lab-progress', JSON.stringify({version:2,completedIds:['hello'],stars:1,solved:{hello:['main']}}));
  const result = new ProgressStore(storage,definitions).load();
  assert.deepEqual(result.completedIds,['hello']);
  assert.deepEqual(result.solved.hello,['a','b','c']);
});
test('invalid data and nonsequential completion are rejected', () => {
  for (const value of ['{', JSON.stringify({version:1,completedIds:['variables'],stars:1}),JSON.stringify({version:1,completedIds:['unknown'],stars:1})]) {
    const storage = new MemoryStorage(); storage.setItem('python-lab-progress',value);
    assert.equal(new ProgressStore(storage,definitions).load().stars,0);
  }
});
test('snapshots cannot mutate private stored progress', () => {
  const store = new ProgressStore(new MemoryStorage(),definitions);
  const snapshot = store.completeExercise('hello','a');
  snapshot.solved.hello.push('b','c');
  assert.deepEqual(store.load().solved.hello,['a']);
});
const feedback = {correct:'yes',incorrect:'no'};
const mission = new Mission({id:'first',exercises:[{id:'order',type:'order',lines:[['a','A'],['b','B']],answer:['a','b'],feedback},{id:'choice',type:'choice',options:[['yes','Yes'],['no','No']],answer:'yes',feedback}]});
test('every exercise checks its own answer and ordered arrays exactly', () => {
  assert.equal(mission.validate(['a','b'],'order').correct,true);
  assert.equal(mission.validate(['a|b'],'order').correct,false);
  assert.equal(mission.validate(['b','a'],'order').correct,false);
  assert.equal(mission.validate('yes','choice').correct,true);
  assert.equal(mission.validate(undefined,'choice').correct,false);
  assert.throws(() => mission.validate('yes','missing'),RangeError);
});
test('resume selects next incomplete lesson, or last when course is complete', () => {
  const missions = definitions.map(d => new Mission({...d,exercises:mission.exercises}));
  assert.equal(nextMission(missions,[]).id,'hello');
  assert.equal(nextMission(missions,['hello']).id,'variables');
  assert.equal(nextMission(missions,['hello','variables']).id,'variables');
});
