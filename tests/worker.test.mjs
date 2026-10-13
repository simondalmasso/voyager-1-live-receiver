import test from 'node:test';
import assert from 'node:assert/strict';
import {parseHorizonsVectors} from '../worker/horizons.js';
import {parseDsnXml} from '../worker/dsn.js';
import {api,SECURITY} from '../worker/index.js';
const H=`header\n$$SOE\n2461000.5, A.D. 2026-Aug-05 00:00:00.0000, -1.9E+10, -1.5E+10, 7.7E+9, -12.4, -10.2, 5.1, 0,0,0\n$$EOE`;

test('Horizons parser requires markers, finite vectors and derived truth',()=>{
  const s=parseHorizonsVectors(H,'2026-08-05T00:00:01Z');
  assert.equal(s.provenance.truthClass,'DERIVED_GEOMETRY');
  assert.equal(s.provenance.upstreamAuthority,'JPL Horizons');
  assert.ok(s.distanceKm>1e10);
  assert.throws(()=>parseHorizonsVectors('<html>error</html>'));
});

test('DSN parser rejects entities and only reports explicit Voyager 1',()=>{
  assert.throws(()=>parseDsnXml('<!DOCTYPE x [<!ENTITY y SYSTEM "file:///etc/passwd">]>'));
  const d=parseDsnXml('<root><dish name="DSS-14" complex="Goldstone"><target>Voyager 1</target><band>X</band></dish></root>');
  assert.equal(d.available,true);
  assert.equal(d.stations[0].target,'Voyager 1');
  assert.equal(d.provenance.truthClass,'DSN_LIVE_PUBLIC_STATUS');
});

test('API validates observer inputs and emits security headers',async()=>{
  const url=new URL('https://x/api/v1/voyager/sky?lat=999&lon=0');
  const r=await api(new Request(url),url,{});
  assert.equal(r.status,400);
  assert.equal(SECURITY['x-content-type-options'],'nosniff');
});

test('DSN Now parser reads nested target attributes and directional signal state',()=>{
  const xml='<dsn><timestamp>2026-10-13T05:00:00Z</timestamp><station name="MDSCC" friendlyName="Madrid" timeUTC="2026-10-13T05:00:00Z"/><dish name="DSS-63" azimuthAngle="210.0" elevationAngle="35.0" activity="Track"><target name="Voyager 1" id="-31" uplegRange="1" downlegRange="2" rtlt="3"/><downSignal active="true" signalType="data" dataRate="160" frequency="8420" band="X" power="-155" spacecraft="Voyager 1" spacecraftID="-31"/><upSignal active="false" signalType="command" dataRate="0" frequency="8420" band="X" power="-160" spacecraft="Voyager 1" spacecraftID="-31"/></dish></dsn>';
  const d=parseDsnXml(xml,'2026-10-13T05:00:01Z');
  assert.equal(d.available,true);
  assert.equal(d.sourceTimestamp,'2026-10-13T05:00:00Z');
  assert.equal(d.stations[0].dish,'DSS-63');
  assert.equal(d.stations[0].downlinkActive,true);
  assert.equal(d.stations[0].uplinkActive,false);
  assert.equal(d.stations[0].band,'X');
  assert.equal(d.provenance.truthClass,'DSN_LIVE_PUBLIC_STATUS');
  assert.equal(d.provenance.fetchedAt,'2026-10-13T05:00:01Z');
});
test('DSN Now does not promote another spacecraft to Voyager 1',()=>{
  const d=parseDsnXml('<dsn><timestamp>2026-10-13T05:00:00Z</timestamp><dish name="DSS-63"><target name="Voyager 2" id="-32"/></dish></dsn>');
  assert.equal(d.available,false);
  assert.equal(d.stations.length,0);
  assert.equal(d.provenance.truthClass,'UNAVAILABLE');
});
