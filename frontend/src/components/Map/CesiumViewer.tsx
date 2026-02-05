import { useEffect, useRef } from 'react'
import * as Cesium from 'cesium'
import type { MapViewState } from '../../types'
import { jetColor } from './layers/WatershedHeatmapLayer'

export interface Bbox { minx: number; miny: number; maxx: number; maxy: number }

interface CesiumViewerProps {
  center: [number, number]
  zoom: number
  layers: MapViewState['layers']
  rectangleDrawMode?: boolean
  onBboxDrawn?: (bbox: Bbox) => void
  heatmapData?: GeoJSON.GeoJsonObject | null
  drawnRectangle?: GeoJSON.Feature<GeoJSON.Polygon> | null
  heatmapMode?: 'area' | 'tc'
}

// Get Cesium Ion token from environment
const CESIUM_ION_TOKEN = import.meta.env.VITE_CESIUM_ION_TOKEN || ''

if (CESIUM_ION_TOKEN && CESIUM_ION_TOKEN !== 'YOUR_CESIUM_ION_TOKEN_HERE') {
  Cesium.Ion.defaultAccessToken = CESIUM_ION_TOKEN
}

// Convert Leaflet zoom to Cesium camera height (approximate)
function zoomToHeight(zoom: number): number {
  return 40000000 / Math.pow(2, zoom)
}

export function CesiumViewer({
  center,
  zoom,
  layers,
  rectangleDrawMode = false,
  onBboxDrawn,
  heatmapData,
  drawnRectangle,
  heatmapMode = 'area',
}: CesiumViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const viewerRef = useRef<Cesium.Viewer | null>(null)
  const handlerRef = useRef<Cesium.ScreenSpaceEventHandler | null>(null)
  const drawingStateRef = useRef<{
    isDrawing: boolean
    startPosition: Cesium.Cartographic | null
    currentEntity: Cesium.Entity | null
  }>({ isDrawing: false, startPosition: null, currentEntity: null })

  // Initialize viewer
  useEffect(() => {
    if (!containerRef.current || viewerRef.current) return

    const viewer = new Cesium.Viewer(containerRef.current, {
      terrainProvider: new Cesium.EllipsoidTerrainProvider(),
      baseLayerPicker: false,
      geocoder: false,
      homeButton: false,
      sceneModePicker: false,
      navigationHelpButton: false,
      animation: false,
      timeline: false,
      fullscreenButton: false,
      vrButton: false,
      selectionIndicator: false,
      infoBox: false,
      requestRenderMode: false,
    })

    // Add default imagery
    viewer.imageryLayers.removeAll()
    viewer.imageryLayers.addImageryProvider(
      new Cesium.OpenStreetMapImageryProvider({
        url: 'https://tile.openstreetmap.org/',
      })
    )

    viewerRef.current = viewer

    // Load world terrain asynchronously
    Cesium.createWorldTerrainAsync({
      requestWaterMask: true,
      requestVertexNormals: true,
    }).then((terrain) => {
      if (viewerRef.current) {
        viewerRef.current.terrainProvider = terrain
      }
    }).catch((error) => {
      console.warn('Failed to load Cesium World Terrain:', error)
    })

    return () => {
      if (handlerRef.current) {
        handlerRef.current.destroy()
        handlerRef.current = null
      }
      if (viewerRef.current) {
        viewerRef.current.destroy()
        viewerRef.current = null
      }
    }
  }, [])

  // Update imagery based on layer selection
  useEffect(() => {
    if (!viewerRef.current) return

    const viewer = viewerRef.current
    viewer.imageryLayers.removeAll()

    if (layers?.imagery) {
      Cesium.ArcGisMapServerImageryProvider.fromUrl(
        'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer'
      ).then((provider) => {
        if (viewerRef.current) {
          viewerRef.current.imageryLayers.addImageryProvider(provider)
        }
      }).catch(() => {
        if (viewerRef.current) {
          viewerRef.current.imageryLayers.addImageryProvider(
            new Cesium.OpenStreetMapImageryProvider({
              url: 'https://tile.openstreetmap.org/',
            })
          )
        }
      })
    } else {
      viewer.imageryLayers.addImageryProvider(
        new Cesium.OpenStreetMapImageryProvider({
          url: 'https://tile.openstreetmap.org/',
        })
      )
    }
  }, [layers?.imagery])

  // Fly to location
  useEffect(() => {
    if (!viewerRef.current) return

    viewerRef.current.camera.flyTo({
      destination: Cesium.Cartesian3.fromDegrees(center[1], center[0], zoomToHeight(zoom)),
      orientation: {
        heading: 0,
        pitch: Cesium.Math.toRadians(-45),
        roll: 0,
      },
      duration: 0,
    })
  }, [center, zoom])

  // Handle rectangle drawing
  useEffect(() => {
    if (!viewerRef.current) return

    const viewer = viewerRef.current
    const scene = viewer.scene

    // Clean up existing handler
    if (handlerRef.current) {
      handlerRef.current.destroy()
      handlerRef.current = null
    }

    if (!rectangleDrawMode || !onBboxDrawn) {
      scene.screenSpaceCameraController.enableRotate = true
      scene.screenSpaceCameraController.enableTranslate = true
      return
    }

    const handler = new Cesium.ScreenSpaceEventHandler(scene.canvas)
    handlerRef.current = handler

    handler.setInputAction((click: { position: Cesium.Cartesian2 }) => {
      const cartesian = viewer.camera.pickEllipsoid(click.position, scene.globe.ellipsoid)
      if (!cartesian) return

      const cartographic = Cesium.Cartographic.fromCartesian(cartesian)
      drawingStateRef.current.startPosition = cartographic
      drawingStateRef.current.isDrawing = true

      scene.screenSpaceCameraController.enableRotate = false
      scene.screenSpaceCameraController.enableTranslate = false
    }, Cesium.ScreenSpaceEventType.LEFT_DOWN)

    handler.setInputAction((movement: { endPosition: Cesium.Cartesian2 }) => {
      const state = drawingStateRef.current
      if (!state.isDrawing || !state.startPosition) return

      const cartesian = viewer.camera.pickEllipsoid(movement.endPosition, scene.globe.ellipsoid)
      if (!cartesian) return

      const cartographic = Cesium.Cartographic.fromCartesian(cartesian)

      const west = Math.min(state.startPosition.longitude, cartographic.longitude)
      const east = Math.max(state.startPosition.longitude, cartographic.longitude)
      const south = Math.min(state.startPosition.latitude, cartographic.latitude)
      const north = Math.max(state.startPosition.latitude, cartographic.latitude)

      const rectangle = Cesium.Rectangle.fromRadians(west, south, east, north)

      if (state.currentEntity) {
        viewer.entities.remove(state.currentEntity)
      }

      state.currentEntity = viewer.entities.add({
        rectangle: {
          coordinates: rectangle,
          material: Cesium.Color.CYAN.withAlpha(0.3),
          outline: true,
          outlineColor: Cesium.Color.CYAN,
          outlineWidth: 2,
          height: 0,
        },
      })
    }, Cesium.ScreenSpaceEventType.MOUSE_MOVE)

    handler.setInputAction((click: { position: Cesium.Cartesian2 }) => {
      const state = drawingStateRef.current
      if (!state.isDrawing || !state.startPosition) return

      const cartesian = viewer.camera.pickEllipsoid(click.position, scene.globe.ellipsoid)
      if (!cartesian) return

      const cartographic = Cesium.Cartographic.fromCartesian(cartesian)

      const west = Math.min(state.startPosition.longitude, cartographic.longitude)
      const east = Math.max(state.startPosition.longitude, cartographic.longitude)
      const south = Math.min(state.startPosition.latitude, cartographic.latitude)
      const north = Math.max(state.startPosition.latitude, cartographic.latitude)

      const bbox = {
        minx: Cesium.Math.toDegrees(west),
        miny: Cesium.Math.toDegrees(south),
        maxx: Cesium.Math.toDegrees(east),
        maxy: Cesium.Math.toDegrees(north),
      }

      const minSize = 0.0001
      if (Math.abs(bbox.maxx - bbox.minx) > minSize && Math.abs(bbox.maxy - bbox.miny) > minSize) {
        onBboxDrawn(bbox)
      }

      if (state.currentEntity) {
        viewer.entities.remove(state.currentEntity)
        state.currentEntity = null
      }
      state.isDrawing = false
      state.startPosition = null

      scene.screenSpaceCameraController.enableRotate = true
      scene.screenSpaceCameraController.enableTranslate = true
    }, Cesium.ScreenSpaceEventType.LEFT_UP)

    return () => {
      if (handlerRef.current) {
        handlerRef.current.destroy()
        handlerRef.current = null
      }
      scene.screenSpaceCameraController.enableRotate = true
      scene.screenSpaceCameraController.enableTranslate = true
    }
  }, [rectangleDrawMode, onBboxDrawn])

  // Render drawn rectangle
  useEffect(() => {
    if (!viewerRef.current) return

    const viewer = viewerRef.current

    // Remove existing rectangle entities (not heatmap ones)
    const toRemove = viewer.entities.values.filter(
      (e) => e.id?.startsWith('drawn-rectangle')
    )
    toRemove.forEach((e) => viewer.entities.remove(e))

    if (drawnRectangle && drawnRectangle.geometry.type === 'Polygon') {
      viewer.entities.add({
        id: 'drawn-rectangle',
        polygon: {
          hierarchy: new Cesium.PolygonHierarchy(
            drawnRectangle.geometry.coordinates[0].map((coord: number[]) =>
              Cesium.Cartesian3.fromDegrees(coord[0], coord[1])
            )
          ),
          material: Cesium.Color.CYAN.withAlpha(0.1),
          outline: true,
          outlineColor: Cesium.Color.CYAN,
          outlineWidth: 2,
          height: 0,
          heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
        },
      })
    }
  }, [drawnRectangle])

  // Render heatmap data
  useEffect(() => {
    if (!viewerRef.current) return

    const viewer = viewerRef.current

    // Remove existing heatmap entities
    const toRemove = viewer.entities.values.filter(
      (e) => e.id?.startsWith('heatmap-')
    )
    toRemove.forEach((e) => viewer.entities.remove(e))

    if (!heatmapData || !('features' in heatmapData) || !Array.isArray(heatmapData.features)) {
      return
    }

    heatmapData.features.forEach((feature: any, index: number) => {
      if (feature.geometry?.type !== 'Polygon') return

      const props = feature.properties || {}
      const jetValue = heatmapMode === 'area' ? props.jet_value_area : props.jet_value_tc
      const colorHex = jetColor(jetValue || 0)
      const cesiumColor = Cesium.Color.fromCssColorString(colorHex).withAlpha(0.7)

      viewer.entities.add({
        id: `heatmap-${index}`,
        polygon: {
          hierarchy: new Cesium.PolygonHierarchy(
            feature.geometry.coordinates[0].map((coord: number[]) =>
              Cesium.Cartesian3.fromDegrees(coord[0], coord[1])
            )
          ),
          material: cesiumColor,
          outline: true,
          outlineColor: Cesium.Color.BLACK.withAlpha(0.5),
          outlineWidth: 1,
          height: 0,
          heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
        },
        description: `
          <div>
            <strong>Watershed Area:</strong> ${props.area_ha?.toFixed(2) || 'N/A'} ha<br/>
            <strong>Time of Concentration:</strong> ${props.tc_min?.toFixed(2) || 'N/A'} min
          </div>
        `,
      })
    })
  }, [heatmapData, heatmapMode])

  return (
    <div
      ref={containerRef}
      data-testid="cesium-viewer"
      className="cesium-viewer"
      style={{ height: '100%', width: '100%' }}
    />
  )
}
