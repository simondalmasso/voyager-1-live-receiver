import { test, expect } from '@playwright/test';
import { ready } from './helpers.mjs';

async function instrumentDownloads(page){
  await page.addInitScript(()=>{
    globalThis.__r3DownloadClicks=0;
    const original=HTMLAnchorElement.prototype.click;
    HTMLAnchorElement.prototype.click=function(){
      if(this.download){globalThis.__r3DownloadClicks+=1;return;}
      return original.call(this);
    };
  });
}

test('browser refuses partial listener manifest while NOT_READY',async({page})=>{
  await instrumentDownloads(page);
  await page.route('**/api/v2/lab/evidence',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({schemaVersion:2,status:'NOT_READY',canonicalStatus:'NOT_READY',truthClass:'TELESCOPE_LIVE_VERIFIED',missing:['station'],partialManifestAvailable:true,receiveOnly:true})}));
  await ready(page);await page.getByRole('button',{name:'SIGNAL LAB'}).click();await expect(page.locator('#lab-drawer')).toBeVisible();await page.locator('#evidence-download').click();
  await expect(page.locator('#evidence-status')).toContainText(/NOT READY.*station/i);
  expect(await page.evaluate(()=>globalThis.__r3DownloadClicks)).toBe(0);
});

test('browser downloads only canonical READY listener manifest',async({page})=>{
  await instrumentDownloads(page);
  await page.route('**/api/v2/lab/evidence',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({schemaVersion:2,status:'READY',canonicalStatus:'READY_CANONICAL_MANIFEST',truthClass:'RECORDED_AUTHENTIC_VERIFIED',missing:[],manifest:{schemaVersion:1,observationId:'r3-ready',files:{}},manifestSha256:'abcdef1234567890',bundleSha256:'1234',receiveOnly:true})}));
  await ready(page);await page.getByRole('button',{name:'SIGNAL LAB'}).click();await expect(page.locator('#lab-drawer')).toBeVisible();await page.locator('#evidence-download').click();
  await expect(page.locator('#evidence-status')).toContainText(/Canonical listener manifest downloaded/i);
  expect(await page.evaluate(()=>globalThis.__r3DownloadClicks)).toBe(1);
});
