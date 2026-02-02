import { test, expect } from '@playwright/test'

async function loadMapAtLocation(
  page: import('@playwright/test').Page,
  lat: string,
  lon: string
) {
  await page.goto('/')
  await page.fill('[data-testid="lat-input"]', lat)
  await page.fill('[data-testid="lon-input"]', lon)
  await page.click('[data-testid="load-map"]')
  await expect(page.locator('.leaflet-container')).toBeVisible({ timeout: 15000 })
}

test('draw watershed: click map then Draw watershed shows polygon and time of concentration', async ({
  page,
}) => {
  await loadMapAtLocation(page, '35.2', '-80.8')
  await page.click('.leaflet-container', { position: { x: 400, y: 300 } })
  await expect(page.locator('[data-testid="query-panel"]')).toBeVisible({ timeout: 10000 })
  await page.click('[data-testid="query-watershed"]')
  await expect(page.locator('[data-testid="watershed-info-panel"]')).toBeVisible({ timeout: 20000 })
  await expect(page.locator('[data-testid="watershed-area"]')).toBeVisible()
  await expect(page.locator('[data-testid="watershed-tc"]')).toContainText(
    'Time of concentration'
  )
  await expect(page.locator('[data-testid="watershed-layer"]')).toBeAttached()
})
