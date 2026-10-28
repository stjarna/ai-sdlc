import { createApp } from '../src/http.mjs';
import { createRepository } from '../src/repository.mjs';
import { mkdir, writeFile, readFile } from 'node:fs/promises';
import { createHash, randomUUID } from 'node:crypto';
import { fileURLToPath } from 'node:url';

export const referenceDay = '2026-10-28';
export const dates = ['2026-12-31', '2027-01-01', '2028-02-29'];
export async function fixture(seeds) {
  const server = createApp({ repository: createRepository(seeds), referenceDay: () => referenceDay });
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  return { url: `http://127.0.0.1:${server.address().port}`,
    async close() {
      server.closeAllConnections();
      await new Promise((resolve, reject) => server.close(error => error ? reject(error) : resolve()));
    },
  };
}

// Each invocation creates new files; output never goes into fingerprinted QA source.
export async function evidenceDirectory(kind) {
  const parent = new URL('../requirements/REQ-0001-task-due-date-management/test-evidence/', import.meta.url);
  await mkdir(parent, { recursive: true });
  const dir = new URL(`qa-${kind}-${randomUUID()}/`, parent);
  await mkdir(dir, { recursive: false });
  console.log(`Node ${process.version}; QA kind ${kind}; reference day ${referenceDay} (test data only)`);
  return dir;
}
export async function reportFile(file) {
  const data = await readFile(file);
  console.log(JSON.stringify({ evidence: fileURLToPath(file), sha256: createHash('sha256').update(data).digest('hex') }));
}
export async function report(dir, name, data) {
  const file = new URL(name, dir);
  await writeFile(file, JSON.stringify(data, null, 2) + '\n', { flag: 'wx' });
  await reportFile(file);
}
