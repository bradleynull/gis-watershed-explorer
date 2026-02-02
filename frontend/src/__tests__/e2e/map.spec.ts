import { test, expect } from '@playwright/test'

test('page loads with map', async ({ page }) => {
  await page.goto('/')
  await expect(page.locator('[data-testid="map-container"]')).toBeVisible({ timeout: 20000 })
})

test('location input and load map', async ({ page }) => {
  await page.goto('/')
  await page.fill('[data-testid="lat-input"]', '35.1234')
  await page.fill('[data-testid="lon-input"]', '-80.5678')
  await page.click('[data-testid="load-map"]')
  await expect(page.locator('.leaflet-container')).toBeVisible({ timeout: 10000 })
})

test('layer panel has toggles', async ({ page }) => {
  await page.goto('/')
  await expect(page.locator('[data-testid="layer-panel"]')).toBeVisible({ timeout: 10000 })
  const checkboxes = page.locator('[data-testid="layer-panel"] input[type="checkbox"]')
  await expect(checkboxes).toHaveCount(4)
})
