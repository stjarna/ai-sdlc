import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { fixture, dates, evidenceDirectory, report, reportFile } from './helpers.mjs';

const dir = await evidenceDirectory('ui');
const browser = await chromium.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true });
console.log(`Browser ${browser.version()}; Playwright 1.64.1; existing Chrome only, no browser download`);
let sequence = 0;
async function scenario(name, cases, fn, seeds) {
  const id = `${++sequence}`;
  const app = await fixture(seeds);
  const context = await browser.newContext({ viewport: { width: 1100, height: 900 } });
  const page = await context.newPage();
  page.setDefaultTimeout(10000);
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await context.route('**/*', route => route.request().url().startsWith(app.url + '/') ? route.continue() : route.abort());
  await context.tracing.start({ screenshots: true, snapshots: true, sources: false });
  let status = 'failed';
  try {
    await page.goto(app.url);
    await page.locator('#tasks li').nth(1).waitFor();
    await fn(page, app.url);
    assert.deepEqual(errors, [], 'Unhandled browser script errors');
    status = 'passed';
  } finally {
    try {
      const screenshot = new URL(`${id}-${status}.png`, dir);
      await page.screenshot({ path: screenshot.pathname, fullPage: true });
      await reportFile(screenshot);
      const trace = new URL(`${id}-trace.zip`, dir);
      await context.tracing.stop({ path: trace.pathname });
      await reportFile(trace);
      await report(dir, `${id}.json`, { name, cases, status, pageErrors: errors });
    } finally { await context.close(); await app.close(); }
  }
}
const input = (page, index) => page.locator('#tasks li').nth(index).locator('input[type=date]');
const button = (page, index) => page.locator('#tasks li').nth(index).getByRole('button', { name: 'Assign due date' });
async function expectDate(page, index, date) {
  await page.locator('#tasks li').nth(index).getByText(`Due date: ${date}`, { exact: true }).waitFor();
}
async function state(url) {
  const response = await fetch(`${url}/api/tasks`);
  assert.equal(response.status, 200);
  return response.json();
}
try {
  await scenario('TC-001 / AC-002: undated state remains valid through real UI reload', ['TC-001'], async (page, url) => {
    assert.equal(await page.getByText('No due date', { exact: true }).count(), 2);
    await page.reload();
    await page.locator('#tasks li').nth(1).waitFor();
    assert.equal(await page.getByText('No due date', { exact: true }).count(), 2);
    const data = await state(url);
    assert.ok(data.tasks.every(task => task.dueDate === null));
  });
  for (const date of dates) {
    await scenario(`TC-002/003 / AC-001/002: actual date input assignment ${date} and independent readback`, ['TC-002', 'TC-003'], async (page, url) => {
      await input(page, 0).fill(date);
      await button(page, 0).click();
      await expectDate(page, 0, date);
      assert.equal(await page.locator('#tasks li').nth(1).getByText('No due date', { exact: true }).count(), 1);
      const data = await state(url);
      assert.equal(data.tasks[0].dueDate, date);
      assert.equal(data.tasks[1].dueDate, null);
      await page.reload();
      await expectDate(page, 0, date);
    });
  }
  await scenario('R1: unrelated draft and active input survive delayed response; submitted form has focus fallback', ['TC-002', 'TC-003'], async page => {
    let release;
    const gate = new Promise(resolve => { release = resolve; });
    const handler = async route => { await gate; await route.continue(); };
    await page.route('**/api/tasks/task-1/due-date', handler);
    await input(page, 0).fill(dates[0]);
    const started = page.waitForRequest(request => request.method() === 'POST');
    await button(page, 0).click();
    await started;
    await input(page, 1).fill(dates[1]);
    await input(page, 1).focus();
    release();
    await expectDate(page, 0, dates[0]);
    assert.equal(await input(page, 1).inputValue(), dates[1]);
    assert.ok(await input(page, 1).evaluate(element => element === document.activeElement));
    await page.unroute('**/api/tasks/task-1/due-date', handler);
    await button(page, 1).click();
    await expectDate(page, 1, dates[1]);
    assert.ok(await page.locator('#tasks li').nth(1).locator('h2').evaluate(element => element === document.activeElement));
  });
  await scenario('R2: server commits, response lost; readback confirms without duplicate POST', ['TC-002', 'TC-003'], async (page, url) => {
    let posts = 0;
    await page.route('**/api/tasks/task-1/due-date', async route => {
      posts++;
      const response = await route.fetch();
      assert.equal(response.status(), 200);
      await route.abort('failed');
    });
    await input(page, 0).fill(dates[0]);
    await button(page, 0).click();
    await page.getByRole('status').filter({ hasText: 'Due date confirmed from current task state.' }).waitFor();
    await expectDate(page, 0, dates[0]);
    assert.equal(posts, 1);
    const data = await state(url);
    assert.equal(data.tasks[0].dueDate, dates[0]);
    assert.equal(data.tasks[1].dueDate, null);
  });
  await scenario('R2: unknown outcome blocks repeat mutation until task state is reloaded', ['TC-001'], async page => {
    let posts = 0;
    await page.route('**/api/tasks', route => route.abort('failed'));
    await page.route('**/api/tasks/task-1/due-date', route => { posts++; return route.abort('failed'); });
    await input(page, 0).fill(dates[0]);
    await button(page, 0).click();
    await page.getByRole('status').filter({ hasText: 'Save outcome unknown.' }).waitFor();
    assert.equal(await button(page, 0).isDisabled(), true);
    await input(page, 0).press('Enter');
    assert.equal(posts, 1);
  });
  await scenario('Supplementary approved Design control: seeded hostile text renders literally, not as markup', ['TC-001'], async page => {
    await page.getByRole('heading', { name: '<img src=x onerror="window.injected=true">', exact: true }).waitFor();
    assert.equal(await page.locator('#tasks img').count(), 0);
    assert.equal(await page.evaluate(() => window.injected), undefined);
    assert.equal(await page.getByText('No due date', { exact: true }).count(), 2);
  }, [
    { id: 'task-1', title: '<img src=x onerror="window.injected=true">', dueDate: null },
    { id: 'task-2', title: 'Undated control task', dueDate: null },
  ]);
  console.log('All declared browser scenarios completed. TC-004/TC-005 remain blocked, not passed.');
} finally { await browser.close(); }
