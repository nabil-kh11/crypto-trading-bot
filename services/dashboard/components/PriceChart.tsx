/* eslint-disable @typescript-eslint/no-explicit-any */

'use client'
import { useEffect, useState } from 'react'
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS, CategoryScale, LinearScale,
  PointElement, LineElement, Title, Tooltip, Legend, Filler
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

export default function PriceChart({ symbol, color, label }: { symbol: string, color: string, label: string }) {
  const [chartData, setChartData] = useState<any>(null)

  useEffect(() => {
    fetch(`http://localhost:8001/ohlcv/${symbol}?limit=200`)
      .then(r => r.json())
      .then(data => {
        if (!data || data.length === 0) return
        setChartData({
          labels: data.map((d: any) => new Date(d.timestamp).toLocaleTimeString()),
          datasets: [{
            label: `${label} Price`,
            data: data.map((d: any) => d.close),
            borderColor: color,
            backgroundColor: color + '20',
            borderWidth: 2,
            pointRadius: 0,
            fill: true,
            tension: 0.4,
          }]
        })
      })
  }, [symbol, color, label])

  const options = {
    responsive: true,
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { color: '#9ca3af', maxTicksLimit: 6 }, grid: { color: '#1f2937' } },
      y: { ticks: { color: '#9ca3af' }, grid: { color: '#1f2937' } }
    }
  }

  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
      <p className="text-gray-400 text-sm mb-2">{label} Price Chart (last 200 candles)</p>
      {chartData ? <Line data={chartData} options={options} /> : (
        <div className="h-40 flex items-center justify-center text-gray-600">Loading...</div>
      )}
    </div>
  )
}