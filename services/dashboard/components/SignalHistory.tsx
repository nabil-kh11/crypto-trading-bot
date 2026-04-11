/* eslint-disable @typescript-eslint/no-explicit-any */
'use client'
import { useEffect, useState } from 'react'
import { Bar } from 'react-chartjs-2'
import {
  Chart as ChartJS, CategoryScale, LinearScale,
  BarElement, Tooltip, Legend
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend)

export default function SignalHistory({ symbol }: { symbol: string }) {
  const [chartData, setChartData] = useState<any>(null)
  const [stats, setStats] = useState<any>(null)

  useEffect(() => {
    fetch(`http://localhost:8090/api/trade/signals?symbol=${symbol}&limit=200`)
      .then(r => r.json())
      .then(data => {
        const signals = data.signals || []
        if (signals.length === 0) return

        const buy  = signals.filter((s: any) => s.signal === 'BUY').length
        const sell = signals.filter((s: any) => s.signal === 'SELL').length
        const hold = signals.filter((s: any) => s.signal === 'HOLD').length
        const total = signals.length

        setStats({ buy, sell, hold, total })

        // Last 24 signals for chart
        const recent = signals.slice(0, 24).reverse()
        setChartData({
          labels: recent.map((s: any) => {
            const date = new Date(s.created_at)
            return date.toLocaleString('fr-TN', {
              timeZone: 'Africa/Tunis',
              hour: '2-digit',
              minute: '2-digit',
              hour12: false
            })
          }),
          datasets: [{
            label: 'Signal',
           data: recent.map((s: any) =>
  s.signal === 'BUY' ? 3 : s.signal === 'SELL' ? 1 : 2
),
backgroundColor: recent.map((s: any) =>
  s.signal === 'BUY' ? '#22c55e80' :
  s.signal === 'SELL' ? '#ef444480' : '#eab30820'
),
borderColor: recent.map((s: any) =>
  s.signal === 'BUY' ? '#22c55e' :
  s.signal === 'SELL' ? '#ef4444' : '#eab308'
),
            borderWidth: 1,
          }]
        })
      })
  }, [symbol])

  const options = {
    responsive: true,
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { color: '#9ca3af', maxTicksLimit: 6 }, grid: { color: '#1f2937' } },
      y: {
  min: 0, max: 4,
  ticks: {
    color: '#9ca3af',
    callback: (val: any) => 
      val === 3 ? 'BUY' : val === 2 ? 'HOLD' : val === 1 ? 'SELL' : ''
  },
  grid: { color: '#1f2937' }
}
    }
  }

  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
      <p className="text-gray-400 text-sm mb-2">
        {symbol.replace('/USDT', '')} Signal History
      </p>
      {stats && (
        <div className="flex gap-4 mb-3 text-xs">
          <span className="text-green-400">▲ BUY: {stats.buy}</span>
          <span className="text-red-400">▼ SELL: {stats.sell}</span>
          <span className="text-yellow-400">— HOLD: {stats.hold}</span>
          <span className="text-gray-500">Total: {stats.total}</span>
        </div>
      )}
      {chartData ? <Bar data={chartData} options={options as any} /> : (
        <div className="h-32 flex items-center justify-center text-gray-600">
          {stats === null ? 'Loading...' : 'No signal data yet'}
        </div>
      )}
    </div>
  )
}