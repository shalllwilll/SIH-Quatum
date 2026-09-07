import React from 'react'
import './App.css'

function App() {
  return (
    <div className="driver-app">
      <header className="driver-header">
        <h1>Driver App</h1>
        <p className="badge">Route & Delivery View</p>
      </header>
      <main className="driver-main">
        <div className="card">
          <h2>Assigned Route</h2>
          <p>Driver terminal initialized. Awaiting route dispatch.</p>
        </div>
      </main>
    </div>
  )
}

export default App
