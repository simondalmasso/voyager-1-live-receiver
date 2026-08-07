import {mkdir,writeFile} from 'node:fs/promises';
await mkdir('artifacts',{recursive:true});
const inventory={
  schemaVersion:1,
  generatedAt:new Date().toISOString(),
  runtimeDependencies:[{name:'three',version:'0.180.0',license:'MIT',role:'WebGL scene, GLTF loader and Draco integration'}],
  ciOnly:[{name:'wrangler',version:'4.114.0',license:'MIT OR Apache-2.0'},{name:'@playwright/test',version:'1.62.0',license:'Apache-2.0'},{name:'@axe-core/playwright',version:'4.12.1',license:'MPL-2.0'}],
  assets:[{name:'Voyager Probe (A)',origin:'NASA 3D Resources',credit:'NASA',usagePolicy:'https://www.nasa.gov/nasa-brand-center/images-and-media/',sha256:'7cf8eefb5a0fca9e4e1b0d1e51c37433124169183e5dbfd2d8034af902311821',truth:'PRIMARY_VISUAL_MODEL'},{name:'Procedural spacecraft mesh',origin:'Project code',license:'MIT',truth:'FALLBACK_ONLY'}],
  datasets:[{name:'NAIF Voyager SPICE trajectory',origin:'NASA/JPL NAIF',redistribution:'normalized derived coordinates plus kernel hashes; kernels not bundled'},{name:'Embedded mission fallback seed',origin:'Order 010 sourced geometry',redistribution:'small normalized metadata only'}]
};
await writeFile('artifacts/source-license-inventory.json',JSON.stringify(inventory,null,2)+'\n');
console.log('inventory written');
