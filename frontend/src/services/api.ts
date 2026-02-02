const API_BASE = '/api'

export async function getWatershedGrid(
  minx: number,
  miny: number,
  maxx: number,
  maxy: number,
  gridSpacingM = 100
) {
  const params = new URLSearchParams({
    minx: String(minx),
    miny: String(miny),
    maxx: String(maxx),
    maxy: String(maxy),
    grid_spacing_m: String(gridSpacingM),
  })
  const r = await fetch(`${API_BASE}/hydrology/watershed/grid?${params}`)
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}
