import test from 'node:test';
import assert from 'node:assert/strict';
import { fixture, dates, evidenceDirectory, report } from './helpers.mjs';

const dir = await evidenceDirectory('integration');
let sequence = 0;
function integration(name, cases, fn) {
  const filename = `${++sequence}.json`;
  test(name, { timeout: 12000 }, async () => {
    const app = await fixture();
    let status = 'failed';
    try { await fn(app.url); status = 'passed'; }
    finally {
      await app.close();
      await report(dir, filename, { name, cases, status });
    }
  });
}
async function state(url) {
  const response = await fetch(`${url}/api/tasks`);
  assert.equal(response.status, 200);
  return response.json();
}
const post = (url, data, headers = {}) => fetch(`${url}/api/tasks/task-1/due-date`, {
  method: 'POST', headers: { 'Content-Type': 'application/json', ...headers }, body: JSON.stringify(data),
});
integration('TC-001 / FR-002 / AC-002: repeated real reads retain permitted undated state', ['TC-001'], async url => {
  for (let i = 0; i < 2; i++) {
    const data = await state(url);
    assert.equal(data.tasks.length, 2);
    assert.equal(data.tasks[0].dueDate, null);
    assert.equal(data.tasks[1].dueDate, null);
  }
});
for (const date of dates) {
  integration(`TC-002/003 / AC-001/002: exact date ${date}, independent readback and other task untouched`, ['TC-002', 'TC-003'], async url => {
    const before = await state(url);
    assert.equal(before.tasks[0].dueDate, null);
    assert.equal(before.tasks[1].dueDate, null);
    const response = await post(url, { dueDate: date });
    assert.equal(response.status, 200);
    assert.equal((await response.json()).task.dueDate, date);
    const after = await state(url);
    assert.equal(after.tasks[0].id, before.tasks[0].id);
    assert.equal(after.tasks[0].dueDate, date);
    assert.deepEqual(after.tasks[1], before.tasks[1]);
  });
}
integration('Supplementary approved Design controls: malformed bodies and foreign Origin do not mutate', [], async url => {
  const initial = await state(url);
  const foreign = await post(url, { dueDate: dates[0] }, { Origin: 'https://foreign.invalid' });
  assert.equal(foreign.status, 403);
  assert.equal((await foreign.json()).error.code, 'FOREIGN_ORIGIN');
  const malformed = await fetch(`${url}/api/tasks/task-1/due-date`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{' });
  assert.equal(malformed.status, 400);
  assert.equal((await malformed.json()).error.code, 'INVALID_JSON');
  const invalid = await post(url, { dueDate: '2027-02-30' });
  assert.equal(invalid.status, 400);
  assert.equal((await invalid.json()).error.code, 'INVALID_DATE');
  const extra = await post(url, { dueDate: dates[0], other: true });
  assert.equal(extra.status, 400);
  const large = await post(url, { dueDate: 'x'.repeat(5000) });
  assert.equal(large.status, 413);
  assert.deepEqual(await state(url), initial);
});
integration('Supplementary approved Design controls: fixed routes, no artifact exposure and security headers', [], async url => {
  for (const path of ['/requirements/REQ-0001-task-due-date-management/metadata.yaml', '/src/server.mjs', '/..%2fREADME.md']) {
    const response = await fetch(url + path);
    assert.equal(response.status, 404);
    assert.equal((await response.json()).error.code, 'NOT_FOUND');
  }
  const html = await fetch(url);
  assert.equal(html.status, 200);
  assert.match(html.headers.get('content-type'), /text\/html/);
  assert.equal(html.headers.get('x-content-type-options'), 'nosniff');
  assert.match(html.headers.get('content-security-policy'), /script-src 'self'/);
  assert.match(await html.text(), /Task due dates/);
});
console.log('TC-004/TC-005 remain blocked; no past-date or change/clear product outcome is asserted.');
