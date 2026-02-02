import { test, expect } from '@playwright/test'

async function loadMapAtLocation(page: import('@playwright/test').Page, lat: string, lon: string) {
  await page.goto('/')
  await page.fill('[data-testid="lat-input"]', lat)
  await page.fill('[data-testid="lon-input"]', lon)
  await page.click('[data-testid="load-map"]')
  await expect(page.locator('.leaflet-container')).toBeVisible({ timeout: 15000 })
}

test('clicking map and flow direction shows flow path', async ({ page }) => {
  await loadMapAtLocation(page, '35.1234', '-80.5678')
  await page.click('.leaflet-container', { position: { x: 400, y: 300 } })
  await expect(page.locator('[data-testid="query-panel"]')).toBeVisible({ timeout: 10000 })
  await page.click('[data-testid="query-flow-direction"]')
  await expect(page.locator('[data-testid="flow-info-panel"]')).toBeVisible({ timeout: 15000 })
  await expect(page.locator('[data-testid="flow-distance"]')).toBeVisible()
})

test('flood zone query returns zone info', async ({ page }) => {
  await loadMapAtLocation(page, '35.1234', '-80.5678')
  await page.click('.leaflet-container', { position: { x: 400, y: 300 } })
  await page.click('[data-testid="query-flood-zone"]')
  const panel = page.locator('[data-testid="flood-info-panel"]')
  await expect(panel).toBeVisible({ timeout: 15000 })
  await expect(panel.locator('[data-testid="fema-zone"]')).toBeVisible()
})
