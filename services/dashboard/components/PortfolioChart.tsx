/* eslint-disable @typescript-eslint/no-explicit-any */
'use client'
import { useEffect, useState } from 'react'
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS, CategoryScale, LinearScale,
  PointElement, LineElement, Title, Tooltip, Legend, Filler
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

export default function PortfolioChart({ trades }: { trades: any[] }) {
  const [chartData, setChartData] = useState<any>(null)

  useEffect(() => {
    if (!trades || trades.length === 0) return

    const sorted = [...trades].sort((a, b) => 
      new Date(a.executed_at).getTime() - new Date(b.executed_at).getTime()
    )

    let portfolioValue = 10000000
    const points = [{ time: 'Start', value: portfolioValue }]

    sorted.forEach(trade => {
      if (trade.signal === 'BUY') {
        portfolioValue = trade.position_value
      } else if (trade.signal === 'SELL') {
        portfolioValue = trade.capital_after
      }
      points.push({
        time: new Date(trade.executed_at).toLocaleDateString(),
        value: portfolioValue
      })
    })

    setChartData({
      labels: points.map(p => p.time),
      datasets: [{
        label: 'Portfolio Value ($)',
        data: points.map(p => p.value),
        borderColor: '#a855f7',
        backgroundColor: '#a855f720',
        borderWidth: 2,
        pointRadius: 4,
        pointBackgroundColor: '#a855f7',
        fill: true,
        tension: 0.3,
      }]
    })
  }, [trades])

  const options = {
    responsive: true,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (ctx: any) => `$${ctx.raw.toLocaleString()}`
        }
      }
    },
    scales: {
      x: { ticks: { color: '#9ca3af' }, grid: { color: '#1f2937' } },
      y: { 
        ticks: { 
          color: '#9ca3af',
          callback: (val: any) => `$${(val/1000000).toFixed(1)}M`
        }, 
        grid: { color: '#1f2937' } 
      }
    }
  }

  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800 mb-6">
      <p className="text-gray-400 text-sm mb-3">Portfolio Value Over Time</p>
      {chartData ? (
        <Line data={chartData} options={options} />
      ) : (
        <div className="h-40 flex items-center justify-center text-gray-600">
          No trade history yet
        </div>
      )}
    </div>
  )
}