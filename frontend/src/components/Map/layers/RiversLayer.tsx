import { GeoJSON } from 'react-leaflet'

interface RiversLayerProps {
  data: GeoJSON.GeoJsonObject
}

export function RiversLayer({ data }: RiversLayerProps) {
  const style = () => ({ color: '#06c', weight: 2, opacity: 0.9 })
  return <GeoJSON data-testid="rivers-layer" data={data} style={style} />
}
