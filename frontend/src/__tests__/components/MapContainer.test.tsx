import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MapContainer } from '../../components/Map/MapContainer'

const mockMap = {
  setView: vi.fn(),
  getBounds: () => ({ getWest: () => -81, getSouth: () => 35, getEast: () => -80, getNorth: () => 36 }),
  on: vi.fn(),
  off: vi.fn(),
}

vi.mock('react-leaflet', () => ({
  MapContainer: ({ children }: { children: React.ReactNode }) => <div data-testid="map-container">{children}</div>,
  TileLayer: () => null,
  useMap: () => mockMap,
  GeoJSON: () => null,
}))

describe('MapContainer', () => {
  it('renders map container', () => {
    render(
      <MapContainer
        center={[35.2, -80.8]}
        zoom={14}
        layers={{ imagery: false, contours: false, rivers: false, floodZones: false }}
      />
    )
    expect(screen.getByTestId('map-container')).toBeInTheDocument()
  })
})
