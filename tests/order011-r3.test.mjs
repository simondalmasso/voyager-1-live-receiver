import test from 'node:test';
import assert from 'node:assert/strict';
import { canonical,verifyUpload } from '../worker/index.js';
import { canonicalEvidenceStatus,pipelineTelemetry } from '../worker/lab.js';

const b64=bytes=>Buffer.from(bytes).toString('base64');
async function signedSnapshot(evidence){
  const pair=await crypto.subtle.generateKey({name:'Ed25519'},true,['sign','verify']);
  const publicKey=await crypto.subtle.exportKey('raw',pair.publicKey);
  const now=new Date().toISOString();
  const snapshot={schemaVersion:1,sourceMode:'TELESCOPE_LIVE_VERIFIED',station:{id:'r3-dish',name:'R3 Dish'},analysis:{state:'VERIFIED_CARRIER',confidence:.97,expectedFrequencyHz:8420430000,observedFrequencyHz:8420429999,snrDb:12},spectrum:{valuesDb:[-80,-70,-60]},evidence,provenance:{truthClass:'TELESCOPE_LIVE_VERIFIED',sourceId:'r3-dish',fetchedAt:now},generatedAt:now};
  const body={schemaVersion:1,stationId:'r3-dish',sequence:1,nonce:'r3-nonce-123456789',softwareSha:'abcdef1234abcdef',observedAt:now,band:{centerFrequencyHz:8420430000},snapshot};
  body.signature=b64(await crypto.subtle.sign({name:'Ed25519'},pair.privateKey,new TextEncoder().encode(canonical(body))));
  const env={RECEIVER_STATIONS_JSON:JSON.stringify([{id:'r3-dish',name:'R3 Dish',publicKeyBase64:b64(publicKey),allowedMinHz:8400000000,allowedMaxHz:8500000000}])};
  return (await verifyUpload(body,env)).snapshot;
}

test('signed partial manifest remains NOT_READY end to end',async()=>{
  const manifest={schemaVersion:1,observationId:'partial',files:{}};
  const snapshot=await signedSnapshot({status:'NOT_READY',missing:['station'],manifest,manifestSha256:'partial-sha'});
  const api=canonicalEvidenceStatus(snapshot),pipeline=pipelineTelemetry(snapshot),stage=pipeline.stages.find(x=>x.id==='EVIDENCE');
  assert.equal(api.status,'NOT_READY');assert.equal(api.partialManifestAvailable,true);assert.deepEqual(api.missing,['station']);assert.equal('manifest' in api,false);
  assert.equal(stage.status,'NOT_READY');assert.deepEqual(stage.missing,['station']);assert.equal(stage.partialManifestAvailable,true);
});

test('manifest existence without canonical listener READY never promotes evidence',()=>{
  const manifest={schemaVersion:1,observationId:'ambiguous',files:{}};
  const api=canonicalEvidenceStatus({provenance:{truthClass:'RECORDED_AUTHENTIC_VERIFIED'},evidence:{status:'READY',missing:[],manifest}});
  assert.equal(api.status,'NOT_READY');assert.equal(api.partialManifestAvailable,true);assert.ok(api.missing.includes('listenerEvidenceReadiness'));
});

test('canonical READY requires status manifest and empty missing simultaneously',async()=>{
  const manifest={schemaVersion:1,observationId:'ready',files:{'station.json':{sha256:'abc'}}};
  const snapshot=await signedSnapshot({status:'READY_CANONICAL_MANIFEST',missing:[],manifest,manifestSha256:'ready-sha',bundleSha256:'bundle-sha'});
  const api=canonicalEvidenceStatus(snapshot),stage=pipelineTelemetry(snapshot).stages.find(x=>x.id==='EVIDENCE');
  assert.equal(api.status,'READY');assert.equal(api.canonicalStatus,'READY_CANONICAL_MANIFEST');assert.equal(api.manifest,manifest);assert.deepEqual(api.missing,[]);
  assert.equal(stage.status,'READY_CANONICAL_MANIFEST');assert.deepEqual(stage.missing,[]);assert.equal(stage.partialManifestAvailable,false);
});
