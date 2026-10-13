import test from 'node:test';
import assert from 'node:assert/strict';
import { analyzePwsCsv } from '../src/os-voyager.js';

test('PWS measurement CSV summary preserves timestamp range and numeric statistics',()=>{
  const csv='SCET,ElectronDensity_cm-3,Frequency_Hz\n2012-10-22T09:44:19Z,0.05,1200\n2012-10-23T09:44:19Z,0.04,1100\n2012-10-24T09:44:19Z,0.07,1300\n';
  const result=analyzePwsCsv(csv);
  assert.equal(result.classification,'MEASUREMENT_TABLE');
  assert.equal(result.rowCount,3);
  assert.equal(result.timeRange.start,'2012-10-22T09:44:19.000Z');
  assert.equal(result.timeRange.end,'2012-10-24T09:44:19.000Z');
  assert.equal(result.fillValuesMasked,false);
  assert.equal(result.numericSummaries.find(x=>x.name==='ElectronDensity_cm-3').min,0.04);
  assert.equal(result.numericSummaries.find(x=>x.name==='ElectronDensity_cm-3').max,0.07);
});

test('PDS collection inventory is not misclassified as measurement rows',()=>{
  const result=analyzePwsCsv('LIDVID,FILE_REF_NAME,FILE_REF_URL\nurn:nasa:pds:example,data.csv,https://example.invalid/data.csv\n');
  assert.equal(result.classification,'PDS_COLLECTION_INVENTORY');
  assert.equal(result.rowCount,1);
});

test('CSV parser respects quoted commas and escaped quotes',()=>{
  const result=analyzePwsCsv('SCET,"Electron density, cm-3",Note\n2020-01-01T00:00:00Z,2.5,"text ""quoted"""\n');
  assert.equal(result.columns[1],'Electron density, cm-3');
  assert.equal(result.numericSummaries[0].min,2.5);
});
