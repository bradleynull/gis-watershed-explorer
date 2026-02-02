interface QueryPanelProps {
  rectangleDrawMode: boolean
  heatmapMode: 'area' | 'tc'
  onHeatmapModeChange: (mode: 'area' | 'tc') => void
  gridSpacing: number
  onGridSpacingChange: (spacing: number) => void
  heatmapMetadata: Record<string, unknown> | null | undefined
  isLoading: boolean
}

export function QueryPanel({
  rectangleDrawMode,
  heatmapMode,
  onHeatmapModeChange,
  gridSpacing,
  onGridSpacingChange,
  heatmapMetadata,
  isLoading,
}: QueryPanelProps) {
  if (!rectangleDrawMode && !heatmapMetadata) {
    return null
  }

  return (
    <div
      data-testid="query-panel"
      style={{
        position: 'absolute',
        top: 16,
        right: 16,
        background: 'white',
        padding: 16,
        borderRadius: 8,
        boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
        zIndex: 1000,
        minWidth: 280,
        maxWidth: 350,
      }}
    >
      <h3 style={{ margin: '0 0 12px 0', fontSize: 16 }}>Watershed Heatmap</h3>

      {rectangleDrawMode && !heatmapMetadata && !isLoading && (
        <p style={{ margin: 0, fontSize: 14, color: '#666' }}>
          Draw a rectangle on the map to compute watershed area and time of concentration.
        </p>
      )}

      {isLoading && (
        <p style={{ margin: 0, fontSize: 14, color: '#666' }}>
          Computing watersheds...
        </p>
      )}

      {heatmapMetadata && (
        <>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', marginBottom: 8, fontWeight: 600, fontSize: 14 }}>
              Display Mode
            </label>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                <input
                  type="radio"
                  name="heatmap-mode"
                  checked={heatmapMode === 'area'}
                  onChange={() => onHeatmapModeChange('area')}
                />
                <span>Watershed Area (hectares)</span>
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                <input
                  type="radio"
                  name="heatmap-mode"
                  checked={heatmapMode === 'tc'}
                  onChange={() => onHeatmapModeChange('tc')}
                />
                <span>Time of Concentration (minutes)</span>
              </label>
            </div>
          </div>

          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', marginBottom: 8, fontWeight: 600, fontSize: 14 }}>
              Grid Resolution: {gridSpacing}m
            </label>
            <input
              type="range"
              min="50"
              max="500"
              step="50"
              value={gridSpacing}
              onChange={(e) => onGridSpacingChange(Number(e.target.value))}
              style={{ width: '100%' }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: '#666', marginTop: 4 }}>
              <span>Fine (50m)</span>
              <span>Coarse (500m)</span>
            </div>
          </div>

          <div style={{ 
            padding: 12, 
            background: '#f5f5f5', 
            borderRadius: 4,
            fontSize: 13 
          }}>
            <h4 style={{ margin: '0 0 8px 0', fontSize: 14 }}>Statistics</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <div>Grid points: {String(heatmapMetadata.point_count || 0)}</div>
              <div>Grid spacing: {String(heatmapMetadata.grid_spacing_m || 0)}m</div>
              <div>DEM resolution: {String(heatmapMetadata.dem_cell_size_m || 0)}m</div>
              <div style={{ marginTop: 8, fontWeight: 600 }}>
                {heatmapMode === 'area' ? 'Area Range:' : 'Tc Range:'}
              </div>
              {heatmapMode === 'area' ? (
                <>
                  <div>Min: {String(heatmapMetadata.min_area_ha || 0)} ha</div>
                  <div>Max: {String(heatmapMetadata.max_area_ha || 0)} ha</div>
                </>
              ) : (
                <>
                  <div>Min: {String(heatmapMetadata.min_tc_min || 0)} min</div>
                  <div>Max: {String(heatmapMetadata.max_tc_min || 0)} min</div>
                </>
              )}
            </div>
          </div>

          <div style={{ 
            marginTop: 12,
            padding: 8,
            background: '#f0f8ff',
            borderRadius: 4,
            fontSize: 12
          }}>
            <div style={{ fontWeight: 600, marginBottom: 4 }}>Legend</div>
            <div style={{ 
              display: 'flex', 
              height: 20,
              borderRadius: 2,
              overflow: 'hidden',
              marginBottom: 4
            }}>
              <div style={{ flex: 1, background: 'rgb(0,0,255)' }} />
              <div style={{ flex: 1, background: 'rgb(0,255,255)' }} />
              <div style={{ flex: 1, background: 'rgb(0,255,0)' }} />
              <div style={{ flex: 1, background: 'rgb(255,255,0)' }} />
              <div style={{ flex: 1, background: 'rgb(255,0,0)' }} />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Low</span>
              <span>High</span>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
