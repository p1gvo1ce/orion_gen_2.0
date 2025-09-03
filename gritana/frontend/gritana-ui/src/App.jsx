import { useEffect, useState } from 'react'
import LogTable from './components/LogTable'

export default function App() {
  const [showSplash, setShowSplash] = useState(true)

  useEffect(() => {
    const timer = setTimeout(() => setShowSplash(false), 2000)
    return () => clearTimeout(timer)
  }, [])

  return (
    <div className="min-h-screen bg-black text-green-400">
      {showSplash ? (
        <div className="flex items-center justify-center h-screen w-screen animate-fadeout">
          <img
            src="/src/assets/gritana-logo.png"
            alt="GRITANA Logo"
            className="w-full h-full object-contain p-8"
          />
        </div>
      ) : (
        <div className="p-8">
          <LogTable />
        </div>
      )}
    </div>
  )
}
