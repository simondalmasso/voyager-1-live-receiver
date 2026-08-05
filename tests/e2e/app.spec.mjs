import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('loads honest degraded-capable flight experience', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: /farthest human-made object/i })).toBeVisible();

  await page.getByRole('button', { name: /SIGNAL/ }).click();
  await expect(page.getByText(/RECEIVE-ONLY/).first()).toBeVisible();
  await expect(page.getByText('SYNTHETIC TEST').last()).toBeVisible();
  await expect(page.getByText(/not a live Voyager reception/i)).toBeVisible();
});

test('desktop keyboard modes and recenter remain operable', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'chromium', 'Physical keyboard shortcuts are a desktop interaction.');

  await page.goto('/');
  await page.keyboard.press('2');
  await expect(page.getByRole('heading', { name: /human path beyond/i })).toBeVisible();
  await page.keyboard.press('r');
  await expect(page.locator('#camera-label')).toContainText('HERO');
});

test('invalid deep link is sanitized', async ({ page }) => {
  await page.goto('/?mode=javascript:alert(1)');
  await expect(page.getByRole('heading', { name: /farthest human-made object/i })).toBeVisible();
});

test('axe has no serious or critical violations', async ({ page }) => {
  await page.goto('/');
  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations.filter(violation => ['critical', 'serious'].includes(violation.impact))).toEqual([]);
});
