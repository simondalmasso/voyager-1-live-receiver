import { cp,mkdir,rm,writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
await rm('dist',{recursive:true,force:true});await mkdir('dist/data/fixtures',{recursive:true});
await cp('index.html','dist/index.html');
for(const f of ['styles.css','app.js','scene.js','signal.js','data.js'])await cp(`src/${f}`,`dist/${f}`);
await cp('shared/contracts.js','dist/contracts.js');
await cp('data/fixtures/recorded-authentic-manifest.json','dist/data/fixtures/recorded-authentic-manifest.json');
const files=['index.html','styles.css','app.js','scene.js','signal.js','data.js','contracts.js'];const manifest={schemaVersion:1,generatedAt:new Date().toISOString(),files:{}};
for(const f of files){const b=await readFile(`dist/${f}`);manifest.files[f]={bytes:b.length,sha256:createHash('sha256').update(b).digest('hex')}}
await writeFile('dist/build-manifest.json',JSON.stringify(manifest,null,2)+'\n');console.log(JSON.stringify(manifest,null,2));
