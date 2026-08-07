const CACHE='voyager-link-shell-v1';
const SHELL=['/','/styles.css','/app.js','/scene.js','/signal.js','/data.js','/contracts.js','/manifest.webmanifest','/icon.svg','/assets/voyager-probe-a.glb','/assets/voyager-probe-a.provenance.json'];
self.addEventListener('install',event=>event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(SHELL)).then(()=>self.skipWaiting())));
self.addEventListener('activate',event=>event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',event=>{
  if(event.request.method!=='GET')return;
  const url=new URL(event.request.url);
  if(url.pathname.startsWith('/api/')){event.respondWith(fetch(event.request).catch(()=>new Response(JSON.stringify({schemaVersion:1,error:{code:'OFFLINE',message:'Live/mission API unavailable offline'},generatedAt:new Date().toISOString()}),{status:503,headers:{'content-type':'application/json','cache-control':'no-store'}})));return;}
  event.respondWith(fetch(event.request).then(response=>{if(response.ok&&url.origin===location.origin){const copy=response.clone();caches.open(CACHE).then(cache=>cache.put(event.request,copy));}return response}).catch(()=>caches.match(event.request).then(hit=>hit||caches.match('/'))));
});
