import { useState, useCallback } from 'react'
import { MapContainer, type Bbox } from './components/Map/MapContainer'
import { LocationInput } from './components/Controls/LocationInput'
import { QueryPanel } from './components/QueryPanel/QueryPanel'
import * as api from './services/api'
import type { MapViewState } from './types'

function bboxToRectangleGeoJSON(bbox: Bbox): GeoJSON.Feature<GeoJSON.Polygon> {
  const { minx, miny, maxx, maxy } = bbox
  return {
    type: 'Feature',
    geometry: {
      type: 'Polygon',
      coordinates: [[[minx, miny], [maxx, miny], [maxx, maxy], [minx, maxy], [minx, miny]]],
    },
    properties: {},
  }
}

function App() {
  const [center, setCenter] = useState<[number, number]>([35.2, -80.8])
  const [zoom, setZoom] = useState(14)
  const [layers, setLayers] = useState<MapViewState['layers']>({
    imagery: true,
    contours: false,
    rivers: false,
    floodZones: false,
  })
  const [rectangleDrawMode, setRectangleDrawMode] = useState(false)
  const [heatmapData, setHeatmapData] = useState<GeoJSON.GeoJsonObject | null>(null)
  const [drawnRectangle, setDrawnRectangle] = useState<GeoJSON.Feature<GeoJSON.Polygon> | null>(null)
  const [heatmapMode, setHeatmapMode] = useState<'area' | 'tc'>('area')
  const [gridSpacing, setGridSpacing] = useState(100)
  const [isLoading, setIsLoading] = useState(false)

  // Memoize onBboxDrawn to prevent RectangleDrawHandler useEffect from re-running on every render
  const handleBboxDrawn = useCallback((bbox: Bbox) => {
    setDrawnRectangle(bboxToRectangleGeoJSON(bbox))
    setIsLoading(true)
    api
      .getWatershedGrid(bbox.minx, bbox.miny, bbox.maxx, bbox.maxy, gridSpacing)
      .then((data) => {
        setHeatmapData(data)
        setIsLoading(false)
      })
      .catch(() => {
        setHeatmapData(null)
        setIsLoading(false)
      })
  }, [gridSpacing])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <header style={{ padding: '8px 16px', display: 'flex', gap: 16, alignItems: 'center', borderBottom: '1px solid #ccc' }}>
        <h1 style={{ margin: 0, fontSize: 18 }}>Watershed Analysis</h1>
        <LocationInput
          onLoad={(lat, lon) => {
            setCenter([lat, lon])
            setZoom(14)
          }}
        />
        <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <input
            type="checkbox"
            checked={rectangleDrawMode}
            onChange={(e) => {
              setRectangleDrawMode(e.target.checked)
              if (!e.target.checked) {
                setHeatmapData(null)
                setDrawnRectangle(null)
              }
            }}
            data-testid="rectangle-draw-mode"
          />
          Draw watershed heatmap
        </label>
        <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <input
            type="checkbox"
            checked={layers.imagery}
            onChange={(e) => setLayers({ ...layers, imagery: e.target.checked })}
          />
          Satellite
        </label>
      </header>
      <div style={{ flex: 1, display: 'flex', position: 'relative' }}>
        <MapContainer
          center={center}
          zoom={zoom}
          layers={layers}
          rectangleDrawMode={rectangleDrawMode}
          onBboxDrawn={handleBboxDrawn}
          heatmapData={heatmapData}
          drawnRectangle={drawnRectangle}
          heatmapMode={heatmapMode}
        />
        <QueryPanel
          rectangleDrawMode={rectangleDrawMode}
          heatmapMode={heatmapMode}
          onHeatmapModeChange={setHeatmapMode}
          gridSpacing={gridSpacing}
          onGridSpacingChange={setGridSpacing}
          heatmapMetadata={heatmapData ? (heatmapData as { metadata?: Record<string, unknown> }).metadata : null}
          isLoading={isLoading}
        />
      </div>
    </div>
  )
}

export default App
