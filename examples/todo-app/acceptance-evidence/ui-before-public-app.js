const taskList = document.querySelector('#tasks');
const feedback = document.querySelector('#feedback');
const reference = document.querySelector('#reference');

async function api(path, options) {
  const response = await fetch(path, options);
  const body = await response.json();
  if (!response.ok) throw new Error(body.error?.message ?? 'Request failed.');
  return body;
}

function render(tasks) {
  taskList.replaceChildren();
  for (const task of tasks) {
    const item = document.createElement('li');
    const heading = document.createElement('h2');
    heading.textContent = task.title;
    const date = document.createElement('p');
    date.textContent = task.dueDate === null ? 'No due date' : `Due date: ${task.dueDate}`;
    item.append(heading, date);
    if (task.dueDate === null) {
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
      form.addEventListener('submit', async event => {
        event.preventDefault();
        if (!form.reportValidity()) return;
        button.disabled = true;
        feedback.textContent = '';
        let saved = false;
        try {
          await api(`/api/tasks/${encodeURIComponent(task.id)}/due-date`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ dueDate: input.value }),
          });
          saved = true;
          await load();
          feedback.textContent = 'Due date assigned.';
        } catch (error) {
          feedback.textContent = saved
            ? 'The date was saved, but refreshing failed. Reload to see the saved state.'
            : error.message;
        } finally {
          button.disabled = false;
        }
      });
      item.append(form);
    }
    taskList.append(item);
  }
}

async function load() {
  const data = await api('/api/tasks');
  reference.textContent = `UTC test reference day: ${data.referenceDay}. This is a testing convention, not a product timezone rule.`;
  render(data.tasks);
}
load().catch(() => { feedback.textContent = 'Tasks could not be loaded. Reload to try again.'; });
