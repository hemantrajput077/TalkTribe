import { useState } from 'react'

function App() {
  const [apiStatus, setApiStatus] = useState<string>('Not checked')
  const [loading, setLoading] = useState<boolean>(false)

  const checkAPI = async () => {
    setLoading(true)
    try {
      const response = await fetch('http://localhost:8000/health')
      const data = await response.json()
      setApiStatus(`✓ Connected: ${data.status}`)
    } catch (error) {
      setApiStatus('✗ API Unavailable - Make sure backend is running')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white p-8 rounded-2xl shadow-xl max-w-md w-full">
        <div className="text-center mb-6">
          <h1 className="text-4xl font-bold text-indigo-600 mb-2">
            TalkTribe
          </h1>
          <p className="text-gray-600">
            Language Exchange Platform
          </p>
        </div>

        <div className="bg-indigo-50 p-4 rounded-lg mb-6">
          <h2 className="text-sm font-semibold text-indigo-800 mb-2">
            🚀 Milestone 1.1: Setup Complete
          </h2>
          <ul className="text-xs text-indigo-700 space-y-1">
            <li>✓ Docker Environment</li>
            <li>✓ FastAPI Backend</li>
            <li>✓ React Frontend</li>
            <li>✓ PostgreSQL Database</li>
            <li>✓ Redis Cache</li>
          </ul>
        </div>

        <button
          onClick={checkAPI}
          disabled={loading}
          className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-bold py-3 px-4 rounded-lg transition-colors"
        >
          {loading ? 'Checking...' : 'Test API Connection'}
        </button>

        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
          <p className="text-xs text-gray-500 mb-1">API Status:</p>
          <p className="text-sm font-mono text-gray-800">
            {apiStatus}
          </p>
        </div>

        <div className="mt-6 text-center text-xs text-gray-500">
          <p>Next: Milestone 1.2 - Database Models & Migrations</p>
        </div>
      </div>
    </div>
  )
}

export default App
