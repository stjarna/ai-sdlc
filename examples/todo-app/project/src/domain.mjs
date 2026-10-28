export class AppError extends Error {
  constructor(code, message, status = 400) {
    super(message);
    this.code = code;
    this.status = status;
  }
}

export function isCalendarDate(value) {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const [year, month, day] = value.split('-').map(Number);
  if (year < 1 || month < 1 || month > 12 || day < 1) return false;
  const leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const days = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  return day <= days[month - 1];
}

export function assignInitialDate(repository, id, dueDate, referenceDay) {
  if (!isCalendarDate(referenceDay)) throw new Error('Invalid reference calendar day.');
  const task = repository.get(id);
  if (!task) throw new AppError('TASK_NOT_FOUND', 'Task not found.', 404);
  if (dueDate === null || dueDate === '') {
    throw new AppError('DEMO_NOT_IMPLEMENTED', 'Clearing dates is not implemented in this demonstrator; its product behavior remains undefined.', 501);
  }
  if (!isCalendarDate(dueDate)) {
    throw new AppError('INVALID_DATE', 'Supply a real calendar date in YYYY-MM-DD format.');
  }
  if (task.dueDate !== null) {
    throw new AppError('DEMO_NOT_IMPLEMENTED', 'Changing an assigned date is not implemented in this demonstrator; its product behavior remains undefined.', 501);
  }
  if (dueDate <= referenceDay) {
    throw new AppError('DEMO_NOT_IMPLEMENTED', 'Past/today-date behavior is outside this demonstrator. No product acceptance or rejection rule has been decided.', 501);
  }
  return repository.setDueDate(id, dueDate);
}
