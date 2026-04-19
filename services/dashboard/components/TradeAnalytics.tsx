/* eslint-disable @typescript-eslint/no-explicit-any */
'use client'
import { useEffect, useState } from 'react'
import { Bar, Pie } from 'react-chartjs-2'
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement,
  ArcElement, Title, Tooltip, Legend
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend)

export default function TradeAnalytics() {
  const [barData, setBarData] = useState<any>(null)
  const [pieData, setPieData] = useState<any>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch('http://localhost:8004/trades?limit=1000&offset=0')
        const data = await res.json()
        const trades = data.trades || []
        if (trades.length === 0) return

        // Group by day
        const byDay: Record<string, { buy: number, sell: number }> = {}
        trades.forEach((t: any) => {
          const day = new Date(t.executed_at).toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit' })
          if (!byDay[day]) byDay[day] = { buy: 0, sell: 0 }
          if (t.signal === 'BUY') byDay[day].buy++
          else if (t.signal === 'SELL') byDay[day].sell++
        })

        const days = Object.keys(byDay).slice(-7)
        setBarData({
          labels: days,
          datasets: [
            { label: 'BUY', data: days.map(d => byDay[d].buy), backgroundColor: '#22c55e' },
            { label: 'SELL', data: days.map(d => byDay[d].sell), backgroundColor: '#ef4444' },
          ]
        })

        // BTC vs ETH distribution
        const btc = trades.filter((t: any) => t.symbol === 'BTC/USDT').length
        const eth = trades.filter((t: any) => t.symbol === 'ETH/USDT').length
        setPieData({
          labels: ['BTC/USDT', 'ETH/USDT'],
          datasets: [{
            data: [btc, eth],
            backgroundColor: ['#f97316', '#60a5fa'],
            borderWidth: 0,
          }]
        })
      } catch (e) {
        console.error('TradeAnalytics error:', e)
      }
    }
    fetchData()
  }, [])

  const barOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { labels: { color: '#9ca3af' } } },
    scales: {
      x: { ticks: { color: '#9ca3af' }, grid: { color: '#1f2937' } },
      y: { ticks: { color: '#9ca3af' }, grid: { color: '#1f2937' } }
    }
  }

  const pieOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { labels: { color: '#9ca3af' } } }
  }

  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800 mb-6">
      <p className="text-gray-400 text-sm mb-3">Trade Analytics</p>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-gray-500 text-xs mb-2">BUY vs SELL per Day (last 7 days)</p>
          <div style={{ height: '200px' }}>
            {barData ? <Bar data={barData} options={barOptions as any} /> :
              <div className="h-full flex items-center justify-center text-gray-600">Loading...</div>}
          </div>
        </div>
        <div>
          <p className="text-gray-500 text-xs mb-2">BTC vs ETH Distribution</p>
          <div style={{ height: '200px' }}>
            {pieData ? <Pie data={pieData} options={pieOptions as any} /> :
              <div className="h-full flex items-center justify-center text-gray-600">Loading...</div>}
          </div>
        </div>
      </div>
    </div>
  )
}