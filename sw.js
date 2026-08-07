const CACHE='voyager-link-shell-v2';
const SHELL=['/','/styles.css','/order010.css','/app.js','/scene.js','/signal.js','/data.js','/audio.js','/contracts.js','/manifest.webmanifest','/icon.svg','/assets/voyager-probe-a.glb','/assets/voyager-probe-a.provenance.json','/vendor/three.module.js','/vendor/loaders/GLTFLoader.js','/vendor/loaders/DRACOLoader.js','/vendor/utils/BufferGeometryUtils.js','/vendor/draco/draco_decoder.js','/vendor/draco/draco_wasm_wrapper.js','/vendor/draco/draco_decoder.wasm'];
self.addEventListener('install',event=>event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(SHELL)).then(()=>self.skipWaiting())));
self.addEventListener('activate',event=>event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',event=>{
  if(event.request.method!=='GET')return;
  const url=new URL(event.request.url);
  if(url.pathname.startsWith('/api/')){event.respondWith(fetch(event.request).catch(()=>new Response(JSON.stringify({schemaVersion:1,error:{code:'OFFLINE',message:'Live/mission API unavailable offline; cached content is not current state.'},generatedAt:new Date().toISOString()}),{status:503,headers:{'content-type':'application/json','cache-control':'no-store'}})));return;}
  if(url.origin!==location.origin)return;
  event.respondWith(fetch(event.request).then(response=>{if(response.ok){const copy=response.clone();caches.open(CACHE).then(cache=>cache.put(event.request,copy));}return response}).catch(()=>caches.match(event.request).then(hit=>hit||caches.match('/'))));
});
