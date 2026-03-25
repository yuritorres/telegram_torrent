import React, { useState, useEffect } from 'react'
import { BrowserRouter as Router } from 'react-router-dom'
import Desktop from './components/Desktop'
import { SystemProvider } from './context/SystemContext'

function App() {
  return (
    <SystemProvider>
      <Router>
        <div className="desktop">
          <Desktop />
        </div>
      </Router>
    </SystemProvider>
  )
}

export default App
