import { useEffect, useRef } from 'react'
import { MapContainer as LeafletMap, TileLayer, useMap, GeoJSON } from 'react-leaflet'
import L from 'leaflet'
import { WatershedHeatmapLayer } from './layers/WatershedHeatmapLayer'
import type { MapViewState } from '../../types'

export interface Bbox { minx: number; miny: number; maxx: number; maxy: number }

interface MapContainerProps {
  center: [number, number]
  zoom: number
  layers: MapViewState['layers']
  rectangleDrawMode?: boolean
  onBboxDrawn?: (bbox: Bbox) => void
  heatmapData?: GeoJSON.GeoJsonObject | null
  drawnRectangle?: GeoJSON.Feature<GeoJSON.Polygon> | null
  heatmapMode?: 'area' | 'tc'
}

function MapCenterUpdater({ center, zoom }: { center: [number, number]; zoom: number }) {
  const map = useMap()
  useEffect(() => {
    map.setView(center, zoom)
  }, [map, center, zoom])
  return null
}

export function MapContainer({
  center,
  zoom,
  layers,
  rectangleDrawMode = false,
  onBboxDrawn,
  heatmapData,
  drawnRectangle,
  heatmapMode = 'area',
}: MapContainerProps) {
  return (
    <LeafletMap
      data-testid="map-container"
      center={center}
      zoom={zoom}
      style={{ height: '100%', width: '100%' }}
    >
      <MapCenterUpdater center={center} zoom={zoom} />
      {layers.imagery ? (
        <TileLayer
          attribution="Esri"
          url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        />
      ) : (
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
      )}
      {drawnRectangle && (
        <GeoJSON
          data-testid="drawn-rectangle-layer"
          data={drawnRectangle}
          style={() => ({ color: '#06c', weight: 2, dashArray: '4 4', fillOpacity: 0.1 })}
        />
      )}
      {heatmapData && (
        <WatershedHeatmapLayer 
          data={heatmapData as GeoJSON.FeatureCollection} 
          mode={heatmapMode}
        />
      )}
      {rectangleDrawMode && onBboxDrawn && (
        <RectangleDrawHandler onBboxDrawn={onBboxDrawn} />
      )}
    </LeafletMap>
  )
}

function RectangleDrawHandler({ onBboxDrawn }: { onBboxDrawn: (bbox: Bbox) => void }) {
  const map = useMap()
  const onBboxDrawnRef = useRef(onBboxDrawn)
  onBboxDrawnRef.current = onBboxDrawn

  useEffect(() => {
    // Native rectangle drawing - no leaflet-draw library needed
    let isDrawing = false
    let startLatLng: L.LatLng | null = null
    let rectangle: L.Rectangle | null = null

    const container = map.getContainer()
    container.style.cursor = 'crosshair'

    const onMouseDown = (e: L.LeafletMouseEvent) => {
      isDrawing = true
      startLatLng = e.latlng
      map.dragging.disable()
    }

    const onMouseMove = (e: L.LeafletMouseEvent) => {
      if (!isDrawing || !startLatLng) return
      const bounds = L.latLngBounds(startLatLng, e.latlng)
      if (rectangle) {
        rectangle.setBounds(bounds)
      } else {
        rectangle = L.rectangle(bounds, { color: '#3388ff', weight: 2, fillOpacity: 0.2 })
        rectangle.addTo(map)
      }
    }

    const onMouseUp = (e: L.LeafletMouseEvent) => {
      if (!isDrawing || !startLatLng) return
      isDrawing = false
      map.dragging.enable()

      const bounds = L.latLngBounds(startLatLng, e.latlng)

      // Only trigger if rectangle has meaningful size
      const minSize = 0.0001 // ~10 meters
      if (Math.abs(bounds.getEast() - bounds.getWest()) > minSize && 
          Math.abs(bounds.getNorth() - bounds.getSouth()) > minSize) {
        onBboxDrawnRef.current({
          minx: bounds.getWest(),
          miny: bounds.getSouth(),
          maxx: bounds.getEast(),
          maxy: bounds.getNorth(),
        })
      }

      // Remove the temporary rectangle (will be replaced by GeoJSON layer)
      if (rectangle) {
        map.removeLayer(rectangle)
        rectangle = null
      }
      startLatLng = null
    }

    map.on('mousedown', onMouseDown)
    map.on('mousemove', onMouseMove)
    map.on('mouseup', onMouseUp)

    return () => {
      container.style.cursor = ''
      map.dragging.enable()
      map.off('mousedown', onMouseDown)
      map.off('mousemove', onMouseMove)
      map.off('mouseup', onMouseUp)
      if (rectangle) {
        map.removeLayer(rectangle)
      }
    }
  }, [map])

  return null
}
