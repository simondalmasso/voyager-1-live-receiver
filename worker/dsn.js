const URL='https://eyes.nasa.gov/dsn/data/dsn.xml';
export function parseDsnXml(xml,fetchedAt=new Date().toISOString()){
  if(typeof xml!=='string'||xml.length>2_000_000)throw new Error('DSN_SIZE');if(/<!DOCTYPE|<!ENTITY/i.test(xml))throw new Error('DSN_UNSAFE_XML');
  const dishBlocks=[...xml.matchAll(/<dish\b[^>]*>([\s\S]*?)<\/dish>/gi)].map(m=>m[0]),stations=[];
  for(const block of dishBlocks){const target=attrOrTag(block,'target')||attrOrTag(block,'spacecraft')||'';if(!/voyager\s*1|voyager-?1|vgr\s*1/i.test(target))continue;stations.push({dish:attrOrTag(block,'name')||attrOrTag(block,'dish')||'Unknown DSN dish',complex:attrOrTag(block,'complex')||'Unknown complex',target:'Voyager 1',band:attrOrTag(block,'band')||null,dataRateBps:num(attrOrTag(block,'dataRate')||attrOrTag(block,'datarate')),powerDbm:num(attrOrTag(block,'power'))})}
  return {schemaVersion:1,generatedAt:new Date().toISOString(),available:stations.length>0,stations,provenance:{truthClass:stations.length?'DSN_LIVE_PUBLIC_STATUS':'UNAVAILABLE',sourceId:'nasa-dsn-now-public-feed',sourceUrl:URL,fetchedAt,fallbackReason:stations.length?undefined:'Feed contained no explicit Voyager 1 activity.'}};
}
function attrOrTag(block,name){const attr=block.match(new RegExp(`${name}=["']([^"']+)["']`,'i'));if(attr)return clean(attr[1]);const tag=block.match(new RegExp(`<${name}[^>]*>([^<]+)</${name}>`,'i'));return tag?clean(tag[1]):null}
function clean(v){return String(v).replace(/[\r\n\t]+/g,' ').replace(/\s+/g,' ').trim().slice(0,180)}
function num(v){const n=Number(v);return Number.isFinite(n)?n:null}
export {URL as DSN_URL};
