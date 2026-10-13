import { test, expect } from '@playwright/test';
import { ready } from './helpers.mjs';
const viewports=[[360,800],[390,844],[412,915],[844,390],[1280,720],[1440,900]];

async function persistentOccupancy(page){
  return page.evaluate(()=>{
    const nodes=[...document.querySelectorAll('.o13-wordmark,.o13-truth,.o13-mode-status,.o13-nav')].filter(n=>getComputedStyle(n).display!=='none');
    const area=nodes.reduce((s,n)=>{const r=n.getBoundingClientRect();return s+r.width*r.height},0);
    return area/(innerWidth*innerHeight);
  });
}

test('first view keeps disclosures closed and current navigation visible',async({page})=>{
  await ready(page);
  await expect(page.locator('#o13-distance')).toBeHidden();
  await expect(page.locator('#o13-lookback')).toBeHidden();
  await expect(page.locator('#o13-solar-note')).toBeHidden();
  await expect(page.locator('#lab-drawer')).toBeHidden();
  await expect(page.locator('#os-voyager-panel')).toBeHidden();
  await expect(page.locator('.o13-nav')).toBeVisible();
  await expect(page.locator('[data-o13-mode="FLIGHT"]')).toHaveAttribute('aria-pressed','true');
  await expect(page.getByRole('button',{name:'Play or pause track 3'})).toBeVisible();
  expect(await persistentOccupancy(page)).toBeLessThan(0.1);
  await page.getByRole('button',{name:'SIGNAL LAB'}).click();
  await expect(page.locator('#lab-drawer')).toBeVisible();
  await expect(page.locator('#o13-mode-status')).toContainText('SIGNAL LAB');
});

test('lab disclosure exposes truthful pipeline and station physics',async({page})=>{
  await ready(page);
  await page.getByRole('button',{name:'SIGNAL LAB'}).click();
  await expect(page.locator('#lab-drawer')).toBeVisible();
  await expect(page.locator('#lab-capabilities')).toContainText(/WOLA 4-tap/);
  await expect(page.locator('#lab-pipeline')).toContainText('SOURCE');
  await page.locator('#station-form input[name=antennaDiameterM]').fill('20');
  await page.locator('#station-form input[name=apertureEfficiency]').fill('0.6');
  await page.locator('#station-form input[name=systemTemperatureK]').fill('50');
  await page.locator('#station-form input[name=bandwidthHz]').fill('1');
  await page.locator('#station-form input[name=integrationSeconds]').fill('100');
  await page.locator('#station-form button[type=submit]').click();
  await expect(page.locator('#station-output')).toContainText(/G\/T/);
  await page.locator('#lab-close').click();
  await expect(page.locator('#lab-drawer')).toBeHidden();
});

for(const [width,height] of viewports)test(`visual acceptance ${width}x${height}`,async({page},info)=>{
  test.skip(info.project.name!=='chromium','canonical screenshot matrix captured once in Chromium');
  await page.setViewportSize({width,height});
  await ready(page);
  const canvas=page.locator('#space-canvas');
  await expect(canvas).toBeVisible();
  await expect(canvas).toHaveAttribute('data-model-truth','NASA_OFFICIAL_GLB');
  await expect(page.locator('#lab-drawer')).toBeHidden();
  await expect(page.locator('.o13-nav')).toBeVisible();
  const audit=await page.evaluate(()=>window.__order013.getAudit());
  expect(audit.truth).toBe('NASA_OFFICIAL_GLB');
  expect(audit.fallbackUsed).toBe(false);
  expect(audit.commonEpochFrame).toBe(true);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth&&document.documentElement.scrollHeight<=innerHeight)).toBe(true);
  expect(await persistentOccupancy(page)).toBeLessThan(0.1);
  await info.attach(`order013-${width}x${height}`,{body:await page.screenshot({fullPage:true}),contentType:'image/png'});
});

test('reduced motion and disclosure remain usable',async({page})=>{
  await page.emulateMedia({reducedMotion:'reduce'});
  await ready(page);
  await expect(page.locator('#lab-drawer')).toBeHidden();
  await page.keyboard.press('6');
  await expect(page.locator('#lab-drawer')).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.locator('#lab-drawer')).toBeHidden();
  await expect(page.locator('[data-o13-mode="FLIGHT"]')).toHaveAttribute('aria-pressed','true');
});
