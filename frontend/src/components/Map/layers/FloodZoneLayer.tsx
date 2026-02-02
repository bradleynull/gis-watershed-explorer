import { GeoJSON } from 'react-leaflet'

interface FloodZoneLayerProps {
  data: GeoJSON.GeoJsonObject
}

export function FloodZoneLayer({ data }: FloodZoneLayerProps) {
  const style = () => ({ color: '#c00', weight: 1, fillColor: '#f88', fillOpacity: 0.3 })
  return <GeoJSON data-testid="flood-zone-layer" data={data} style={style} />
}
