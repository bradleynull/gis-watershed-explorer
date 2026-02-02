declare namespace GeoJSON {
  interface LineString {
    type: 'LineString'
    coordinates: number[][]
  }
  interface Polygon {
    type: 'Polygon'
    coordinates: number[][][]
  }
  interface Feature<G = GeometryObject, P = GeoJsonProperties> {
    type: 'Feature'
    geometry: G
    properties: P
  }
  type GeometryObject = LineString | Polygon | unknown
  type GeoJsonProperties = Record<string, unknown> | null
  interface GeoJsonObject {
    type: string
  }
}
