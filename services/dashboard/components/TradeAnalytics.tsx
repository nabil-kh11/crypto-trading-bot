/* eslint-disable @typescript-eslint/no-explicit-any */
'use client'
import { useEffect, useState } from 'react'
import { Bar, Doughnut } from 'react-chartjs-2'
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement,
  ArcElement, Title, Tooltip, Legend
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend)

export default function TradeAnalytics() {
  const [barData, setBarData] = useState<any>(null)
  const [donutData, setDonutData] = useState<any>(null)
  const [stats, setStats] = useState<any>(null)

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
          const day = new Date(t.executed_at + 'Z').toLocaleDateString('fr-TN', {
            timeZone: 'Africa/Tunis', day: '2-digit', month: '2-digit'
          })
          if (!byDay[day]) byDay[day] = { buy: 0, sell: 0 }
          if (t.signal === 'BUY') byDay[day].buy++
          else if (t.signal === 'SELL') byDay[day].sell++
        })

        const days = Object.keys(byDay).slice(-7)
        setBarData({
          labels: days,
          datasets: [
            {
              label: 'BUY',
              data: days.map(d => byDay[d].buy),
              backgroundColor: 'rgba(6, 182, 212, 0.8)',
              borderColor: '#0891b2',
              borderWidth: 1,
              borderRadius: 4,
            },
            {
              label: 'SELL',
              data: days.map(d => byDay[d].sell),
              backgroundColor: 'rgba(244, 63, 94, 0.8)',
              borderColor: '#e11d48',
              borderWidth: 1,
              borderRadius: 4,
            },
          ]
        })

        // BTC vs ETH distribution
        const btc = trades.filter((t: any) => t.symbol === 'BTC/USDT').length
        const eth = trades.filter((t: any) => t.symbol === 'ETH/USDT').length
        setDonutData({
          labels: ['BTC/USDT', 'ETH/USDT'],
          datasets: [{
            data: [btc, eth],
            backgroundColor: ['rgba(168, 85, 247, 0.85)', 'rgba(251, 191, 36, 0.85)'],
            borderColor: ['#9333ea', '#f59e0b'],
            borderWidth: 2,
            hoverOffset: 8,
          }]
        })

        // Quick stats
        const buys  = trades.filter((t: any) => t.signal === 'BUY').length
        const sells = trades.filter((t: any) => t.signal === 'SELL').length
        const avgConf = trades.reduce((s: number, t: any) => s + (t.confidence || 0), 0) / trades.length
        setStats({ buys, sells, total: trades.length, avgConf: avgConf.toFixed(1), btc, eth })
      } catch (e) {
        console.error('TradeAnalytics error:', e)
      }
    }
    fetchData()
  }, [])

  const barOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: { color: '#9ca3af', font: { size: 11 }, padding: 16 }
      },
      tooltip: {
        backgroundColor: '#1f2937',
        titleColor: '#f9fafb',
        bodyColor: '#9ca3af',
        borderColor: '#374151',
        borderWidth: 1,
      }
    },
    scales: {
      x: {
        ticks: { color: '#6b7280', font: { size: 11 } },
        grid: { color: '#1f2937' },
        border: { color: '#374151' }
      },
      y: {
        ticks: { color: '#6b7280', font: { size: 11 } },
        grid: { color: '#1f2937' },
        border: { color: '#374151' }
      }
    }
  }

  const donutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '65%',
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: {
          color: '#9ca3af',
          font: { size: 11 },
          padding: 16,
          usePointStyle: true,
          pointStyleWidth: 10,
        }
      },
      tooltip: {
        backgroundColor: '#1f2937',
        titleColor: '#f9fafb',
        bodyColor: '#9ca3af',
        borderColor: '#374151',
        borderWidth: 1,
        callbacks: {
          label: (ctx: any) => ` ${ctx.label}: ${ctx.raw} trades (${((ctx.raw / (stats?.total || 1)) * 100).toFixed(1)}%)`
        }
      }
    }
  }

  return (
    <div className="bg-gray-900 rounded-xl p-5 border border-gray-800 mb-6">
      <div className="flex justify-between items-center mb-4">
        <p className="text-white text-sm font-semibold">Trade Analytics</p>
        {stats && (
          <div className="flex gap-4 text-xs">
            <span className="text-green-400 font-medium">{stats.buys} BUY</span>
            <span className="text-red-400 font-medium">{stats.sells} SELL</span>
            <span className="text-blue-400 font-medium">{stats.avgConf}% avg conf</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Bar chart - takes 2/3 width */}
        <div className="col-span-2">
          <p className="text-gray-500 text-xs mb-2 font-medium uppercase tracking-wide">
            BUY vs SELL — Last 7 Days
          </p>
          <div style={{ height: '220px' }}>
            {barData
              ? <Bar data={barData} options={barOptions as any} />
              : <div className="h-full flex items-center justify-center text-gray-600 text-sm">Loading...</div>
            }
          </div>
        </div>

        {/* Donut chart - takes 1/3 width */}
        <div>
          <p className="text-gray-500 text-xs mb-2 font-medium uppercase tracking-wide">
            Symbol Distribution
          </p>
          <div style={{ height: '220px', position: 'relative' }}>
            {donutData ? (
              <>
                <Doughnut data={donutData} options={donutOptions as any} />
                {/* Center label */}
                {stats && (
                  <div style={{
                    position: 'absolute',
                    top: '40%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    textAlign: 'center',
                    pointerEvents: 'none'
                  }}>
                    <p className="text-white font-bold text-lg">{stats.total}</p>
                    <p className="text-gray-500 text-xs">trades</p>
                  </div>
                )}
              </>
            ) : (
              <div className="h-full flex items-center justify-center text-gray-600 text-sm">Loading...</div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}