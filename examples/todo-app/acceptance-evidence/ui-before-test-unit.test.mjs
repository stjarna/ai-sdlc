import test from 'node:test';
import assert from 'node:assert/strict';
import { isCalendarDate, assignInitialDate, AppError } from '../src/domain.mjs';
import { createRepository } from '../src/repository.mjs';
const day = '2026-10-28';
for (const date of ['2026-12-31', '2027-01-01', '2028-02-29', '2000-02-29', '0001-01-01', '9999-12-31']) {
  test(`real calendar date ${date}`, () => assert.equal(isCalendarDate(date), true));
}
for (const date of ['2026-02-29', '1900-02-29', '2026-04-31', '2026-00-01', '2026-13-01', '2026-01-00', '0000-01-01', '2026-1-01', '2026-01-01T12:00:00Z', ' 2026-01-01', null, 20261028, {}, ['2027-01-01']]) {
  test(`reject non-calendar value ${JSON.stringify(date)}`, () => assert.equal(isCalendarDate(date), false));
}
test('FR-002 / AC-002: leaving tasks alone preserves permitted absence', () => {
  const r = createRepository();
  assert.deepEqual(r.list().map(t => t.dueDate), [null, null]);
  r.list();
  assert.equal(r.get('task-1').dueDate, null);
});
for (const date of ['2026-12-31', '2027-01-01', '2028-02-29']) {
  test(`FR-001 / AC-001: exact initial date ${date}, other task stays undated`, () => {
    const r = createRepository();
    assert.equal(assignInitialDate(r, 'task-1', date, day).dueDate, date);
    assert.equal(r.get('task-1').dueDate, date);
    assert.equal(r.get('task-2').dueDate, null);
  });
}
test('returned copies cannot mutate stored or seeded state', () => {
  const seed = { id: 'a', title: '<script>alert(1)</script>', dueDate: null };
  const r = createRepository([seed]); seed.dueDate = '2027-01-01';
  r.get('a').title = 'changed'; r.list()[0].dueDate = '2027-01-01';
  assert.equal(r.get('a').title, '<script>alert(1)</script>');
  assert.equal(r.get('a').dueDate, null);
});
test('repositories isolate independent fixtures', () => {
  const a = createRepository(), b = createRepository();
  assignInitialDate(a, 'task-1', '2027-01-01', day);
  assert.equal(b.get('task-1').dueDate, null);
});
test('invalid structural input leaves state unchanged', () => {
  const r = createRepository();
  assert.throws(() => assignInitialDate(r, 'task-1', '2027-02-30', day), e => e instanceof AppError && e.code === 'INVALID_DATE');
  assert.equal(r.get('task-1').dueDate, null);
});
test('unknown target returns controlled error without mutation', () => {
  const r = createRepository(); const before = r.list();
  assert.throws(() => assignInitialDate(r, 'missing', '2027-01-01', day), e => e.status === 404 && e.code === 'TASK_NOT_FOUND');
  assert.deepEqual(r.list(), before);
});
test('past/today demonstrator boundaries are not product-policy decisions', () => {
  const r = createRepository();
  for (const date of ['2026-10-27', day]) {
    assert.throws(() => assignInitialDate(r, 'task-1', date, day), e => e.status === 501 && e.code === 'DEMO_NOT_IMPLEMENTED');
    assert.equal(r.get('task-1').dueDate, null);
  }
});
test('change/clear demonstrator boundaries preserve state without defining product policy', () => {
  const r = createRepository(); assignInitialDate(r, 'task-1', '2027-01-01', day);
  for (const date of ['2027-02-01', null, '']) {
    assert.throws(() => assignInitialDate(r, 'task-1', date, day), e => e.status === 501 && e.code === 'DEMO_NOT_IMPLEMENTED');
    assert.equal(r.get('task-1').dueDate, '2027-01-01');
  }
});
test('invalid reference day cannot silently classify an assignment', () => {
  const r = createRepository();
  assert.throws(() => assignInitialDate(r, 'task-1', '2027-01-01', 'bad'), /Invalid reference/);
  assert.equal(r.get('task-1').dueDate, null);
});
test('invalid or duplicate seed records fail explicitly', () => {
  const task = {id:'a', title:'test', dueDate:null};
  assert.throws(() => createRepository([task, task]), /Invalid or duplicate/);
  assert.throws(() => createRepository([{...task, dueDate:'2026-02-30'}]), /Invalid or duplicate/);
});
