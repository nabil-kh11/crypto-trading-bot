/* eslint-disable @typescript-eslint/no-explicit-any */
'use client'
import React, { useEffect, useState, useCallback } from 'react'
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS, CategoryScale, LinearScale,
  PointElement, LineElement, Title, Tooltip, Legend, Filler
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

const PortfolioChart = React.memo(function PortfolioChart() {
  const [chartData, setChartData] = useState<any>(null)
  const [allTrades, setAllTrades] = useState<any[]>([])
  const [allBalance, setAllBalance] = useState<any>(null)
  const [startDate, setStartDate] = useState<string>(() => {
    const d = new Date()
    d.setDate(d.getDate() - 7)
    return d.toISOString().split('T')[0]
  })
  const [endDate, setEndDate] = useState<string>(() =>
    new Date().toISOString().split('T')[0]
  )

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [tradesRes, balanceRes] = await Promise.all([
          fetch('http://localhost:8090/api/trade/trades?limit=500&offset=0'),
          fetch('http://localhost:8090/api/trade/balance')
        ])
        const tradesData = await tradesRes.json()
        const balance = await balanceRes.json()
        setAllTrades(tradesData.trades || [])
        setAllBalance(balance)
      } catch (e) {
        console.error('PortfolioChart fetch error:', e)
      }
    }
    fetchData()
  }, [])

 const buildChart = useCallback((trades: any[], balance: any) => {
    if (!balance) return

    const btcPrice = balance.BTC_PRICE || 0
    const ethPrice = balance.ETH_PRICE || 0
    const usdtNow  = balance.USDT || 0
    const btcNow   = balance.BTC || 0
    const ethNow   = balance.ETH || 0
    const currentTotal = usdtNow + (btcNow * btcPrice) + (ethNow * ethPrice)

    const sorted = [...trades].sort((a: any, b: any) =>
      new Date(a.executed_at).getTime() - new Date(b.executed_at).getTime()
    )

    const start = new Date(startDate)
    start.setHours(0, 0, 0, 0)
    const end = new Date(endDate)
    end.setHours(23, 59, 59, 999)

    // Track running quantities
    let btcQty = 0
    let ethQty = 0
    let lastBtcPrice = btcPrice
    let lastEthPrice = ethPrice

    const points: { label: string; value: number }[] = []

    sorted.forEach((trade: any) => {
      const tradeTime = new Date(trade.executed_at)
      const price = trade.price || 0
      const qty = trade.quantity || 0
      const usdt = trade.capital_after || 0

      // Update running quantities
      if (trade.symbol === 'BTC/USDT') {
        if (trade.signal === 'BUY') btcQty += qty
        else if (trade.signal === 'SELL') btcQty = Math.max(0, btcQty - qty)
        lastBtcPrice = price
      }
      if (trade.symbol === 'ETH/USDT') {
        if (trade.signal === 'BUY') ethQty += qty
        else if (trade.signal === 'SELL') ethQty = Math.max(0, ethQty - qty)
        lastEthPrice = price
      }

      // Only plot points within date range
      if (tradeTime >= start && tradeTime <= end) {
        const portfolioValue = usdt + (btcQty * lastBtcPrice) + (ethQty * lastEthPrice)
        const label = tradeTime.toLocaleDateString('en-GB', {
          day: '2-digit', month: '2-digit',
          hour: '2-digit', minute: '2-digit'
        })
        points.push({ label, value: Math.max(0, portfolioValue) })
      }
    })

    // Add current total as last point
    const isToday = endDate === new Date().toISOString().split('T')[0]
    if (isToday) {
      points.push({ label: 'Now', value: currentTotal })
    }

    if (points.length === 0) {
      points.push({ label: 'Now', value: currentTotal })
    }

    setChartData({
      labels: points.map(p => p.label),
      datasets: [{
        label: 'Portfolio Value (USDT + Assets)',
        data: points.map(p => p.value),
        borderColor: '#a855f7',
        backgroundColor: '#a855f720',
        borderWidth: 2,
        pointRadius: 3,
        pointBackgroundColor: '#a855f7',
        fill: true,
        tension: 0.3,
      }]
    })
  }, [startDate, endDate])

  useEffect(() => {
    if (allTrades.length > 0 && allBalance) {
      buildChart(allTrades, allBalance)
    } else if (allBalance) {
      buildChart([], allBalance)
    }
  }, [allTrades, allBalance, buildChart])

  const resetDates = () => {
    const d = new Date()
    d.setDate(d.getDate() - 30)
    setStartDate(d.toISOString().split('T')[0])
    setEndDate(new Date().toISOString().split('T')[0])
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (ctx: any) =>
            `$${ctx.raw.toLocaleString(undefined, { maximumFractionDigits: 2 })}`
        }
      }
    },
    scales: {
      x: { ticks: { color: '#9ca3af', maxTicksLimit: 10 }, grid: { color: '#1f2937' } },
      y: {
        ticks: {
          color: '#9ca3af',
          callback: (val: any) => `$${val.toLocaleString(undefined, { maximumFractionDigits: 0 })}`
        },
        grid: { color: '#1f2937' }
      }
    }
  }

  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800 mb-6">
      <div className="flex justify-between items-center mb-3 flex-wrap gap-2">
        <p className="text-gray-400 text-sm">Portfolio Value Over Time</p>
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-gray-500 text-xs">From:</span>
          <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)}
            className="bg-gray-800 text-gray-300 text-xs rounded px-2 py-1 border border-gray-700" />
          <span className="text-gray-500 text-xs">To:</span>
          <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)}
            className="bg-gray-800 text-gray-300 text-xs rounded px-2 py-1 border border-gray-700" />
          <button onClick={resetDates}
            className="px-2 py-1 text-xs rounded bg-gray-700 text-gray-300 hover:bg-gray-600">
            Reset
          </button>
        </div>
      </div>
      {chartData ? (
        <div style={{ height: '300px', position: 'relative' }}>
          <Line data={chartData} options={options} />
        </div>
      ) : (
        <div className="h-40 flex items-center justify-center text-gray-600">
          Loading portfolio data...
        </div>
      )}
    </div>
  )
})

export default PortfolioChart