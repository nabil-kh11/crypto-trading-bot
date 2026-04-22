/* eslint-disable @typescript-eslint/no-explicit-any */
'use client'
import { useEffect, useState } from 'react'

const HOURS = Array.from({ length: 24 }, (_, i) => i)
const DAYS  = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

export default function SignalHeatmap() {
  const [heatmap, setHeatmap] = useState<Record<string, number>>({})
  const [maxVal, setMaxVal] = useState(1)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch('http://localhost:8004/trades?limit=1000&offset=0')
        const data = await res.json()
        const trades = data.trades || []
        const map: Record<string, number> = {}
        trades.forEach((t: any) => {
          const d = new Date(t.executed_at + 'Z')
          const key = `${d.getDay()}-${d.getHours()}`
          map[key] = (map[key] || 0) + 1
        })
        setHeatmap(map)
        setMaxVal(Math.max(...Object.values(map), 1))
      } catch (e) {
        console.error('Heatmap error:', e)
      }
    }
    fetchData()
  }, [])

  const getColor = (val: number) => {
  if (val === 0) return '#111827'
  const intensity = val / maxVal
  if (intensity > 0.66) return '#7c3aed'  // deep purple
  if (intensity > 0.33) return '#a78bfa'  // medium purple
  return '#ddd6fe'                          // light purple
}

const getBorder = (val: number) => {
  if (val === 0) return '1px solid #1f2937'
  const intensity = val / maxVal
  if (intensity > 0.66) return '1px solid #6d28d9'
  if (intensity > 0.33) return '1px solid #8b5cf6'
  return '1px solid #c4b5fd'
}

  return (
    <div className="bg-gray-900 rounded-xl p-6 border border-gray-800 mb-6">
      <div className="flex justify-between items-center mb-4">
        <div>
          <p className="text-white text-sm font-semibold">Signal Activity Heatmap</p>
          <p className="text-gray-500 text-xs mt-0.5">
            Trade frequency by hour and day of week
          </p>
        </div>
        <div className="flex gap-4">
          {[
           { color: '#111827', border: '#1f2937', label: 'None' },
            { color: '#ddd6fe', border: '#c4b5fd', label: 'Low' },
            { color: '#a78bfa', border: '#8b5cf6', label: 'Medium' },
            { color: '#7c3aed', border: '#6d28d9', label: 'High' },
          ].map(({ color, border, label }) => (
            <span key={label} className="flex items-center gap-1.5 text-xs text-gray-400">
              <div style={{
                width: 14, height: 14,
                backgroundColor: color,
                border: `1px solid ${border}`,
                borderRadius: 3
              }} />
              {label}
            </span>
          ))}
        </div>
      </div>

      <div className="w-full">
        {/* Hour labels */}
        <div className="flex mb-2 pl-12">
          {HOURS.map(h => (
            <div key={h} className="flex-1 text-center text-gray-500"
              style={{ fontSize: '10px' }}>
              {h % 3 === 0 ? `${h}h` : ''}
            </div>
          ))}
        </div>

        {/* Grid rows */}
        {DAYS.map((day, di) => (
          <div key={day} className="flex items-center mb-1.5">
            <div className="text-gray-400 text-xs font-medium w-12 text-right pr-3 flex-shrink-0">
              {day}
            </div>
            {HOURS.map(h => {
              const val = heatmap[`${di}-${h}`] || 0
              return (
                <div
                  key={h}
                  className="flex-1 mx-0.5 transition-all duration-200 hover:scale-110 cursor-default"
                  title={`${day} ${h}:00 — ${val} trade${val !== 1 ? 's' : ''}`}
                >
                  <div style={{
                    backgroundColor: getColor(val),
                    border: getBorder(val),
                    borderRadius: '5px',
                    aspectRatio: '1',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '9px',
                    fontWeight: 'bold',
                    color: val > 0 ? 'rgba(255,255,255,0.9)' : 'transparent',
                    boxShadow: val > 0 ? `0 0 6px ${getColor(val)}60` : 'none',
                  }}>
                    {val > 0 ? val : ''}
                  </div>
                </div>
              )
            })}
          </div>
        ))}
      </div>
    </div>
  )
}