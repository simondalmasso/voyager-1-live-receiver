import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { ready } from './helpers.mjs';

test('mission trajectory and receive-only lab remain available through current navigation',async({page})=>{
  await ready(page);
  await expect(page.getByRole('button',{name:'MISSION TRAJECTORY'})).toBeVisible();
  await page.getByRole('button',{name:'SIGNAL LAB'}).click();
  await expect(page.locator('#lab-drawer')).toBeVisible();
  await expect(page.locator('#o13-mode-status')).toContainText('SIGNAL LAB');
  await expect(page.locator('#lab-capabilities')).toContainText(/WOLA 4-tap/);
  await expect(page.locator('#lab-pipeline')).toContainText('SOURCE');
  await expect(page.locator('#lab-drawer')).toContainText(/no TLE or rotator control/i);
});

test('desktop keyboard modes and recenter remain operable',async({page},info)=>{
  test.skip(info.project.name!=='chromium','desktop keyboard');
  await ready(page);
  await page.keyboard.press('2');
  await expect(page.locator('[data-o13-mode="SOLAR_SYSTEM"]')).toHaveAttribute('aria-pressed','true');
  await expect(page.locator('#o13-solar-note')).toBeVisible();
  await page.evaluate(()=>{window.__order013.scene.camera.position.x+=3});
  await page.locator('#o13-recenter').click();
  await expect.poll(()=>page.evaluate(()=>window.__order013.scene.camera.position.distanceTo(window.__order013.scene.targetPosition))).toBeLessThan(0.25);
  await expect(page.locator('[data-o13-mode="SOLAR_SYSTEM"]')).toHaveAttribute('aria-pressed','true');
});

test('invalid deep link remains sanitized',async({page})=>{
  let dialogCount=0;
  page.on('dialog',dialog=>{dialogCount++;void dialog.dismiss()});
  await ready(page,'/?mode=javascript:alert(1)');
  await expect(page.locator('[data-o13-mode="FLIGHT"]')).toHaveAttribute('aria-pressed','true');
  expect(dialogCount).toBe(0);
});

test('axe has no serious or critical violations',async({page})=>{
  await ready(page);
  const results=await new AxeBuilder({page}).analyze();
  expect(results.violations.filter(v=>['critical','serious'].includes(v.impact))).toEqual([]);
});
