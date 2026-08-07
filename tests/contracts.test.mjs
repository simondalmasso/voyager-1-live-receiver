import test from 'node:test';
import assert from 'node:assert/strict';
import {AU_KM,C_KM_S,lightTime,makeVoyagerState,topocentricFromGeocentric,validateSignalSnapshot} from '../shared/contracts.js';

test('physical constants and light-time are exact',()=>{
  assert.equal(C_KM_S,299792.458);
  assert.equal(AU_KM,149597870.7);
  assert.equal(lightTime(C_KM_S).oneWaySeconds,1);
});

test('state derives distance, radial velocity and Earth direction',()=>{
  const s=makeVoyagerState({observedAt:'2026-01-01T00:00:00Z',positionKm:[3,4,0],velocityKmS:[.3,.4,0],source:{truthClass:'DERIVED_GEOMETRY',sourceId:'test-horizons',fetchedAt:'2026-01-01T00:00:00Z'}});
  assert.equal(s.distanceKm,5);
  assert.equal(s.rangeRateKmS,.5);
  assert.equal(s.oneWayLightTimeSeconds,5/C_KM_S);
  assert.deepEqual(s.earthDirection,[-.6,-.8,0]);
  assert.equal(s.orientationTruthClass,'EARTH_POINTING_DERIVED');
});

test('synthetic snapshot remains synthetic and cannot alias telescope live',()=>{
  const v=validateSignalSnapshot({schemaVersion:1,sourceMode:'SYNTHETIC_TEST',analysis:{state:'VERIFIED_CARRIER'},spectrum:{valuesDb:[-90,-40]},provenance:{truthClass:'SYNTHETIC_TEST',sourceId:'fixture',fetchedAt:'2026-01-01T00:00:00Z'}});
  assert.equal(v.sourceMode,'SYNTHETIC_TEST');
  assert.notEqual(v.provenance.truthClass,'TELESCOPE_LIVE_VERIFIED');
  assert.throws(()=>validateSignalSnapshot({...v,sourceMode:'TELESCOPE_LIVE_VERIFIED'}),/requires verified provenance/);
});

test('topocentric observer validates coordinates and yields finite sky angles',()=>{
  const sky=topocentricFromGeocentric([2.1e10,-1.2e10,8e9],{lat:-31.6333,lon:-60.7,elevation:25,at:'2026-08-07T08:00:00Z'});
  assert.ok(Number.isFinite(sky.azimuthDeg));
  assert.ok(Number.isFinite(sky.elevationDeg));
  assert.ok(sky.azimuthDeg>=0&&sky.azimuthDeg<360);
  assert.throws(()=>topocentricFromGeocentric([1,2,3],{lat:91,lon:0}),/outside range/);
});
