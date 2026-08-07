import baseWorker,{state,hubSnapshot,SECURITY} from './index.js';
import {stationPhysics,observationWindow,labCapabilities,pipelineTelemetry,canonicalEvidenceStatus} from './lab.js';
import {fetchHorizonsObserverSeries} from './horizons.js';
const headers={'content-type':'application/json; charset=utf-8','cache-control':'no-store',...SECURITY};
const json=(value,status=200)=>new Response(JSON.stringify(value),{status,headers});
const finite=v=>Number.isFinite(Number(v))?Number(v):null;
export {ReceiverHub} from './index.js';
export default {async fetch(request,env,ctx){
  const url=new URL(request.url),p=url.pathname;
  try{
    if(request.method==='GET'&&p==='/api/v2/lab/capabilities')return json(labCapabilities());
    if(request.method==='GET'&&p==='/api/v2/lab/pipeline')return json(pipelineTelemetry(await hubSnapshot(env)));
    if(request.method==='GET'&&p==='/api/v2/lab/evidence')return json(canonicalEvidenceStatus(await hubSnapshot(env)));
    if(request.method==='GET'&&p==='/api/v2/station/physics')return json(stationPhysics(Object.fromEntries(url.searchParams.entries())));
    if(request.method==='GET'&&p==='/api/v2/observation-window'){
      const q=Object.fromEntries(url.searchParams.entries()),lat=finite(q.lat),lon=finite(q.lon),elevation=finite(q.elevation)||0,duration=Math.min(720,Math.max(15,finite(q.durationMinutes)||180)),step=Math.min(60,Math.max(1,finite(q.stepMinutes)||15));
      if(lat===null||lon===null)throw new Error('INVALID_OBSERVER');const startAt=new Date(),stopAt=new Date(startAt.getTime()+duration*60_000);let series=null,error=null;
      try{series=await fetchHorizonsObserverSeries({startAt,stopAt,stepMinutes:step,lat,lon,elevation})}catch(e){error=e}
      return json(observationWindow(await state(),q,series,error));
    }
  }catch{return json({schemaVersion:2,error:{code:'LAB_REQUEST_INVALID',message:'Order 011 laboratory request rejected'},generatedAt:new Date().toISOString()},400)}
  return baseWorker.fetch(request,env,ctx);
}};
