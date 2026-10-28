import http from 'node:http';
import { readFile } from 'node:fs/promises';
import { AppError, assignInitialDate, isCalendarDate } from './domain.mjs';
import { createRepository } from './repository.mjs';

const assets = new Map([
  ['/', ['../public/index.html', 'text/html; charset=utf-8']],
  ['/app.js', ['../public/app.js', 'text/javascript; charset=utf-8']],
  ['/styles.css', ['../public/styles.css', 'text/css; charset=utf-8']],
]);
const bodyLimit = 4096;
const csp = "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'";

function send(response, status, value, type = 'application/json; charset=utf-8') {
  response.writeHead(status, {
    'Content-Type': type,
    'Content-Security-Policy': csp,
    'X-Content-Type-Options': 'nosniff',
    'Referrer-Policy': 'no-referrer',
    'Cache-Control': 'no-store',
  });
  response.end(type.startsWith('application/json') ? JSON.stringify(value) : value);
}

async function jsonBody(request) {
  if (!/^application\/json(?:\s*;\s*charset=utf-8)?$/i.test(request.headers['content-type'] ?? '')) {
    throw new AppError('CONTENT_TYPE', 'Use application/json.', 415);
  }
  const length = request.headers['content-length'];
  if (length !== undefined && (!/^\d+$/.test(length) || Number(length) > bodyLimit)) {
    throw new AppError('BODY_TOO_LARGE', 'Request body exceeds the demonstrator limit.', 413);
  }
  const chunks = [];
  await new Promise((resolve, reject) => {
    let size = 0;
    function cleanup() {
      request.off('data', onData);
      request.off('end', onEnd);
      request.off('aborted', onAborted);
      request.off('error', onError);
    }
    function onData(chunk) {
      size += chunk.length;
      if (size > bodyLimit) {
        cleanup();
        // Drain without buffering; destroying the input would also destroy the error response.
        request.resume();
        reject(new AppError('BODY_TOO_LARGE', 'Request body exceeds the demonstrator limit.', 413));
      } else chunks.push(chunk);
    }
    function onEnd() { cleanup(); resolve(); }
    function onAborted() { cleanup(); reject(new AppError('INCOMPLETE_BODY', 'Request was interrupted.')); }
    function onError() { cleanup(); reject(new AppError('INCOMPLETE_BODY', 'Request could not be read.')); }
    request.on('data', onData);
    request.on('end', onEnd);
    request.on('aborted', onAborted);
    request.on('error', onError);
  });
  let body;
  try {
    const text = new TextDecoder('utf-8', { fatal: true }).decode(Buffer.concat(chunks));
    body = JSON.parse(text);
  } catch {
    throw new AppError('INVALID_JSON', 'Supply a valid UTF-8 JSON object.');
  }
  if (!body || Array.isArray(body) || typeof body !== 'object'
      || Object.keys(body).length !== 1 || !Object.hasOwn(body, 'dueDate')) {
    throw new AppError('INVALID_BODY', 'Supply exactly the dueDate field.');
  }
  return body;
}

// Construct without listening so QA can start isolated servers with fixed test data/time.
export function createApp({ repository = createRepository(), referenceDay = () => new Date().toISOString().slice(0, 10) } = {}) {
  const server = http.createServer(async (request, response) => {
    try {
      const host = `127.0.0.1:${server.address().port}`;
      if (request.headers.host !== host) throw new AppError('INVALID_HOST', 'Use the local application URL.', 403);
      const path = request.url;
      if (request.method === 'GET' && path === '/api/tasks') {
        const day = referenceDay();
        if (!isCalendarDate(day)) throw new Error('Invalid reference day.');
        send(response, 200, { tasks: repository.list(), referenceDay: day });
      } else if (request.method === 'GET' && assets.has(path)) {
        const [file, type] = assets.get(path);
        send(response, 200, await readFile(new URL(file, import.meta.url)), type);
      } else if (request.method === 'POST' && /^\/api\/tasks\/[a-zA-Z0-9_-]{1,80}\/due-date$/.test(path)) {
        const origin = request.headers.origin;
        if (origin !== undefined && origin !== `http://${host}`) {
          throw new AppError('FOREIGN_ORIGIN', 'Only same-origin browser mutations are supported.', 403);
        }
        const body = await jsonBody(request);
        const id = path.split('/')[3];
        const task = assignInitialDate(repository, id, body.dueDate, referenceDay());
        send(response, 200, { task });
      } else {
        throw new AppError('NOT_FOUND', 'Route not found.', 404);
      }
    } catch (error) {
      const known = error instanceof AppError;
      if (!response.headersSent && !response.destroyed) {
        send(response, known ? error.status : 500, { error: {
          code: known ? error.code : 'INTERNAL_ERROR',
          message: known ? error.message : 'The application could not complete this request.',
        } });
      }
    }
  });
  server.requestTimeout = 10000;
  server.headersTimeout = 10000;
  server.keepAliveTimeout = 1000;
  server.maxHeadersCount = 50;
  return server;
}
