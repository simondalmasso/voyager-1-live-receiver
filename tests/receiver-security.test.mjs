import test from 'node:test';
import assert from 'node:assert/strict';
import { canonical,verifyUpload } from '../worker/index.js';
import { lost,noSource } from '../worker/receiver-hub.js';

const b64=bytes=>Buffer.from(bytes).toString('base64');
async function fixture(overrides={}){
  const pair=await crypto.subtle.generateKey({name:'Ed25519'},true,['sign','verify']);
  const pub=await crypto.subtle.exportKey('raw',pair.publicKey);
  const now=new Date().toISOString();
  const body={schemaVersion:1,stationId:'test-dish',sequence:7,nonce:'nonce-1234567890',softwareSha:'abcdef1234567890',observedAt:now,band:{centerFrequencyHz:8_420_430_000},snapshot:{schemaVersion:1,sourceMode:'TELESCOPE_LIVE_VERIFIED',station:{id:'test-dish',name:'Test Dish'},analysis:{state:'VERIFIED_CARRIER',confidence:.97,expectedFrequencyHz:8_420_430_000,observedFrequencyHz:8_420_429_991,snrDb:16.2},spectrum:{valuesDb:[-81,-74,-42,-76]},provenance:{truthClass:'TELESCOPE_LIVE_VERIFIED',sourceId:'test-dish',fetchedAt:now},generatedAt:now},...overrides};
  const signed={...body};delete signed.signature;
  body.signature=b64(await crypto.subtle.sign({name:'Ed25519'},pair.privateKey,new TextEncoder().encode(canonical(signed))));
  const env={RECEIVER_STATIONS_JSON:JSON.stringify([{id:'test-dish',name:'Test Dish',publicKeyBase64:b64(pub),allowedMinHz:8_400_000_000,allowedMaxHz:8_500_000_000}])};
  return {body,env,pair};
}

test('valid station Ed25519 envelope verifies without exposing private material',async()=>{const {body,env}=await fixture();const v=await verifyUpload(body,env);assert.equal(v.stationId,'test-dish');assert.equal(v.snapshot.sourceMode,'TELESCOPE_LIVE_VERIFIED');assert.ok(v.verifiedAt)});

test('tampered signed payload and wrong key are rejected',async()=>{
  const {body,env}=await fixture();const tampered=structuredClone(body);tampered.band.centerFrequencyHz+=10;await assert.rejects(()=>verifyUpload(tampered,env),/SIGNATURE_INVALID/);
  const other=await crypto.subtle.generateKey({name:'Ed25519'},true,['sign','verify']),raw=await crypto.subtle.exportKey('raw',other.publicKey);const wrong={RECEIVER_STATIONS_JSON:JSON.stringify([{...JSON.parse(env.RECEIVER_STATIONS_JSON)[0],publicKeyBase64:b64(raw)}])};await assert.rejects(()=>verifyUpload(body,wrong),/SIGNATURE_INVALID/);
});

test('stale, future, station mismatch and synthetic promotion are rejected',async()=>{
  const stale=await fixture({observedAt:new Date(Date.now()-180000).toISOString()});await assert.rejects(()=>verifyUpload(stale.body,stale.env),/STALE_UPLOAD/);
  const future=await fixture({observedAt:new Date(Date.now()+60000).toISOString()});await assert.rejects(()=>verifyUpload(future.body,future.env),/FUTURE_CLOCK_SKEW/);
  const mismatch=await fixture();mismatch.body.snapshot.station.id='different-dish';await assert.rejects(()=>verifyUpload(mismatch.body,mismatch.env),/STATION_MISMATCH/);
  const synthetic=await fixture();synthetic.body.snapshot.sourceMode='SYNTHETIC_TEST';synthetic.body.snapshot.provenance.truthClass='SYNTHETIC_TEST';await assert.rejects(()=>verifyUpload(synthetic.body,synthetic.env),/SOURCE_NOT_LIVE_VERIFIED|SIGNATURE_INVALID/);
});

test('expired verified signal is represented as LOST, absence as NO_SOURCE',()=>{const base={analysis:{state:'VERIFIED_CARRIER',confidence:.9}};const l=lost(base);assert.equal(l.sourceMode,'LOST');assert.equal(l.analysis.state,'LOST');assert.equal(l.provenance.truthClass,'LOST');const n=noSource();assert.equal(n.sourceMode,'NO_SOURCE');assert.equal(n.analysis.state,'NO_SOURCE')});
