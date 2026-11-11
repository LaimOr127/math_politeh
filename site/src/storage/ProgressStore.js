/** Persists validated progress; storage failures switch to honest in-memory session mode. */
export class ProgressStore {
  #storage;
  #missions;
  #snapshot;
  #persistent = true;
  #key = 'python-lab-progress';

  /** @param {Storage|function():Storage} storage Adapter or lazy provider (may throw). @param {Array<{id:string,exercises:Array<{id:string}>}>} missions Course order and exercise IDs. Reads storage once; preserves completed v1 lessons. */
  constructor(storage, missions) {
    this.#missions = missions.map(m => typeof m === 'string' ? {id:m,exercises:[{id:'main'}]} : m);
    this.#snapshot = this.#empty();
    try {
      this.#storage = typeof storage === 'function' ? storage() : storage;
      const raw = this.#storage.getItem(this.#key);
      if (raw) {
        try { this.#snapshot = this.#restore(JSON.parse(raw)); } catch { this.#snapshot = this.#empty(); }
      }
    } catch { this.#persistent = false; }
  }

  /** @returns {boolean} Whether writes are still backed by browser storage. */
  get persistent() { return this.#persistent; }

  /** @returns {{version:number,completedIds:string[],stars:number,solved:object}} Independent snapshot; no storage access. */
  load() { return structuredClone(this.#snapshot); }

  /** @param {string} missionId Unlocked lesson. @param {string} exerciseId Correctly answered exercise. @returns {object} Updated snapshot. Writes once; repeated answers never award extra parts. */
  completeExercise(missionId, exerciseId) {
    const index = this.#missions.findIndex(m => m.id === missionId);
    const mission = this.#missions[index];
    if (!mission || !mission.exercises.some(e => e.id === exerciseId)) throw new RangeError('Unknown lesson or exercise.');
    if (index > 0 && !this.#snapshot.completedIds.includes(this.#missions[index-1].id)) throw new RangeError('Lesson is locked.');
    const solved = this.#snapshot.solved[missionId] ?? [];
    if (solved.includes(exerciseId)) return this.load();
    this.#snapshot.solved[missionId] = [...solved,exerciseId];
    if (this.#snapshot.solved[missionId].length === mission.exercises.length && !this.#snapshot.completedIds.includes(missionId)) this.#snapshot.completedIds.push(missionId);
    this.#snapshot.stars = this.#snapshot.completedIds.length;
    this.#save();
    return this.load();
  }

  /** @returns {object} Empty snapshot. Clears local/session progress; reports persistence failure through persistent. */
  reset() {
    this.#snapshot = this.#empty();
    if (this.#persistent) {
      try { this.#storage.removeItem(this.#key); } catch { this.#persistent = false; }
    }
    return this.load();
  }

  #empty() { return {version:2,completedIds:[],stars:0,solved:{}}; }
  #save() {
    if (this.#persistent) {
      try { this.#storage.setItem(this.#key,JSON.stringify(this.#snapshot)); } catch { this.#persistent = false; }
    }
  }
  #restore(value) {
    if (!value || ![1,2].includes(value.version) || !Array.isArray(value.completedIds) || !Number.isInteger(value.stars) || value.stars !== value.completedIds.length) return this.#empty();
    if (value.completedIds.some((id,index) => id !== this.#missions[index]?.id)) return this.#empty();
    const result = this.#empty();
    for (const mission of this.#missions) {
      const complete = value.completedIds.includes(mission.id);
      const oldAnswers = value.solved?.[mission.id] ?? [];
      // Previous release awarded a completed lesson for the sole exercise named main.
      const legacyComplete = complete && Array.isArray(oldAnswers) && oldAnswers.length === 1 && oldAnswers[0] === 'main' && !mission.exercises.some(e => e.id === 'main');
      const solved = value.version === 1 || legacyComplete ? (complete ? mission.exercises.map(e => e.id) : []) : oldAnswers;
      if (!Array.isArray(solved) || new Set(solved).size !== solved.length || solved.some(id => !mission.exercises.some(e => e.id === id))) return this.#empty();
      if (complete !== (solved.length === mission.exercises.length)) return this.#empty();
      const index = this.#missions.indexOf(mission);
      if (solved.length && index > 0 && !value.completedIds.includes(this.#missions[index-1].id)) return this.#empty();
      if (solved.length) result.solved[mission.id] = [...solved];
      if (complete) result.completedIds.push(mission.id);
    }
    result.stars = result.completedIds.length;
    return result;
  }
}
