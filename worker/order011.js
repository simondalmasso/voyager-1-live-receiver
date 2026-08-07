import baseWorker,{state,hubSnapshot,SECURITY} from './index.js';
import {stationPhysics,observationWindow,labCapabilities,pipelineTelemetry} from './lab.js';
const headers={'content-type':'application/json; charset=utf-8','cache-control':'no-store',...SECURITY};
const json=(value,status=200)=>new Response(JSON.stringify(value),{status,headers});
export {ReceiverHub} from './index.js';
export default {async fetch(request,env,ctx){
  const url=new URL(request.url),p=url.pathname;
  try{
    if(request.method==='GET'&&p==='/api/v2/lab/capabilities')return json(labCapabilities());
    if(request.method==='GET'&&p==='/api/v2/lab/pipeline')return json(pipelineTelemetry(await hubSnapshot(env)));
    if(request.method==='GET'&&p==='/api/v2/station/physics')return json(stationPhysics(Object.fromEntries(url.searchParams.entries())));
    if(request.method==='GET'&&p==='/api/v2/observation-window')return json(observationWindow(await state(),Object.fromEntries(url.searchParams.entries())));
  }catch{return json({schemaVersion:2,error:{code:'LAB_REQUEST_INVALID',message:'Order 011 laboratory request rejected'},generatedAt:new Date().toISOString()},400)}
  return baseWorker.fetch(request,env,ctx);
}};
