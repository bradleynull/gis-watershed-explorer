import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'
import 'cesium/Build/Cesium/Widgets/widgets.css'
// Removed leaflet-draw CSS - using native rectangle drawing instead

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
