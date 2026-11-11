/** One lesson and its independently checked exercises; never writes progress. */
export class Mission {
  /** @param {object} definition Course content. Throws for malformed exercises. */
  constructor(definition) {
    const exercises = definition?.exercises ?? (definition?.challenge ? [{...definition.challenge, id:'main', feedback:definition.feedback}] : []);
    if (!definition?.id || !exercises.length || new Set(exercises.map(e => e.id)).size !== exercises.length) {
      throw new TypeError('Mission needs an id and unique exercises.');
    }
    for (const exercise of exercises) {
      const choices = exercise.type === 'choice' ? exercise.options : exercise.lines;
      const ids = choices?.map(([id]) => id);
      if (!exercise.id || !['choice','order'].includes(exercise.type) || !ids?.length || new Set(ids).size !== ids.length || !exercise.feedback?.correct || !exercise.feedback?.incorrect) throw new TypeError('Invalid exercise.');
      if (exercise.type === 'choice' ? !ids.includes(exercise.answer) : !Array.isArray(exercise.answer) || exercise.answer.length !== ids.length || new Set(exercise.answer).size !== ids.length || exercise.answer.some(id => !ids.includes(id))) throw new TypeError('Invalid exercise answer.');
    }
    Object.assign(this, structuredClone(definition), {exercises:structuredClone(exercises)});
  }

  /** @param {string|string[]|undefined} answer Pupil answer. @param {string} exerciseId Exercise to check. @returns {{correct:boolean,message:string}} No side effects. */
  validate(answer, exerciseId = this.exercises[0].id) {
    const exercise = this.exercises.find(item => item.id === exerciseId);
    if (!exercise) throw new RangeError('Unknown exercise.');
    const correct = exercise.type === 'order'
      ? Array.isArray(answer) && answer.length === exercise.answer.length && answer.every((id,index) => id === exercise.answer[index])
      : answer === exercise.answer;
    return {correct, message:exercise.feedback[correct ? 'correct' : 'incorrect']};
  }

  /** @param {string[]} completedIds Earned parts. @param {Mission|null} previous Previous lesson. @returns {boolean} Whether the lesson is available. */
  isUnlocked(completedIds, previous) { return previous === null || completedIds.includes(previous.id); }
}

/** @param {Mission[]} missions Ordered lessons. @param {string[]} completedIds Earned parts. @returns {Mission} First unfinished available lesson, or last completed lesson. No side effects. */
export function nextMission(missions, completedIds) {
  return missions.find((mission,index) => !completedIds.includes(mission.id) && mission.isUnlocked(completedIds,missions[index-1] ?? null)) ?? missions.at(-1);
}
