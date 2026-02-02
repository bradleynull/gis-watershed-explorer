import { GeoJSON } from 'react-leaflet'
import L from 'leaflet'

interface WatershedContourLayerProps {
  data: GeoJSON.GeoJsonObject
}

/**
 * Jet colormap: maps value 0-1 to RGB color (blue -> cyan -> green -> yellow -> red).
 */
function jetColor(value: number): string {
  // Clamp to 0-1
  const v = Math.max(0, Math.min(1, value))
  
  let r: number, g: number, b: number
  
  if (v < 0.125) {
    // Dark blue to blue
    r = 0
    g = 0
    b = 0.5 + v * 4
  } else if (v < 0.375) {
    // Blue to cyan
    r = 0
    g = (v - 0.125) * 4
    b = 1
  } else if (v < 0.625) {
    // Cyan to green to yellow
    r = (v - 0.375) * 4
    g = 1
    b = 1 - (v - 0.375) * 4
  } else if (v < 0.875) {
    // Yellow to red
    r = 1
    g = 1 - (v - 0.625) * 4
    b = 0
  } else {
    // Red to dark red
    r = 1 - (v - 0.875) * 2
    g = 0
    b = 0
  }
  
  const toHex = (c: number) => {
    const hex = Math.round(c * 255).toString(16)
    return hex.length === 1 ? '0' + hex : hex
  }
  
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`
}

export function WatershedContourLayer({ data }: WatershedContourLayerProps) {
  const style = (feature?: GeoJSON.Feature) => {
    const jetValue = feature?.properties?.jet_value ?? 0.5
    return {
      color: jetColor(jetValue),
      weight: 2,
      opacity: 0.9,
    }
  }
  
  const onEachFeature = (feature: GeoJSON.Feature, layer: L.Layer) => {
    const props = feature.properties
    if (props?.elevation != null) {
      layer.bindTooltip(`${props.elevation.toFixed(1)} m`, { permanent: false })
    }
  }
  
  return (
    <div data-testid="watershed-contour-layer">
      <GeoJSON data={data} style={style} onEachFeature={onEachFeature} />
    </div>
  )
}
