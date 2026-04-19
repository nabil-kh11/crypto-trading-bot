/* eslint-disable @typescript-eslint/no-explicit-any */
'use client'
import { useEffect, useState } from 'react'

export default function LiveActivityFeed() {
  const [activities, setActivities] = useState<any[]>([])

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [tradesRes, signalsRes] = await Promise.all([
          fetch('http://localhost:8004/trades?limit=10&offset=0'),
          fetch('http://localhost:8004/signals?limit=10')
        ])
        const tradesData  = await tradesRes.json()
        const signalsData = await signalsRes.json()

        const trades  = (tradesData.trades || []).map((t: any) => ({ ...t, type: 'TRADE' }))
        const signals = (signalsData.signals || []).map((s: any) => ({ ...s, type: 'SIGNAL', executed_at: s.created_at }))

        const combined = [...trades, ...signals]
          .sort((a, b) => new Date(b.executed_at).getTime() - new Date(a.executed_at).getTime())
          .slice(0, 15)

        setActivities(combined)
      } catch (e) {
        console.error('LiveFeed error:', e)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 10000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800 mb-6">
      <div className="flex justify-between items-center mb-3">
        <p className="text-gray-400 text-sm">Live Activity Feed</p>
        <span className="text-xs text-green-400 animate-pulse">● Live</span>
      </div>
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {activities.length === 0 ? (
          <p className="text-gray-600 text-xs text-center py-4">No activity yet</p>
        ) : activities.map((a, i) => (
          <div key={i} className="flex items-center justify-between bg-gray-800 rounded-lg px-3 py-2">
            <div className="flex items-center gap-2">
              <span className={`text-xs font-bold px-1.5 py-0.5 rounded ${
                a.type === 'TRADE'
                  ? a.signal === 'BUY' ? 'bg-green-900 text-green-400'
                  : a.signal === 'SELL' ? 'bg-red-900 text-red-400'
                  : 'bg-yellow-900 text-yellow-400'
                  : 'bg-blue-900 text-blue-400'
              }`}>
                {a.type === 'TRADE' ? a.signal : 'SIG'}
              </span>
              <span className="text-gray-300 text-xs">{a.symbol}</span>
              {a.price && (
                <span className="text-gray-500 text-xs">${a.price?.toLocaleString()}</span>
              )}
              {a.confidence && (
                <span className="text-gray-600 text-xs">{a.confidence?.toFixed(1)}%</span>
              )}
            </div>
            <span className="text-gray-600 text-xs">
              {new Date(a.executed_at).toLocaleTimeString()}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}