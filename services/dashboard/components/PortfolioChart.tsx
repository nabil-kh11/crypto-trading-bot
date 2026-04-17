/* eslint-disable @typescript-eslint/no-explicit-any */
'use client'
import { useEffect, useState, useRef } from 'react'
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS, CategoryScale, LinearScale,
  PointElement, LineElement, Title, Tooltip, Legend, Filler
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

export default function PortfolioChart() {
  const [chartData, setChartData] = useState<any>(null)
  const [initialCapital, setInitialCapital] = useState<number>(0)
  const [startDate, setStartDate] = useState<string>(() => {
    const d = new Date()
    d.setDate(d.getDate() - 7)
    return d.toISOString().split('T')[0]
  })
  const [endDate, setEndDate] = useState<string>(() =>
    new Date().toISOString().split('T')[0]
  )
  const chartRef = useRef<any>(null)

  const resetDates = () => {
    const d = new Date()
    d.setDate(d.getDate() - 7)
    setStartDate(d.toISOString().split('T')[0])
    setEndDate(new Date().toISOString().split('T')[0])
  }

  const buildChart = async () => {
    try {
      const [tradesRes, balanceRes] = await Promise.all([
        fetch('http://localhost:8004/trades?limit=1000&offset=0'),
        fetch('http://localhost:8004/balance')
      ])
      const tradesData = await tradesRes.json()
      const balance    = await balanceRes.json()

      const trades = tradesData.trades || []
      if (trades.length === 0) return

      const btcPrice = balance.BTC_PRICE || 0
      const ethPrice = balance.ETH_PRICE || 0
      const usdtNow  = balance.USDT || 0
      const btcNow   = balance.BTC || 0
      const ethNow   = balance.ETH || 0
      const currentTotal = usdtNow + (btcNow * btcPrice) + (ethNow * ethPrice)

      const allSorted = [...trades].sort((a: any, b: any) =>
        new Date(a.executed_at).getTime() - new Date(b.executed_at).getTime()
      )

      const firstBuy = allSorted.find((t: any) => t.signal === 'BUY' && t.capital_before > 0)
      const startingUsdt = firstBuy ? firstBuy.capital_before : usdtNow
      const startingBtc  = 1.0
      const startingEth  = 1.0
      const firstPrice   = allSorted[0]?.price || btcPrice
      const startingTotal = startingUsdt + (startingBtc * firstPrice) + (startingEth * firstPrice)
      setInitialCapital(startingTotal)

      let usdt   = startingUsdt
      let btcQty = startingBtc
      let ethQty = startingEth

      const allPoints: { time: Date; value: number }[] = []

      allSorted.forEach((trade: any) => {
        if (trade.signal === 'BUY') {
          usdt = trade.capital_after
          if (trade.symbol === 'BTC/USDT') btcQty += trade.quantity
          if (trade.symbol === 'ETH/USDT') ethQty += trade.quantity
        } else if (trade.signal === 'SELL') {
          usdt = trade.capital_after
          if (trade.symbol === 'BTC/USDT') btcQty = Math.max(0, btcQty - trade.quantity)
          if (trade.symbol === 'ETH/USDT') ethQty = Math.max(0, ethQty - trade.quantity)
        }
        const portfolioValue = usdt + (btcQty * trade.price) + (ethQty * trade.price)
        allPoints.push({ time: new Date(trade.executed_at), value: Math.max(0, portfolioValue) })
      })

      const start = new Date(startDate)
      start.setHours(0, 0, 0, 0)
      const end = new Date(endDate)
      end.setHours(23, 59, 59, 999)

      let capitalAtStart = startingTotal
      for (const pt of allPoints) {
        if (pt.time < start) capitalAtStart = pt.value
        else break
      }

      const filtered = allPoints.filter(p => p.time >= start && p.time <= end)
      const isToday = endDate === new Date().toISOString().split('T')[0]

      const points = [
        { label: startDate, value: capitalAtStart },
        ...filtered.map(p => ({
          label: p.time.toLocaleDateString('en-GB', {
            day: '2-digit', month: '2-digit',
            hour: '2-digit', minute: '2-digit'
          }),
          value: p.value
        })),
        ...(isToday ? [{ label: 'Now', value: currentTotal }] : [])
      ]

      setChartData({
        labels: points.map(p => p.label),
        datasets: [{
          label: 'Portfolio Value ($)',
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
    } catch (e) {
      console.error('PortfolioChart error:', e)
    }
  }

  // Only rebuild when dates change or on mount
  useEffect(() => {
    buildChart()
  }, [startDate, endDate])

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
      x: {
        ticks: { color: '#9ca3af', maxTicksLimit: 10 },
        grid: { color: '#1f2937' }
      },
      y: {
        ticks: {
          color: '#9ca3af',
          callback: (val: any) =>
            `$${val.toLocaleString(undefined, { maximumFractionDigits: 0 })}`
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
          <input
            type="date"
            value={startDate}
            onChange={e => setStartDate(e.target.value)}
            className="bg-gray-800 text-gray-300 text-xs rounded px-2 py-1 border border-gray-700"
          />
          <span className="text-gray-500 text-xs">To:</span>
          <input
            type="date"
            value={endDate}
            onChange={e => setEndDate(e.target.value)}
            className="bg-gray-800 text-gray-300 text-xs rounded px-2 py-1 border border-gray-700"
          />
          <button
            onClick={resetDates}
            className="px-2 py-1 text-xs rounded bg-gray-700 text-gray-300 hover:bg-gray-600"
          >
            Reset
          </button>
          {initialCapital > 0 && (
            <span className="text-gray-500 text-xs">
              Start: ${initialCapital.toLocaleString(undefined, { maximumFractionDigits: 0 })}
            </span>
          )}
        </div>
      </div>
      {chartData ? (
        <div style={{ height: '300px', position: 'relative' }}>
          <Line ref={chartRef} data={chartData} options={options} />
        </div>
      ) : (
        <div className="h-40 flex items-center justify-center text-gray-600">
          Loading portfolio data...
        </div>
      )}
    </div>
  )
}