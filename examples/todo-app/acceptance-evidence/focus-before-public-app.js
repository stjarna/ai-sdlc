const taskList = document.querySelector('#tasks');
const feedback = document.querySelector('#feedback');
const reference = document.querySelector('#reference');
const rows = new Map();

async function api(path, options) {
  const response = await fetch(path, options);
  const body = await response.json();
  if (!response.ok) throw new Error(body.error?.message ?? 'Request failed.');
  return body;
}

function render(tasks) {
  for (const task of tasks) {
    let row = rows.get(task.id);
    if (!row) {
      const item = document.createElement('li');
      const heading = document.createElement('h2');
      heading.tabIndex = -1;
      const date = document.createElement('p');
      item.append(heading, date);
      row = { item, heading, date, form: null, busy: false, blocked: false };
      rows.set(task.id, row);
      taskList.append(item);
    }
    row.heading.textContent = task.title;
    row.date.textContent = task.dueDate === null ? 'No due date' : `Due date: ${task.dueDate}`;
    if (task.dueDate !== null && row.form) {
      const restoreFocus = row.form.contains(document.activeElement);
      row.form.remove();
      row.form = null;
      if (restoreFocus) row.heading.focus();
    } else if (task.dueDate === null && !row.form) {
      const form = document.createElement('form');
      const label = document.createElement('label');
      label.htmlFor = `date-${task.id}`;
      label.textContent = `Initial due date for ${task.title}`;
      const input = document.createElement('input');
      input.id = label.htmlFor;
      input.type = 'date';
      input.required = true;
      const button = document.createElement('button');
      button.type = 'submit';
      button.textContent = 'Assign due date';
      form.append(label, input, button);
      row.form = form;
      form.addEventListener('submit', async event => {
        event.preventDefault();
        if (row.busy || row.blocked || !form.reportValidity()) return;
        const requestedDate = input.value;
        row.busy = true;
        button.disabled = true;
        feedback.textContent = '';
        let saved = false;
        try {
          const result = await api(`/api/tasks/${encodeURIComponent(task.id)}/due-date`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ dueDate: requestedDate }),
          });
          saved = true;
          // Apply the authoritative mutation response even if the subsequent refresh fails.
          render([result.task]);
          await load();
          feedback.textContent = 'Due date assigned.';
        } catch (error) {
          if (saved) {
            feedback.textContent = 'The date was saved, but refreshing failed. Reload to refresh task state.';
          } else {
            try {
              // A failed response does not prove the server failed to save. Never retry blindly.
              const current = await load();
              const actual = current.tasks.find(candidate => candidate.id === task.id);
              if (!actual) throw new Error('Task state unavailable.');
              if (actual.dueDate === requestedDate) {
                feedback.textContent = 'Due date confirmed from current task state.';
              } else if (actual.dueDate === null) {
                feedback.textContent = `${error.message} The task is still undated. You can try again.`;
              } else {
                feedback.textContent = `Current saved due date: ${actual.dueDate}. The attempted date was not confirmed.`;
              }
            } catch {
              row.blocked = true;
              feedback.textContent = 'Save outcome unknown. Reload to check task state before trying again.';
            }
          }
        } finally {
          row.busy = false;
          button.disabled = row.blocked;
        }
      });
      row.item.append(form);
    }
  }
}

async function load() {
  const data = await api('/api/tasks');
  reference.textContent = `UTC test reference day: ${data.referenceDay}. This is a testing convention, not a product timezone rule.`;
  render(data.tasks);
  return data;
}
load().catch(() => { feedback.textContent = 'Tasks could not be loaded. Reload to try again.'; });
