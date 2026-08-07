export const SCHEMA_VERSION = 1;
export const TRUTH_CLASSES = Object.freeze([
  'MISSION_STATUS_OFFICIAL_SNAPSHOT','DSN_LIVE_PUBLIC_STATUS','PWS_ARCHIVED_SCIENCE',
  'DERIVED_GEOMETRY','TELESCOPE_LIVE_VERIFIED','RECORDED_AUTHENTIC_VERIFIED',
  'SYNTHETIC_TEST','UNVERIFIED_SOURCE','STALE','UNAVAILABLE'
]);
export const SIGNAL_STATES = Object.freeze(['NO_SOURCE','SEARCHING','CANDIDATE','VERIFIED_CARRIER','LOST','STALE','ERROR']);
export const SOURCE_MODES = Object.freeze(['TELESCOPE_LIVE_VERIFIED','RECORDED_AUTHENTIC_VERIFIED','SYNTHETIC_TEST','UNVERIFIED_SOURCE','NO_SOURCE','STALE','LOST']);
export const C_KM_S = 299_792.458;
export const AU_KM = 149_597_870.7;
export const WGS84_A_KM = 6378.137;
export const WGS84_E2 = 6.69437999014e-3;

export function assertFinite(value,name){if(!Number.isFinite(value))throw new TypeError(`${name} must be finite`);return value}
export function isoUtc(value,name='timestamp'){const date=new Date(value);if(Number.isNaN(date.valueOf()))throw new TypeError(`${name} must be UTC ISO-8601`);return date.toISOString()}
export function provenance(input){if(!input||!TRUTH_CLASSES.includes(input.truthClass))throw new TypeError('Invalid truthClass');if(!input.sourceId||typeof input.sourceId!=='string')throw new TypeError('sourceId required');return {...input,fetchedAt:isoUtc(input.fetchedAt??new Date().toISOString(),'fetchedAt')}}
export function lightTime(distanceKm){assertFinite(distanceKm,'distanceKm');if(distanceKm<0)throw new RangeError('distanceKm cannot be negative');const oneWaySeconds=distanceKm/C_KM_S;return {oneWaySeconds,roundTripSeconds:oneWaySeconds*2}}
export function vectorMagnitude([x,y,z]){return Math.hypot(assertFinite(x,'x'),assertFinite(y,'y'),assertFinite(z,'z'))}
export function normalizeVector(vector){const mag=vectorMagnitude(vector);if(mag===0)throw new RangeError('Cannot normalize zero vector');return vector.map(v=>v/mag)}
export function radialVelocity(positionKm,velocityKmS){const direction=normalizeVector(positionKm);return direction[0]*velocityKmS[0]+direction[1]*velocityKmS[1]+direction[2]*velocityKmS[2]}
export function raDecFromVector(positionKm){const [x,y,z]=positionKm,rangeKm=vectorMagnitude(positionKm);let raRad=Math.atan2(y,x);if(raRad<0)raRad+=Math.PI*2;return {raDeg:raRad*180/Math.PI,decDeg:Math.asin(z/rangeKm)*180/Math.PI,rangeKm}}
export function gmstDegrees(at){const jd=new Date(at).getTime()/86400000+2440587.5;const t=(jd-2451545.0)/36525;let v=280.46061837+360.98564736629*(jd-2451545.0)+0.000387933*t*t-t*t*t/38710000;return ((v%360)+360)%360}
export function topocentricFromGeocentric(positionKm,{lat,lon,elevation=0,at=new Date().toISOString()}){
  assertFinite(lat,'lat');assertFinite(lon,'lon');assertFinite(elevation,'elevation');if(lat<-90||lat>90||lon<-180||lon>180)throw new RangeError('observer coordinates outside range');
  const phi=lat*Math.PI/180,lambda=lon*Math.PI/180,h=elevation/1000,s=Math.sin(phi),c=Math.cos(phi),n=WGS84_A_KM/Math.sqrt(1-WGS84_E2*s*s);
  const ecef=[(n+h)*c*Math.cos(lambda),(n+h)*c*Math.sin(lambda),(n*(1-WGS84_E2)+h)*s];
  const theta=gmstDegrees(at)*Math.PI/180,observerEci=[Math.cos(theta)*ecef[0]-Math.sin(theta)*ecef[1],Math.sin(theta)*ecef[0]+Math.cos(theta)*ecef[1],ecef[2]];
  const top=positionKm.map((v,i)=>v-observerEci[i]),eq=raDecFromVector(top),ra=eq.raDeg*Math.PI/180,dec=eq.decDeg*Math.PI/180,lst=(gmstDegrees(at)+lon)*Math.PI/180,hour=lst-ra;
  const alt=Math.asin(Math.sin(phi)*Math.sin(dec)+Math.cos(phi)*Math.cos(dec)*Math.cos(hour));
  let az=Math.atan2(-Math.sin(hour)*Math.cos(dec),Math.sin(dec)*Math.cos(phi)-Math.cos(dec)*Math.sin(phi)*Math.cos(hour));if(az<0)az+=Math.PI*2;
  return {azimuthDeg:az*180/Math.PI,elevationDeg:alt*180/Math.PI,raDeg:eq.raDeg,decDeg:eq.decDeg,rangeKm:eq.rangeKm,observedAt:isoUtc(at)};
}
export function makeVoyagerState({observedAt,positionKm,velocityKmS,source,orientationTruthClass='EARTH_POINTING_DERIVED'}){
  const distanceKm=vectorMagnitude(positionKm),light=lightTime(distanceKm),eq=raDecFromVector(positionKm);
  return {schemaVersion:SCHEMA_VERSION,generatedAt:new Date().toISOString(),observedAt:isoUtc(observedAt,'observedAt'),frame:'ICRF_GEOCENTRIC',units:{position:'km',velocity:'km/s',distance:'km',lightTime:'s',angles:'deg'},positionKm,velocityKmS,distanceKm,distanceAu:distanceKm/AU_KM,oneWayLightTimeSeconds:light.oneWaySeconds,roundTripLightTimeSeconds:light.roundTripSeconds,rangeRateKmS:radialVelocity(positionKm,velocityKmS),raDeg:eq.raDeg,decDeg:eq.decDeg,earthDirection:normalizeVector(positionKm.map(v=>-v)),orientationTruthClass,provenance:provenance(source)};
}
export function validateSignalSnapshot(value){
  if(!value||value.schemaVersion!==1)throw new TypeError('SignalSnapshotV1 schemaVersion must be 1');if(!SOURCE_MODES.includes(value.sourceMode))throw new TypeError('Invalid sourceMode');if(!SIGNAL_STATES.includes(value.analysis?.state))throw new TypeError('Invalid detector state');if(!Array.isArray(value.spectrum?.valuesDb)||value.spectrum.valuesDb.length>2048)throw new TypeError('Invalid spectrum');const p=provenance(value.provenance);
  if(value.sourceMode==='TELESCOPE_LIVE_VERIFIED'&&(p.truthClass!=='TELESCOPE_LIVE_VERIFIED'||value.analysis.state!=='VERIFIED_CARRIER'))throw new TypeError('Verified telescope mode requires verified provenance and carrier state');
  if(value.sourceMode==='RECORDED_AUTHENTIC_VERIFIED'&&p.truthClass!=='RECORDED_AUTHENTIC_VERIFIED')throw new TypeError('Recorded authentic mode requires verified provenance');
  if(value.sourceMode==='SYNTHETIC_TEST'&&p.truthClass!=='SYNTHETIC_TEST')throw new TypeError('Synthetic mode requires synthetic truth class');return value;
}
export function publicError(code,message,status=502,details=undefined){return {schemaVersion:1,error:{code,message,details},status,generatedAt:new Date().toISOString()}}
