import { spawnSync } from 'node:child_process';
import { readFileSync, existsSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { resolve, join } from 'node:path';
import assert from 'node:assert/strict';

const root = fileURLToPath(new URL('../', import.meta.url));
process.chdir(root);
function run(args) {
  const result = spawnSync(process.execPath, args, { stdio: 'inherit', timeout: 45000 });
  if (result.error) throw result.error;
  if (result.status !== 0) process.exit(result.status ?? 1);
}
const category = process.argv[2];
if (category === 'unit') {
  run(['--test', 'test/unit.test.mjs']);
} else if (category === 'build') {
  const files = [];
  function scan(dir) {
    for (const entry of readdirSync(join(root, dir), { withFileTypes: true })) {
      const path = join(dir, entry.name);
      if (entry.isDirectory()) scan(path);
      else if (/\.(?:mjs|js)$/.test(path)) files.push(path);
    }
  }
  for (const dir of ['src', 'public', 'scripts', 'test']) scan(dir);
  for (const file of files.sort()) {
    run(['--check', file]);
    const text = readFileSync(file, 'utf8');
    for (const match of text.matchAll(/(?:from\s+|import\s*)['"](\.[^'"]+)['"]/g)) {
      assert.ok(existsSync(resolve(root, file, '..', match[1])), `Missing local import: ${file}: ${match[1]}`);
    }
  }
  const html = readFileSync('public/index.html', 'utf8');
  for (const asset of ['/app.js', '/styles.css']) {
    assert.ok(html.includes(`"${asset}"`), `Missing declared asset reference ${asset}`);
    assert.ok(existsSync(join(root, 'public', asset.slice(1))));
  }
  const pkg = JSON.parse(readFileSync('package.json', 'utf8'));
  assert.equal(pkg.type, 'module');
  assert.equal(pkg.scripts.start, 'node src/server.mjs');
  assert.equal(pkg.scripts.test, 'node scripts/check.mjs unit');
  assert.equal(pkg.scripts.build, 'node scripts/check.mjs build');
  assert.equal(Object.keys(pkg.dependencies ?? {}).length, 0);
  assert.equal(Object.keys(pkg.devDependencies ?? {}).length, 0);
  console.log(`Build validation passed: ${files.length} JS/MJS files; static assets, local imports and dependency-free package scripts checked. No HTTP/browser test was run.`);
} else {
  console.error('Supported Engineering checks: unit, build');
  process.exitCode = 1;
}
