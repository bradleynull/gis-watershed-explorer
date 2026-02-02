import type { MapViewState } from '../../types'

interface LayerPanelProps {
  layers: MapViewState['layers']
  onChange: (layers: MapViewState['layers']) => void
}

export function LayerPanel({ layers, onChange }: LayerPanelProps) {
  const toggle = (key: keyof MapViewState['layers']) => () => {
    onChange({ ...layers, [key]: !layers[key] })
  }

  return (
    <div data-testid="layer-panel" style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
      <label>
        <input type="checkbox" checked={layers.imagery} onChange={toggle('imagery')} />
        Satellite
      </label>
      <label>
        <input type="checkbox" checked={layers.contours} onChange={toggle('contours')} />
        Contours
      </label>
      <label>
        <input type="checkbox" checked={layers.rivers} onChange={toggle('rivers')} />
        Rivers
      </label>
      <label>
        <input type="checkbox" checked={layers.floodZones} onChange={toggle('floodZones')} />
        Flood zones
      </label>
    </div>
  )
}
