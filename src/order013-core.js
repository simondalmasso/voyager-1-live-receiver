export const KM_PER_AU=149597870.7;
export const C_KM_S=299792.458;
export const VISUAL_SCALE_TRUTH={solar:'TRUE_ORBIT_RELATIVE',overview:'PLANETARY_OVERVIEW',log:'VOYAGER_DISTANCE_LOG',radii:'DISPLAY_RADIUS_EXAGGERATED',orbits:'ORBIT_APPROXIMATION'};
export function physicalKmToSceneSolarUnits(km){return Number(km)/KM_PER_AU*4;}
export function physicalKmToSceneLogDistanceUnits(km){const au=Math.max(0,Number(km)/KM_PER_AU);return au===0?0:Math.log10(1+au)*13;}
export function localSpacecraftMetersToSceneLocalUnits(m){return Number(m)*0.72;}
export function vectorDistanceKm(a,b){return Math.hypot(a[0]-b[0],a[1]-b[1],a[2]-b[2]);}
export function distanceMetrics(a,b){const r=[b.positionKm[0]-a.positionKm[0],b.positionKm[1]-a.positionKm[1],b.positionKm[2]-a.positionKm[2]],v=[b.velocityKmS[0]-a.velocityKmS[0],b.velocityKmS[1]-a.velocityKmS[1],b.velocityKmS[2]-a.velocityKmS[2]],km=Math.hypot(...r),rangeRate=km?((r[0]*v[0]+r[1]*v[1]+r[2]*v[2])/km):0;return {km,au:km/KM_PER_AU,oneWayLightSeconds:km/C_KM_S,theoreticalRttSeconds:2*km/C_KM_S,rangeRateKmS:rangeRate};}
export function verifyCommonEpochFrame(ephemeris){const names=['Sun','Mercury','Venus','Earth','Mars','Jupiter','Saturn','Uranus','Neptune','Voyager 1'];return ephemeris?.frame==='ECLIPJ2000'&&ephemeris?.source==='JPL_HORIZONS'&&names.every(n=>Array.isArray(ephemeris?.bodies?.[n]?.positionKm)&&ephemeris.bodies[n].positionKm.length===3);}
export function heroCameraDistance({radius,fovDeg=42,aspect=16/9,safeArea=.78}){const v=Math.max(.1,fovDeg*Math.PI/180),h=2*Math.atan(Math.tan(v/2)*Math.max(.2,aspect)),half=Math.min(v,h)/2;return Math.max(.5,Number(radius)/Math.sin(half)/Math.max(.5,Math.min(.95,safeArea)));}
export function formatLight(seconds){const s=Math.max(0,Number(seconds));if(s>=3600)return `${Math.floor(s/3600)} h ${Math.floor((s%3600)/60)} min`;if(s>=60)return `${Math.floor(s/60)} min ${Math.round(s%60)} s`;return `${s.toFixed(1)} s`;}
