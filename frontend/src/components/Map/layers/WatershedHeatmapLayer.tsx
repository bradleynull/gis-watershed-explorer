import { GeoJSON } from 'react-leaflet'

interface WatershedHeatmapLayerProps {
  data: GeoJSON.FeatureCollection | null
  mode: 'area' | 'tc'
}

// Jet colormap: blue (low) -> cyan -> green -> yellow -> red (high)
export function jetColor(value: number): string {
  // value should be 0-1
  const v = Math.max(0, Math.min(1, value))
  
  if (v < 0.25) {
    // Blue to cyan
    const t = v / 0.25
    const r = 0
    const g = Math.round(t * 255)
    const b = 255
    return `rgb(${r},${g},${b})`
  } else if (v < 0.5) {
    // Cyan to green
    const t = (v - 0.25) / 0.25
    const r = 0
    const g = 255
    const b = Math.round((1 - t) * 255)
    return `rgb(${r},${g},${b})`
  } else if (v < 0.75) {
    // Green to yellow
    const t = (v - 0.5) / 0.25
    const r = Math.round(t * 255)
    const g = 255
    const b = 0
    return `rgb(${r},${g},${b})`
  } else {
    // Yellow to red
    const t = (v - 0.75) / 0.25
    const r = 255
    const g = Math.round((1 - t) * 255)
    const b = 0
    return `rgb(${r},${g},${b})`
  }
}

export function WatershedHeatmapLayer({ data, mode }: WatershedHeatmapLayerProps) {
  if (!data) return null

  return (
    <GeoJSON
      data-testid="watershed-heatmap-layer"
      data={data}
      style={(feature) => {
        if (!feature || !feature.properties) {
          return { fillColor: '#888', fillOpacity: 0.6, color: '#000', weight: 0.5 }
        }

        const jetValue = mode === 'area' 
          ? feature.properties.jet_value_area 
          : feature.properties.jet_value_tc

        const color = jetColor(jetValue || 0)

        return {
          fillColor: color,
          fillOpacity: 0.7,
          color: '#000',
          weight: 0.5,
        }
      }}
      onEachFeature={(feature, layer) => {
        if (feature.properties) {
          const { area_ha, tc_min } = feature.properties
          layer.bindTooltip(
            `Area: ${area_ha.toFixed(2)} ha<br/>Tc: ${tc_min.toFixed(2)} min`,
            { sticky: true }
          )
        }
      }}
    />
  )
}
