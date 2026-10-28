import { isCalendarDate } from './domain.mjs';

export function createRepository(seeds = [
  { id: 'task-1', title: 'Prepare a presentation', dueDate: null },
  { id: 'task-2', title: 'Read a book', dueDate: null },
]) {
  const rows = new Map();
  for (const task of seeds) {
    if (!task || typeof task.id !== 'string' || !task.id || rows.has(task.id)
        || typeof task.title !== 'string'
        || !(task.dueDate === null || isCalendarDate(task.dueDate))) {
      throw new Error('Invalid or duplicate seeded task.');
    }
    rows.set(task.id, { id: task.id, title: task.title, dueDate: task.dueDate });
  }
  return {
    list: () => Array.from(rows.values(), task => ({ ...task })),
    get: id => rows.has(id) ? { ...rows.get(id) } : null,
    setDueDate(id, dueDate) {
      if (!rows.has(id) || !isCalendarDate(dueDate)) throw new Error('Invalid repository update.');
      rows.get(id).dueDate = dueDate;
      return { ...rows.get(id) };
    },
  };
}
