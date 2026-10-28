import { createApp } from './http.mjs';
const server = createApp();
server.on('error', error => {
  console.error(`Application could not start: ${error.code ?? 'unknown error'}`);
  process.exitCode = 1;
});
server.listen(0, '127.0.0.1', () => {
  console.log(`Task due-date demonstrator: http://127.0.0.1:${server.address().port}`);
  console.log('In-memory seeded tasks only. Data resets on restart.');
});
for (const signal of ['SIGINT', 'SIGTERM']) {
  process.on(signal, () => server.close(() => { process.exitCode = 0; }));
}
