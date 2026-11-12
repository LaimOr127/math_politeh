import test from 'node:test';
import assert from 'node:assert/strict';
import { PreferencesStore } from '../src/storage/ProgressStore.js';

test('theme and introduction persist independently of course progress', () => {
  const data = new Map();
  const storage = {getItem:key => data.get(key),setItem:(key,value) => data.set(key,value)};
  const preferences = new PreferencesStore(storage);
  assert.deepEqual(preferences.load(),{theme:'system',introSeen:false});
  preferences.setTheme('dark'); preferences.dismissIntro();
  assert.deepEqual(new PreferencesStore(storage).load(),{theme:'dark',introSeen:true});
  assert.throws(() => preferences.setTheme('invalid'),RangeError);
});

test('preferences tolerate blocked storage and malformed saved values', () => {
  const blocked = new PreferencesStore(() => {throw Error('blocked');});
  blocked.setTheme('light'); blocked.dismissIntro();
  assert.deepEqual(blocked.load(),{theme:'light',introSeen:true});
  const malformed = new PreferencesStore({getItem:() => '{"theme":"broken","introSeen":"yes"}'});
  assert.deepEqual(malformed.load(),{theme:'system',introSeen:false});
});
