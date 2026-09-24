import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [status, setStatus] = useState<string>('checking...')
  const [apiUrl] = useState<string>(import.meta.env.VITE_API_URL || 'http://localhost:8000')

  useEffect(() => {
    // Check if backend is running
    fetch(`${apiUrl}/health`)
      .then(res => res.json())
      .then(data => {
        setStatus(`Backend online - ${data.environment}`)
      })
      .catch(() => {
        setStatus('Backend offline - start with: cd backend && python -m uvicorn app.main:app --reload')
      })
  }, [apiUrl])

  return (
    <div className="App">
      <div className="container">
        <h1>🤖 AI Chief of Staff</h1>
        <p>Voice-first AI partner for real estate agents</p>

        <div className="status-box">
          <p><strong>Status:</strong> {status}</p>
        </div>

        <section className="getting-started">
          <h2>Getting Started</h2>

          <div className="step">
            <h3>1. Backend Setup</h3>
            <p>Start the FastAPI server:</p>
            <code>cd backend && python -m uvicorn app.main:app --reload</code>
          </div>

          <div className="step">
            <h3>2. Environment Variables</h3>
            <p>Copy .env.example to .env and fill in your API keys:</p>
            <code>cp .env.example .env</code>
          </div>

          <div className="step">
            <h3>3. Database</h3>
            <p>Apply Supabase migrations:</p>
            <code>supabase push</code>
          </div>

          <div className="step">
            <h3>4. Frontend</h3>
            <p>This app is running on port 5173</p>
          </div>
        </section>

        <section className="next-steps">
          <h2>Next Steps</h2>
          <ul>
            <li>Set up Supabase project and get API keys</li>
            <li>Get Anthropic and OpenAI API keys</li>
            <li>Configure Gmail OAuth for email integration</li>
            <li>Set up Twilio for voice calls</li>
            <li>Implement the morning brief scheduler (Layer 3)</li>
            <li>Build agent routers (Layer 4)</li>
            <li>Add voice loop (Layer 5)</li>
          </ul>
        </section>

        <section className="documentation">
          <h2>Documentation</h2>
          <ul>
            <li><a href="./docs/01-BRD-PRD.md">Business & Product Requirements</a></li>
            <li><a href="./docs/02-TRD.md">Technical Requirements & Build Order</a></li>
            <li><a href="./docs/03-Marketing-Sales-Plan.md">Marketing & Sales</a></li>
            <li><a href="./README.md">README</a></li>
          </ul>
        </section>
      </div>
    </div>
  )
}

export default App
