import {makeVoyagerState,publicNoSource,validateBrowserSnapshot} from '/contracts.js';
const FALLBACK=makeVoyagerState({
  observedAt:'2026-08-05T00:00:00.000Z',
  positionKm:[-1.955e10,-1.50e10,7.72e9],
  velocityKmS:[-12.4,-10.2,5.1],
  source:{truthState:'STALE',sourceId:'embedded-aud-002-seed',sourceUrl:'https://github.com/simonkey888/voyager-1-live-receiver/issues/9',observedAt:'2026-08-05T00:00:00.000Z',fetchedAt:'2026-08-05T00:00:00.000Z',fallbackReason:'Worker upstream unavailable; cached mission geometry only.'}
});
async function json(path,signal){const response=await fetch(path,{signal,headers:{accept:'application/json'}});if(!response.ok)throw new Error(`${path} returned ${response.status}`);return response.json();}
export async function loadMissionData(signal){
  const [state,dsn,mission,trajectory,pws,receiver]=await Promise.allSettled([
    json('/api/v1/voyager/state',signal),json('/api/v1/dsn/voyager-1',signal),json('/api/v1/mission/status',signal),json('/api/v1/voyager/trajectory',signal),json('/api/v1/science/pws/catalog',signal),json('/api/v1/receiver/live',signal)
  ]);
  return {
    state:state.status==='fulfilled'?state.value:FALLBACK,
    dsn:dsn.status==='fulfilled'?dsn.value:{available:false,provenance:{truthState:'NO_SOURCE'},reason:String(dsn.reason)},
    mission:mission.status==='fulfilled'?mission.value:null,
    trajectory:trajectory.status==='fulfilled'?trajectory.value:null,
    pws:pws.status==='fulfilled'?pws.value:null,
    receiver:receiver.status==='fulfilled'?validateBrowserSnapshot(receiver.value):publicNoSource('NO VERIFIED LIVE SOURCE'),
    degraded:state.status!=='fulfilled'
  };
}
export {FALLBACK};
