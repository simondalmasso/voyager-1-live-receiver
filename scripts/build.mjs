import {cp,mkdir,readFile,rm,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
await rm('dist',{recursive:true,force:true});await mkdir('dist/data/fixtures',{recursive:true});
await cp('index.html','dist/index.html');
for(const file of ['styles.css','app.js','scene.js','signal.js','data.js'])await cp(`src/${file}`,`dist/${file}`);
await cp('shared/contracts.js','dist/contracts.js');
for(const file of ['trajectory-v2.json','spice-kernels.json','horizons-reference.json','stations.v1.json'])await cp(`data/${file}`,`dist/data/${file}`);
await cp('data/fixtures/recorded-authentic-manifest.json','dist/data/fixtures/recorded-authentic-manifest.json');
const files=['index.html','styles.css','app.js','scene.js','signal.js','data.js','contracts.js','data/trajectory-v2.json','data/spice-kernels.json','data/horizons-reference.json','data/stations.v1.json'];const manifest={schemaVersion:2,files:{}};
for(const file of files){const bytes=await readFile(`dist/${file}`);manifest.files[file]={bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')};}
await mkdir('artifacts',{recursive:true});await writeFile('dist/build-manifest.json',JSON.stringify(manifest,null,2)+'\n');await writeFile('artifacts/build-manifest.json',JSON.stringify(manifest,null,2)+'\n');console.log(JSON.stringify(manifest,null,2));
