import { useState } from 'react'

interface LocationInputProps {
  onLoad: (lat: number, lon: number) => void
}

export function LocationInput({ onLoad }: LocationInputProps) {
  const [lat, setLat] = useState('35.2')
  const [lon, setLon] = useState('-80.8')

  const handleLoad = () => {
    const latNum = parseFloat(lat)
    const lonNum = parseFloat(lon)
    if (!Number.isFinite(latNum) || !Number.isFinite(lonNum)) return
    if (latNum < -90 || latNum > 90 || lonNum < -180 || lonNum > 180) return
    onLoad(latNum, lonNum)
  }

  return (
    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
      <label>
        Lat
        <input
          data-testid="lat-input"
          type="text"
          value={lat}
          onChange={(e) => setLat(e.target.value)}
          style={{ width: 80, marginLeft: 4 }}
        />
      </label>
      <label>
        Lon
        <input
          data-testid="lon-input"
          type="text"
          value={lon}
          onChange={(e) => setLon(e.target.value)}
          style={{ width: 80, marginLeft: 4 }}
        />
      </label>
      <button data-testid="load-map" type="button" onClick={handleLoad}>
        Load Map
      </button>
    </div>
  )
}
