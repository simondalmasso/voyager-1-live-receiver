import { cp,mkdir,rm,writeFile,readFile,readdir } from 'node:fs/promises';
import { createHash } from 'node:crypto';
await rm('dist',{recursive:true,force:true});
for(const dir of ['dist/data/fixtures','dist/assets','dist/artifacts/order013','dist/vendor/loaders','dist/vendor/utils','dist/vendor/draco'])await mkdir(dir,{recursive:true});
await cp('index.html','dist/index.html');
for(const f of ['styles.css','order010.css','order011.css','app.js','scene.js','signal.js','data.js','audio.js','order011.js','order013.css','order013-core.js','order013-scene.js','order013.js','order013-trajectory.js','os-voyager.js'])await cp(`src/${f}`,`dist/${f}`);
await cp('shared/contracts.js','dist/contracts.js');
await cp('data/fixtures/recorded-authentic-manifest.json','dist/data/fixtures/recorded-authentic-manifest.json');
await cp('data/order013-ephemeris.json','dist/data/order013-ephemeris.json');
for(const f of ['model-comparison.json','provenance.json'])await cp(`artifacts/order013/${f}`,`dist/artifacts/order013/${f}`);
for(const f of ['manifest.webmanifest','icon.svg','sw.js'])await cp(f,`dist/${f}`);
for(const f of ['voyager-probe-a.glb','voyager-probe-a.provenance.json','voyager-probe-b.glb','voyager-probe-b.provenance.json'])await cp(`assets/${f}`,`dist/assets/${f}`);
for(const f of ['three.module.js','three.core.js'])await cp(`node_modules/three/build/${f}`,`dist/vendor/${f}`);
await cp('node_modules/three/examples/jsm/loaders/GLTFLoader.js','dist/vendor/loaders/GLTFLoader.js');
await cp('node_modules/three/examples/jsm/loaders/DRACOLoader.js','dist/vendor/loaders/DRACOLoader.js');
await cp('node_modules/three/examples/jsm/utils/BufferGeometryUtils.js','dist/vendor/utils/BufferGeometryUtils.js');
for(const f of ['draco_wasm_wrapper.js','draco_decoder.wasm','draco_decoder.js'])await cp(`node_modules/three/examples/jsm/libs/draco/${f}`,`dist/vendor/draco/${f}`);
for(const f of ['dist/vendor/loaders/GLTFLoader.js','dist/vendor/loaders/DRACOLoader.js','dist/vendor/utils/BufferGeometryUtils.js']){const text=await readFile(f,'utf8');await writeFile(f,text.replaceAll("from 'three'","from '../three.module.js'"))}
async function walk(dir,prefix=''){const out=[];for(const entry of await readdir(dir,{withFileTypes:true})){const rel=prefix?`${prefix}/${entry.name}`:entry.name;if(entry.isDirectory())out.push(...await walk(`${dir}/${entry.name}`,rel));else out.push(rel)}return out}
const files=(await walk('dist')).filter(f=>f!=='build-manifest.json').sort();const manifest={schemaVersion:2,generatedAt:new Date().toISOString(),files:{},totals:{bytes:0}};
for(const f of files){const b=await readFile(`dist/${f}`);const sha256=createHash('sha256').update(b).digest('hex');manifest.files[f]={bytes:b.length,sha256};manifest.totals.bytes+=b.length}
await writeFile('dist/build-manifest.json',JSON.stringify(manifest,null,2)+'\n');console.log(JSON.stringify({files:files.length,totalBytes:manifest.totals.bytes,heroHigh:manifest.files['assets/voyager-probe-b.glb'],heroLow:manifest.files['assets/voyager-probe-a.glb'],order013:{css:manifest.files['order013.css'],js:manifest.files['order013.js'],scene:manifest.files['order013-scene.js'],trajectory:manifest.files['order013-trajectory.js'],ephemeris:manifest.files['data/order013-ephemeris.json'],comparison:manifest.files['artifacts/order013/model-comparison.json'],provenance:manifest.files['artifacts/order013/provenance.json']},runtimeDraco:['vendor/draco/draco_wasm_wrapper.js','vendor/draco/draco_decoder.wasm','vendor/draco/draco_decoder.js'].map(f=>manifest.files[f]),order011:{css:manifest.files['order011.css'],js:manifest.files['order011.js']},three:manifest.files['vendor/three.module.js']},null,2));
