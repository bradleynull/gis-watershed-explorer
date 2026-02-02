# Watershed Area and Time of Concentration Analysis

A focused GIS application for computing watershed characteristics across a user-selected region.

## Demo

<div align="center">
  <video src="https://raw.githubusercontent.com/bradleynull/gis-watershed-explorer/main/docs/watershed-app-demo.mp4" controls="controls" style="max-width: 100%;">
    Your browser does not support the video tag. <a href="./docs/watershed-app-demo.mp4">Download the demo video</a>.
  </video>
</div>

*See the application in action: draw a rectangle on the map, compute watershed grids with configurable resolution, and toggle between watershed area and time of concentration heatmaps with real-time statistics.*

## Features

- **Interactive Rectangle Drawing**: Draw a rectangle on the map to define your analysis area
- **Watershed Grid Computation**: Computes watershed area (hectares) and time of concentration (minutes) for a grid of points
- **Dual Heatmap Visualization**: Toggle between watershed area and time of concentration heatmaps
- **Configurable Resolution**: Adjust grid spacing from 50m to 500m for performance/detail trade-off
- **Jet Colormap**: Blue (low values) to red (high values) for intuitive visualization

## Technology Stack

### Backend
- **FastAPI**: REST API
- **NumPy**: Array processing
- **Rasterio**: DEM data handling
- **PyProj**: Geodesic calculations
- **Shapely**: Geometric operations
- **USGS 3DEP**: Elevation data source

### Frontend
- **React + TypeScript**: UI framework
- **Leaflet**: Interactive mapping
- **Vite**: Build tool

## Running the Application

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Backend API will be available at http://127.0.0.1:8000

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at http://localhost:5173

## Usage

1. **Navigate to location**: Enter latitude and longitude, then click "Load Map"
2. **Enable drawing mode**: Check the "Draw watershed heatmap" checkbox
3. **Draw rectangle**: Click and drag on the map to define your analysis area
4. **View results**: The heatmap will automatically compute and display
5. **Toggle display**: Switch between "Watershed Area" and "Time of Concentration" in the side panel
6. **Adjust resolution**: Use the slider to change grid spacing (redraw to apply)

## API Endpoint

### GET /api/hydrology/watershed/grid

Computes watershed area and time of concentration for a grid of points.

**Parameters:**
- `minx`, `miny`, `maxx`, `maxy`: Bounding box (longitude, latitude)
- `grid_spacing_m`: Grid spacing in meters (50-1000, default 100)

**Response:**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": { "type": "Polygon", "coordinates": [...] },
      "properties": {
        "area_ha": 75.66,
        "tc_min": 8.08,
        "jet_value_area": 0.6511,
        "jet_value_tc": 0.72
      }
    }
  ],
  "metadata": {
    "grid_spacing_m": 100,
    "point_count": 25,
    "min_area_ha": 10.5,
    "max_area_ha": 120.3,
    "min_tc_min": 2.1,
    "max_tc_min": 15.8,
    "dem_cell_size_m": 10.2
  }
}
```

## Watershed Computation Methodology

### D8 Flow Direction
Each DEM cell is analyzed to determine the steepest descent direction to one of its 8 neighbors.

### Watershed Delineation
1. **Downstream tracing**: From the grid point, trace flow downstream to find the natural outlet (pour point)
2. **Upstream delineation**: Use breadth-first search to find all cells that drain to the outlet
3. **Area calculation**: Compute geodesic area of watershed polygon using WGS84 ellipsoid

### Time of Concentration (Kirpich Formula)
```
Tc (minutes) = 0.0078 × L^0.77 × S^(-0.385)
```
Where:
- L = longest flow path length (meters)
- S = average slope (rise/run)

## Testing

### Backend Tests
```bash
cd backend
pytest tests/controllers/test_hydrology_api.py::test_watershed_grid_returns_valid_features -v
```

### Frontend Build
```bash
cd frontend
npm run build
```

## Notes

- Grid computation is CPU-intensive for fine resolutions over large areas
- Recommended starting resolution: 100-200m
- DEM data is fetched from USGS 3DEP (falls back to synthetic data if unavailable)
- Each grid point computes its own watershed independently

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
