const URL='https://eyes.nasa.gov/dsn/data/dsn.xml';
const clean=v=>String(v??'').replace(/[\r\n\t]+/g,' ').replace(/\s+/g,' ').trim().slice(0,180);
function attr(attrs,name){const m=String(attrs||'').match(new RegExp('(?:^|\\s)'+name+'=["\\']([^"\\']*)["\\']','i'));return m?clean(m[1]):null}
function elements(block,name){const re=new RegExp('<'+name+'\\b([^>]*?)(?:\\/\\s*>|>([\\s\\S]*?)<\\/'+name+'\\s*>)','gi');return [...String(block||'').matchAll(re)].map(m=>({attrs:m[1]||'',text:clean(m[2]||'')}))}
function isVoyager1(value){return /^(?:voyager\s*1|voyager-?1|vgr\s*1)$/i.test(clean(value))}
function active(value){return /^(?:true|1|yes|active)$/i.test(String(value||'').trim())}
function parseSignal(el){return {active:active(attr(el.attrs,'active')),spacecraft:attr(el.attrs,'spacecraft'),spacecraftId:attr(el.attrs,'spacecraftID'),signalType:attr(el.attrs,'signalType'),band:attr(el.attrs,'band'),frequency:attr(el.attrs,'frequency'),dataRate:attr(el.attrs,'dataRate'),power:attr(el.attrs,'power')}}
function sourceTime(xml){const tag=/<timestamp\b[^>]*>([^<]+)<\/timestamp>/i.exec(xml);if(tag)return clean(tag[1]);const root=/<dsn\b([^>]*)>/i.exec(xml);return root?attr(root[1],'timestamp'):null}
function legacyField(attrs,inner,name){return attr(attrs,name)||elements(inner,name)[0]?.text||null}
export function parseDsnXml(xml,fetchedAt=new Date().toISOString()){
  if(typeof xml!=='string'||xml.length>2_000_000)throw new Error('DSN_SIZE');
  if(/<!DOCTYPE|<!ENTITY/i.test(xml))throw new Error('DSN_UNSAFE_XML');
  const dishBlocks=[...xml.matchAll(/<dish\b([^>]*?)(?:\/\s*>|>([\s\S]*?)<\/dish\s*>)/gi)];
  const stations=[];
  for(const match of dishBlocks){
    const attrs=match[1]||'',inner=match[2]||'';
    const targets=elements(inner,'target').map(el=>({name:attr(el.attrs,'name')||el.text,id:attr(el.attrs,'id'),uplegRange:attr(el.attrs,'uplegRange'),downlegRange:attr(el.attrs,'downlegRange'),roundTripLightTime:attr(el.attrs,'rtlt')}));
    const downSignals=elements(inner,'downSignal').map(parseSignal);
    const upSignals=elements(inner,'upSignal').map(parseSignal);
    const v1Targets=targets.filter(t=>isVoyager1(t.name));
    const v1Down=downSignals.filter(s=>isVoyager1(s.spacecraft));
    const v1Up=upSignals.filter(s=>isVoyager1(s.spacecraft));
    if(!v1Targets.length&&!v1Down.length&&!v1Up.length)continue;
    const selectedSignal=v1Down.find(s=>s.active)||v1Down[0]||v1Up.find(s=>s.active)||v1Up[0]||null;
    stations.push({
      dish:attr(attrs,'name')||'Unknown DSN dish',
      complex:attr(attrs,'complex'),
      target:'Voyager 1',
      activity:attr(attrs,'activity'),
      band:selectedSignal?.band||legacyField(attrs,inner,'band'),
      dataRate:selectedSignal?.dataRate||legacyField(attrs,inner,'dataRate'),
      power:selectedSignal?.power||legacyField(attrs,inner,'power'),
      downlinkActive:v1Down.some(s=>s.active),
      uplinkActive:v1Up.some(s=>s.active),
      downlinkSignals:v1Down,
      uplinkSignals:v1Up,
      targetMetadata:v1Targets[0]||null
    });
  }
  const timestamp=sourceTime(xml);
  return {schemaVersion:1,generatedAt:new Date().toISOString(),sourceTimestamp:timestamp,feedAvailable:true,available:stations.length>0,stations,provenance:{truthClass:stations.length?'DSN_LIVE_PUBLIC_STATUS':'UNAVAILABLE',sourceId:'nasa-dsn-now-public-feed',sourceUrl:URL,fetchedAt,fallbackReason:stations.length?undefined:'No explicit Voyager 1 target or signal was present in this feed snapshot; this does not establish absence of contact.'}};
}
export {URL as DSN_URL};
