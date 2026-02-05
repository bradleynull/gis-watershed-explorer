export type ViewMode = '2d' | '3d'

export interface MapViewState {
  center: [number, number]
  zoom: number
  layers: {
    imagery: boolean
    contours: boolean
    rivers: boolean
    floodZones: boolean
  }
}

export interface FlowPathResult {
  type: string
  geometry: { type: string; coordinates: number[][] }
  properties: { distance_m: number; reaches_stream?: boolean }
}

export interface FloodZoneResult {
  zone: string | null
  description: string
}
