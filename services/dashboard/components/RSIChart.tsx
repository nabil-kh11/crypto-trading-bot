/* eslint-disable @typescript-eslint/no-explicit-any */
'use client'
import { useEffect, useState } from 'react'
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS, CategoryScale, LinearScale,
  PointElement, LineElement, Tooltip, Filler, Legend
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler, Legend)

export default function RSIChart({ symbol, color, label }: {
  symbol: string, color: string, label: string
}) {
  const [chartData, setChartData] = useState<any>(null)
  const [currentRSI, setCurrentRSI] = useState<number | null>(null)

  useEffect(() => {
    fetch(`http://localhost:8090/api/market/ohlcv/${symbol}?limit=24`)
      .then(r => r.json())
      .then(data => {
        if (!data || data.length === 0) return
        const rsiValues = data.map((d: any) => d.rsi)
        setCurrentRSI(rsiValues[rsiValues.length - 1])
        setChartData({
          labels: data.map((d: any) => {
            const date = new Date(d.timestamp)
            return date.toLocaleString('fr-TN', {
              timeZone: 'Africa/Tunis',
              hour: '2-digit',
              minute: '2-digit',
              hour12: false
            })
          }),
          datasets: [
            {
              label: 'RSI',
              data: rsiValues,
              borderColor: color,
              backgroundColor: color + '20',
              borderWidth: 2,
              pointRadius: 2,
              fill: false,
              tension: 0.4,
            },
            {
              label: 'Overbought (70)',
              data: Array(data.length).fill(70),
              borderColor: '#ef4444',
              borderWidth: 1,
              borderDash: [5, 5],
              pointRadius: 0,
              fill: false,
            },
            {
              label: 'Oversold (30)',
              data: Array(data.length).fill(30),
              borderColor: '#22c55e',
              borderWidth: 1,
              borderDash: [5, 5],
              pointRadius: 0,
              fill: false,
            }
          ]
        })
      })
  }, [symbol, color])

  const getRSIStatus = (rsi: number) => {
    if (rsi >= 70) return { text: 'Overbought', color: 'text-red-400' }
    if (rsi <= 30) return { text: 'Oversold', color: 'text-green-400' }
    return { text: 'Neutral', color: 'text-yellow-400' }
  }

  const options = {
    responsive: true,
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { color: '#9ca3af', maxTicksLimit: 6 }, grid: { color: '#1f2937' } },
      y: {
        min: 0, max: 100,
        ticks: { color: '#9ca3af' },
        grid: { color: '#1f2937' }
      }
    }
  }

  const status = currentRSI ? getRSIStatus(currentRSI) : null

  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
      <div className="flex justify-between items-center mb-2">
        <p className="text-gray-400 text-sm">{label} RSI (14) — Last 24h</p>
        {currentRSI && status && (
          <div className="text-right">
            <span className={`text-lg font-bold ${status.color}`}>
              {currentRSI.toFixed(1)}
            </span>
            <span className={`text-xs ml-2 ${status.color}`}>{status.text}</span>
          </div>
        )}
      </div>
      {chartData ? <Line data={chartData} options={options} /> : (
        <div className="h-32 flex items-center justify-center text-gray-600">Loading...</div>
      )}
    </div>
  )
}