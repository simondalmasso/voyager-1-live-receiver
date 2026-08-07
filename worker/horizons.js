import { makeVoyagerState } from '../shared/contracts.js';
const ENDPOINT='https://ssd.jpl.nasa.gov/api/horizons.api';
export function buildHorizonsUrl(at=new Date()){
  const stop=new Date(at.getTime()+60_000);const f=d=>d.toISOString().replace('T',' ').replace('.000Z','');
  const q=new URLSearchParams({format:'text',COMMAND:"'-31'",OBJ_DATA:'NO',MAKE_EPHEM:'YES',EPHEM_TYPE:'VECTORS',CENTER:"'500@399'",START_TIME:`'${f(at)}'`,STOP_TIME:`'${f(stop)}'`,STEP_SIZE:"'1 m'",REF_SYSTEM:'ICRF',REF_PLANE:'FRAME',OUT_UNITS:'KM-S',VEC_LABELS:'NO',VEC_CORR:'NONE',CSV_FORMAT:'YES'});
  return `${ENDPOINT}?${q}`;
}
export function parseHorizonsVectors(text,fetchedAt=new Date().toISOString()){
  if(typeof text!=='string'||text.length>2_000_000)throw new Error('HORIZONS_SIZE');
  const start=text.indexOf('$$SOE'),end=text.indexOf('$$EOE');if(start<0||end<start)throw new Error('HORIZONS_MARKERS');
  const lines=text.slice(start+5,end).split(/\r?\n/).map(x=>x.trim()).filter(Boolean);
  for(const line of lines){
    const fields=line.split(',').map(x=>x.trim()),dateField=fields.find(x=>/A\.D\.|\d{4}-[A-Z][a-z]{2}-\d{2}/.test(x)),numbers=fields.map(Number);
    const first=numbers.findIndex((v,i)=>i>=2&&Number.isFinite(v)&&numbers.slice(i,i+6).every(Number.isFinite));if(first<0)continue;
    const pos=numbers.slice(first,first+3),vel=numbers.slice(first+3,first+6);if(Math.hypot(...pos)<1e8||Math.hypot(...pos)>1e12||Math.hypot(...vel)>100)continue;
    const observed=parseHorizonsDate(dateField)||new Date().toISOString();
    return makeVoyagerState({observedAt:observed,positionKm:pos,velocityKmS:vel,source:{truthClass:'DERIVED_GEOMETRY',sourceId:'jpl-horizons-vectors',sourceUrl:ENDPOINT,upstreamAuthority:'JPL Horizons',observedAt:observed,fetchedAt,transform:'Official JPL Horizons ICRF geocentric VECTORS; distance/light-time/range-rate/RA/Dec derived locally.'}});
  }
  throw new Error('HORIZONS_VECTOR_NOT_FOUND');
}
function parseHorizonsDate(value=''){const m=value.match(/A\.D\.\s*(\d{4})-([A-Z][a-z]{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})/);if(!m)return null;const month=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'].indexOf(m[2]);if(month<0)return null;return new Date(Date.UTC(+m[1],month,+m[3],+m[4],+m[5],+m[6])).toISOString()}
