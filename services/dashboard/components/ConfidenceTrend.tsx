/* eslint-disable @typescript-eslint/no-explicit-any */
'use client'
import { useEffect, useState } from 'react'
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS, CategoryScale, LinearScale,
  PointElement, LineElement, Tooltip, Filler
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler)

export default function ConfidenceTrend({ symbol, color }: {
  symbol: string, color: string
}) {
  const [chartData, setChartData] = useState<any>(null)
  const [avgConf, setAvgConf] = useState<number | null>(null)

  useEffect(() => {
    fetch(`http://localhost:8004/signals?symbol=${symbol}&limit=50`)
      .then(r => r.json())
      .then(data => {
        const signals = data.signals || []
        if (signals.length === 0) return

        const recent = signals.slice(0, 24).reverse()
        const avg = recent.reduce((s: number, x: any) => s + x.confidence, 0) / recent.length
        setAvgConf(avg)

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
          datasets: [
            {
              label: 'Confidence %',
              data: recent.map((s: any) => s.confidence),
              borderColor: color,
              backgroundColor: color + '20',
              borderWidth: 2,
              pointRadius: 2,
              fill: true,
              tension: 0.4,
            },
            {
              label: 'Min threshold (50%)',
              data: Array(recent.length).fill(50),
              borderColor: '#6b7280',
              borderWidth: 1,
              borderDash: [5, 5],
              pointRadius: 0,
              fill: false,
            }
          ]
        })
      })
  }, [symbol, color])

  const options = {
    responsive: true,
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { color: '#9ca3af', maxTicksLimit: 6 }, grid: { color: '#1f2937' } },
      y: {
        min: 0, max: 100,
        ticks: {
          color: '#9ca3af',
          callback: (val: any) => val + '%'
        },
        grid: { color: '#1f2937' }
      }
    }
  }

  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
      <div className="flex justify-between items-center mb-2">
        <p className="text-gray-400 text-sm">
          {symbol.replace('/USDT', '')} Confidence Trend
        </p>
        {avgConf && (
          <span className="text-white text-sm font-bold">
            Avg: {avgConf.toFixed(1)}%
          </span>
        )}
      </div>
      {chartData ? <Line data={chartData} options={options} /> : (
        <div className="h-32 flex items-center justify-center text-gray-600">
          No data yet
        </div>
      )}
    </div>
  )
}