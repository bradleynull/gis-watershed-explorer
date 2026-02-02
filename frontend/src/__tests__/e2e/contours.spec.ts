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

test('rectangle draw mode shows instructions and draw toolbar', async ({ page }) => {
  await loadMapAtLocation(page, '35.2', '-80.8')

  await page.check('[data-testid="rectangle-draw-mode"]')
  await expect(page.locator('[data-testid="query-panel"]')).toContainText(
    'Rectangle contours',
    { timeout: 5000 }
  )
  await expect(page.locator('[data-testid="query-panel"]')).toContainText(
    'jet-colored contour map',
    { timeout: 2000 }
  )

  // Leaflet Draw toolbar appears when in rectangle mode
  await expect(page.locator('.leaflet-draw-draw-rectangle')).toBeVisible({ timeout: 5000 })
})

test('drawing rectangle shows jet-colored contour map', async ({ page }) => {
  await loadMapAtLocation(page, '35.2', '-80.8')

  await page.check('[data-testid="rectangle-draw-mode"]')
  await expect(page.locator('.leaflet-draw-draw-rectangle')).toBeVisible({ timeout: 5000 })
  await page.click('.leaflet-draw-draw-rectangle')

  // Draw a rectangle on the map: mousedown at start, drag to end, mouseup
  const mapContainer = page.locator('.leaflet-container')
  await expect(mapContainer).toBeVisible()
  const box = await mapContainer.boundingBox()
  expect(box).toBeTruthy()
  const startX = box!.x + box!.width * 0.3
  const startY = box!.y + box!.height * 0.3
  const endX = box!.x + box!.width * 0.6
  const endY = box!.y + box!.height * 0.6

  await page.mouse.move(startX, startY)
  await page.mouse.down()
  await page.mouse.move(endX, endY, { steps: 20 })
  await page.mouse.up()

  // Wait for contour layer (API returns contours for bbox)
  await expect(page.locator('[data-testid="bbox-contour-layer"]')).toBeVisible({
    timeout: 25000,
  })
  await expect(page.locator('[data-testid="drawn-rectangle-layer"]')).toBeAttached()
})
