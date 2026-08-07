import { cp,mkdir,rm,writeFile,readFile,readdir } from 'node:fs/promises';
import { createHash } from 'node:crypto';
await rm('dist',{recursive:true,force:true});
for(const dir of ['dist/data/fixtures','dist/assets','dist/vendor/loaders','dist/vendor/utils','dist/vendor/draco'])await mkdir(dir,{recursive:true});
await cp('index.html','dist/index.html');
for(const f of ['styles.css','order010.css','app.js','scene.js','signal.js','data.js','audio.js'])await cp(`src/${f}`,`dist/${f}`);
await cp('shared/contracts.js','dist/contracts.js');
await cp('data/fixtures/recorded-authentic-manifest.json','dist/data/fixtures/recorded-authentic-manifest.json');
for(const f of ['manifest.webmanifest','icon.svg','sw.js'])await cp(f,`dist/${f}`);
await cp('assets/voyager-probe-a.glb','dist/assets/voyager-probe-a.glb');
await cp('assets/voyager-probe-a.provenance.json','dist/assets/voyager-probe-a.provenance.json');
await cp('node_modules/three/build/three.module.js','dist/vendor/three.module.js');
await cp('node_modules/three/examples/jsm/loaders/GLTFLoader.js','dist/vendor/loaders/GLTFLoader.js');
await cp('node_modules/three/examples/jsm/loaders/DRACOLoader.js','dist/vendor/loaders/DRACOLoader.js');
await cp('node_modules/three/examples/jsm/utils/BufferGeometryUtils.js','dist/vendor/utils/BufferGeometryUtils.js');
await cp('node_modules/three/examples/jsm/libs/draco','dist/vendor/draco',{recursive:true});
for(const f of ['dist/vendor/loaders/GLTFLoader.js','dist/vendor/loaders/DRACOLoader.js','dist/vendor/utils/BufferGeometryUtils.js']){const text=await readFile(f,'utf8');await writeFile(f,text.replaceAll("from 'three'","from '../three.module.js'"))}
async function walk(dir,prefix=''){const out=[];for(const entry of await readdir(dir,{withFileTypes:true})){const rel=prefix?`${prefix}/${entry.name}`:entry.name;if(entry.isDirectory())out.push(...await walk(`${dir}/${entry.name}`,rel));else out.push(rel)}return out}
const files=(await walk('dist')).filter(f=>f!=='build-manifest.json').sort();const manifest={schemaVersion:1,generatedAt:new Date().toISOString(),files:{},totals:{bytes:0}};
for(const f of files){const b=await readFile(`dist/${f}`);const sha256=createHash('sha256').update(b).digest('hex');manifest.files[f]={bytes:b.length,sha256};manifest.totals.bytes+=b.length}
await writeFile('dist/build-manifest.json',JSON.stringify(manifest,null,2)+'\n');console.log(JSON.stringify({files:files.length,totalBytes:manifest.totals.bytes,model:manifest.files['assets/voyager-probe-a.glb'],three:manifest.files['vendor/three.module.js']},null,2));
