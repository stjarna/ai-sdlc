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

// Controller-level regressions: actual browser script in a small DOM/fetch test double.
// These do not replace independent HTTP or real-browser QA verification.
import vm from 'node:vm';
import { readFileSync } from 'node:fs';

function browserHarness(fetchSteps) {
  const doc = { activeElement: null };
  class Element {
    constructor(tag) { this.tag = tag; this.children = []; this.listeners = {}; this.value = ''; this.disabled = false; this.parent = null; }
    append(...nodes) { for (const node of nodes) { node.parent = this; this.children.push(node); } }
    contains(node) { return this === node || this.children.some(child => child.contains(node)); }
    remove() {
      if (this.contains(doc.activeElement)) doc.activeElement = null;
      if (this.parent) this.parent.children = this.parent.children.filter(child => child !== this);
      this.parent = null;
    }
    replaceChildren(...nodes) { for (const node of [...this.children]) node.remove(); this.append(...nodes); }
    addEventListener(type, fn) { this.listeners[type] = fn; }
    focus() { doc.activeElement = this; }
    reportValidity() { return true; }
  }
  const roots = Object.fromEntries(['tasks', 'feedback', 'reference'].map(id => [id, new Element('div')]));
  doc.querySelector = selector => roots[selector.slice(1)];
  doc.createElement = tag => new Element(tag);
  const requests = [];
  const fetch = async (url, options) => {
    requests.push({ url, options });
    const step = fetchSteps.shift();
    assert.ok(step, 'Unexpected extra HTTP request');
    if (step instanceof Error) throw step;
    return { ok: step.ok ?? true, json: async () => step.body ?? step };
  };
  vm.runInNewContext(readFileSync(new URL('../public/app.js', import.meta.url), 'utf8'), { document: doc, fetch });
  const flush = () => new Promise(resolve => setImmediate(resolve));
  const child = (node, tag) => node.children.find(x => x.tag === tag);
  return { doc, roots, requests, flush, child,
    item: index => roots.tasks.children[index],
    async submit(index) {
      const form = child(roots.tasks.children[index], 'form');
      await form.listeners.submit({ preventDefault() {} });
      await flush();
    },
  };
}
function browserTasks(date = null) {
  return { referenceDay: '2026-10-28', tasks: [
    { id: 'task-1', title: 'First task', dueDate: date },
    { id: 'task-2', title: 'Second task', dueDate: null },
  ] };
}
test('UI regression: saving one task preserves another draft and its focused input', async () => {
  const data = browserTasks('2027-01-01');
  const h = browserHarness([browserTasks(), { task: data.tasks[0] }, data]); await h.flush();
  const first = h.child(h.item(0), 'form'); h.child(first, 'input').value = '2027-01-01';
  const other = h.child(h.item(1), 'form'); const input = h.child(other, 'input');
  input.value = '2028-02-29'; input.focus();
  await h.submit(0);
  assert.equal(h.child(h.item(1), 'form'), other);
  assert.equal(input.value, '2028-02-29');
  assert.equal(h.doc.activeElement, input);
  assert.match(h.child(h.item(0), 'p').textContent, /2027-01-01/);
});
test('UI regression: removed assignment control moves focus to the updated task heading', async () => {
  const data = browserTasks('2027-01-01');
  const h = browserHarness([browserTasks(), { task: data.tasks[0] }, data]); await h.flush();
  const form = h.child(h.item(0), 'form'); h.child(form, 'input').value = '2027-01-01';
  h.child(form, 'button').focus(); await h.submit(0);
  assert.equal(h.doc.activeElement, h.child(h.item(0), 'h2'));
  assert.equal(h.child(h.item(0), 'form'), undefined);
});
test('UI regression: lost successful save response reconciles readback without another mutation', async () => {
  const h = browserHarness([browserTasks(), new Error('Response lost'), browserTasks('2027-01-01')]); await h.flush();
  h.child(h.child(h.item(0), 'form'), 'input').value = '2027-01-01';
  await h.submit(0);
  assert.match(h.child(h.item(0), 'p').textContent, /2027-01-01/);
  assert.equal(h.child(h.item(0), 'form'), undefined);
  assert.match(h.roots.feedback.textContent, /confirmed/i);
  assert.equal(h.requests.filter(r => r.options?.method === 'POST').length, 1);
  assert.equal(h.requests.length, 3);
});
test('UI regression: failed save and failed readback block retry with an unknown-outcome message', async () => {
  const h = browserHarness([browserTasks(), new Error('Response lost'), new Error('Read unavailable')]); await h.flush();
  const form = h.child(h.item(0), 'form'); h.child(form, 'input').value = '2027-01-01';
  await h.submit(0);
  assert.equal(h.child(form, 'button').disabled, true);
  assert.match(h.roots.feedback.textContent, /unknown.*reload/i);
  const count = h.requests.length; await h.submit(0); assert.equal(h.requests.length, count);
});
test('UI regression: readback proving no save permits a manual retry and retains the draft', async () => {
  const h = browserHarness([browserTasks(), new Error('Response lost'), browserTasks()]); await h.flush();
  const form = h.child(h.item(0), 'form'); const input = h.child(form, 'input'); input.value = '2027-01-01';
  await h.submit(0);
  assert.equal(h.child(h.item(0), 'form'), form);
  assert.equal(input.value, '2027-01-01');
  assert.equal(h.child(form, 'button').disabled, false);
  assert.match(h.roots.feedback.textContent, /still undated.*try again/i);
});
test('UI regression: known successful save survives a failed subsequent refresh', async () => {
  const data = browserTasks('2027-01-01');
  const h = browserHarness([browserTasks(), { task: data.tasks[0] }, new Error('Read unavailable')]); await h.flush();
  h.child(h.child(h.item(0), 'form'), 'input').value = '2027-01-01';
  const other = h.child(h.child(h.item(1), 'form'), 'input'); other.value = '2028-02-29';
  await h.submit(0);
  assert.match(h.child(h.item(0), 'p').textContent, /2027-01-01/);
  assert.equal(h.child(h.item(0), 'form'), undefined);
  assert.equal(other.value, '2028-02-29');
  assert.match(h.roots.feedback.textContent, /saved.*refresh/i);
});

test('UI regression: rejected input retains the useful server diagnostic after readback', async () => {
  const h = browserHarness([browserTasks(), { ok: false, body: { error: { message: 'Supply a real calendar date.' } } }, browserTasks()]); await h.flush();
  const form = h.child(h.item(0), 'form'); h.child(form, 'input').value = 'bad';
  await h.submit(0);
  assert.match(h.roots.feedback.textContent, /Supply a real calendar date/);
  assert.equal(h.child(form, 'button').disabled, false);
});
test('UI regression: different saved date is reported without claiming the attempted date succeeded', async () => {
  const h = browserHarness([browserTasks(), new Error('Response lost'), browserTasks('2027-02-01')]); await h.flush();
  h.child(h.child(h.item(0), 'form'), 'input').value = '2027-01-01';
  await h.submit(0);
  assert.match(h.child(h.item(0), 'p').textContent, /2027-02-01/);
  assert.match(h.roots.feedback.textContent, /attempted date was not confirmed/);
  assert.equal(h.child(h.item(0), 'form'), undefined);
});
