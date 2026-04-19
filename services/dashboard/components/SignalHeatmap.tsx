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
          const d = new Date(t.executed_at)
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
    if (val === 0) return '#1f2937'
    const intensity = val / maxVal
    if (intensity > 0.66) return '#22c55e'
    if (intensity > 0.33) return '#eab308'
    return '#3b82f6'
  }

  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800 mb-6">
      <p className="text-gray-400 text-sm mb-1">Signal Activity Heatmap</p>
      <p className="text-gray-600 text-xs mb-3">Trade frequency by hour and day of week</p>
      <div className="overflow-x-auto">
        <table className="text-xs">
          <thead>
            <tr>
              <th className="text-gray-500 pr-2 text-right w-8"></th>
              {HOURS.map(h => (
                <th key={h} className="text-gray-600 text-center px-0.5 w-6">
                  {h % 4 === 0 ? `${h}h` : ''}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {DAYS.map((day, di) => (
              <tr key={day}>
                <td className="text-gray-500 pr-2 text-right">{day}</td>
                {HOURS.map(h => {
                  const val = heatmap[`${di}-${h}`] || 0
                  return (
                    <td key={h} className="px-0.5 py-0.5">
                      <div
                        style={{
                          width: '18px', height: '18px',
                          backgroundColor: getColor(val),
                          borderRadius: '2px'
                        }}
                        title={`${day} ${h}:00 — ${val} trades`}
                      />
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
        <div className="flex gap-3 mt-2">
          <span className="flex items-center gap-1 text-xs text-gray-500">
            <div style={{ width: 12, height: 12, backgroundColor: '#1f2937', borderRadius: 2 }} /> 0
          </span>
          <span className="flex items-center gap-1 text-xs text-gray-500">
            <div style={{ width: 12, height: 12, backgroundColor: '#3b82f6', borderRadius: 2 }} /> Low
          </span>
          <span className="flex items-center gap-1 text-xs text-gray-500">
            <div style={{ width: 12, height: 12, backgroundColor: '#eab308', borderRadius: 2 }} /> Medium
          </span>
          <span className="flex items-center gap-1 text-xs text-gray-500">
            <div style={{ width: 12, height: 12, backgroundColor: '#22c55e', borderRadius: 2 }} /> High
          </span>
        </div>
      </div>
    </div>
  )
}