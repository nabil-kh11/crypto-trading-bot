'use client'
import { useEffect, useState } from 'react'

const SERVICES = [
  { name: 'Market Data', url: 'http://localhost:8001/health', port: 8001 },
  { name: 'ML Engine',   url: 'http://localhost:8002/health', port: 8002 },
  { name: 'Sentiment',   url: 'http://localhost:8003/health', port: 8003 },
  { name: 'Order Exec',  url: 'http://localhost:8004/health', port: 8004 },
  { name: 'Chatbot',     url: 'http://localhost:8005/health', port: 8005 },
]

export default function ServiceHealth() {
  const [statuses, setStatuses] = useState<Record<string, boolean>>({})

  useEffect(() => {
    const checkServices = async () => {
      const results: Record<string, boolean> = {}
      await Promise.all(SERVICES.map(async (s) => {
        try {
          const res = await fetch(s.url)
          results[s.name] = res.ok
        } catch {
          results[s.name] = false
        }
      }))
      setStatuses(results)
    }
    checkServices()
    const interval = setInterval(checkServices, 30000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800 mb-6">
      <p className="text-gray-400 text-sm mb-3">Service Health</p>
      <div className="flex gap-4 flex-wrap">
        {SERVICES.map(s => (
          <div key={s.name} className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${
              statuses[s.name] === undefined ? 'bg-gray-500' :
              statuses[s.name] ? 'bg-green-500' : 'bg-red-500'
            }`}></span>
            <span className="text-xs text-gray-300">{s.name}</span>
            <span className={`text-xs ${
              statuses[s.name] === undefined ? 'text-gray-500' :
              statuses[s.name] ? 'text-green-400' : 'text-red-400'
            }`}>
              {statuses[s.name] === undefined ? '...' :
               statuses[s.name] ? 'UP' : 'DOWN'}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}