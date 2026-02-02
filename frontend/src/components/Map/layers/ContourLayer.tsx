import { GeoJSON } from 'react-leaflet'
import L from 'leaflet'

interface ContourLayerProps {
  data: GeoJSON.GeoJsonObject
}

export function ContourLayer({ data }: ContourLayerProps) {
  const style = () => ({ color: '#654', weight: 1, opacity: 0.8 })
  const onEachFeature = (feature: GeoJSON.Feature, layer: L.Layer) => {
    const props = (feature as GeoJSON.Feature<GeoJSON.LineString>).properties
    if (props?.elevation != null) {
      layer.bindTooltip(`${props.elevation} m`, { permanent: false })
    }
  }
  return <GeoJSON data-testid="contour-layer" data={data} style={style} onEachFeature={onEachFeature} />
}
