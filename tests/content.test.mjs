import test from 'node:test';import assert from 'node:assert/strict';import {readFile} from 'node:fs/promises';
test('sensitive claims have truth context',async()=>{for(const p of ['README.md','index.html','src/app.js']){const s=await readFile(p,'utf8');assert.ok(!/NASA approved|official telemetry|connected to the DSN/i.test(s),`${p} has forbidden claim`)}});
test('deploy is not present in automatic workflows',async()=>{for(const p of ['.github/workflows/ci.yml','.github/workflows/listener-ci.yml','.github/workflows/security.yml','.github/workflows/data-verify.yml']){const s=await readFile(p,'utf8');assert.ok(!/wrangler\s+deploy(?!\s+--dry-run)/.test(s),`${p} contains deploy`)}});

test('legacy signal mode defaults to receiver hub and synthetic candidates cannot claim verification',async()=>{const {readFile}=await import('node:fs/promises');const [signal,app]=await Promise.all([readFile('src/signal.js','utf8'),readFile('src/app.js','utf8')]);assert.match(signal,/start\(mode='hub'\)/);assert.match(signal,/state:'CANDIDATE'/);assert.doesNotMatch(signal,/sourceMode:'SYNTHETIC_TEST'[\s\S]{0,500}state:'VERIFIED_CARRIER'/);assert.match(app,/signalView\?\.start\('hub'\)/);});
test('OS Voyager makes public DSN status, archived PWS science and disabled uplink explicit',async()=>{const {readFile}=await import('node:fs/promises');const s=await readFile('src/os-voyager.js','utf8');assert.match(s,/NASA\/JPL DSN Now/);assert.match(s,/PWS ARCHIVED SCIENCE/);assert.match(s,/DISABLED — NO AUTHORIZED CHANNEL/);assert.match(s,/NO RF TRANSMITTED/);assert.match(s,/Processed in this browser only/);});

test('HTML and Worker CSP permit local Draco workers and WebAssembly decoding',async()=>{
  const [html,worker]=await Promise.all([readFile('index.html','utf8'),readFile('worker/index.js','utf8')]);
  const meta=html.match(/http-equiv="Content-Security-Policy" content="([^"]+)"/)?.[1];
  const header=worker.match(/^const CSP="([^"]+)";$/m)?.[1];
  assert.ok(meta,'HTML CSP meta policy exists');
  assert.ok(header,'Worker CSP response policy exists');
  assert.equal(meta,header,'HTML and response CSP policies must stay identical');
  assert.match(meta,/(?:^|;\s*)worker-src 'self' blob:/);
  assert.match(meta,/script-src[^;]*'wasm-unsafe-eval'/);
});
