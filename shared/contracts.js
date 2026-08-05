export const SCHEMA_VERSION = 1;
export const TRUTH_CLASSES = Object.freeze(['OFFICIAL','DERIVED','INTERPOLATED','TELESCOPE_LIVE','RECORDED_AUTHENTIC','SIMULATED','STALE','UNAVAILABLE']);
export const SIGNAL_STATES = Object.freeze(['NO_SOURCE','ACQUIRING','SEARCHING','CANDIDATE','DETECTED','LOST','STALE','ERROR']);
export const SOURCE_MODES = Object.freeze(['TELESCOPE_LIVE','RECORDED_AUTHENTIC','SYNTHETIC_TEST','NO_SOURCE']);
export const C_KM_S = 299_792.458;
export const AU_KM = 149_597_870.7;

export function assertFinite(value, name) {
  if (!Number.isFinite(value)) throw new TypeError(`${name} must be finite`);
  return value;
}
export function isoUtc(value, name='timestamp') {
  const date = new Date(value);
  if (Number.isNaN(date.valueOf()) || !date.toISOString().endsWith('Z')) throw new TypeError(`${name} must be UTC ISO-8601`);
  return date.toISOString();
}
export function provenance(input) {
  if (!input || !TRUTH_CLASSES.includes(input.truthClass)) throw new TypeError('Invalid truthClass');
  if (!input.sourceId || typeof input.sourceId !== 'string') throw new TypeError('sourceId required');
  return { ...input, fetchedAt: isoUtc(input.fetchedAt ?? new Date().toISOString(),'fetchedAt') };
}
export function lightTime(distanceKm) {
  assertFinite(distanceKm,'distanceKm');
  if (distanceKm < 0) throw new RangeError('distanceKm cannot be negative');
  const oneWaySeconds = distanceKm / C_KM_S;
  return { oneWaySeconds, roundTripSeconds: oneWaySeconds * 2 };
}
export function vectorMagnitude([x,y,z]) { return Math.hypot(assertFinite(x,'x'),assertFinite(y,'y'),assertFinite(z,'z')); }
export function normalizeVector(vector) {
  const mag = vectorMagnitude(vector);
  if (mag === 0) throw new RangeError('Cannot normalize zero vector');
  return vector.map(v => v / mag);
}
export function radialVelocity(positionKm, velocityKmS) {
  const direction = normalizeVector(positionKm);
  return direction[0]*velocityKmS[0] + direction[1]*velocityKmS[1] + direction[2]*velocityKmS[2];
}
export function makeVoyagerState({observedAt,positionKm,velocityKmS,source,orientationTruthClass='EARTH_POINTING_DERIVED'}) {
  const distanceKm = vectorMagnitude(positionKm);
  const light = lightTime(distanceKm);
  return {
    schemaVersion: SCHEMA_VERSION,
    generatedAt: new Date().toISOString(),
    observedAt: isoUtc(observedAt,'observedAt'),
    frame: 'ICRF_GEOCENTRIC',
    units: { position:'km', velocity:'km/s', distance:'km', lightTime:'s' },
    positionKm,
    velocityKmS,
    distanceKm,
    distanceAu: distanceKm / AU_KM,
    oneWayLightTimeSeconds: light.oneWaySeconds,
    roundTripLightTimeSeconds: light.roundTripSeconds,
    rangeRateKmS: radialVelocity(positionKm,velocityKmS),
    earthDirection: normalizeVector(positionKm.map(v => -v)),
    orientationTruthClass,
    provenance: provenance(source)
  };
}
export function validateSignalSnapshot(value) {
  if (!value || value.schemaVersion !== 1) throw new TypeError('SignalSnapshotV1 schemaVersion must be 1');
  if (!SOURCE_MODES.includes(value.sourceMode)) throw new TypeError('Invalid sourceMode');
  if (!SIGNAL_STATES.includes(value.analysis?.state)) throw new TypeError('Invalid detector state');
  if (!Array.isArray(value.spectrum?.valuesDb) || value.spectrum.valuesDb.length > 2048) throw new TypeError('Invalid spectrum');
  provenance(value.provenance);
  return value;
}
export function publicError(code,message,status=502,details=undefined){ return {schemaVersion:1,error:{code,message,details},status,generatedAt:new Date().toISOString()}; }
