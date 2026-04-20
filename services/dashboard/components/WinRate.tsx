/* eslint-disable @typescript-eslint/no-explicit-any */
'use client'
import { useEffect, useState } from 'react'

function calculatePositionPnL(trades: any[]) {
  const sorted = [...trades].sort((a, b) =>
    new Date(a.executed_at).getTime() - new Date(b.executed_at).getTime()
  )

  const symbols = ['BTC/USDT', 'ETH/USDT']
  const results: any[] = []

  symbols.forEach(symbol => {
    const symTrades = sorted.filter(t => t.symbol === symbol)

    let position = 0
    let totalCost = 0
    let lastBuyTime: string | null = null

    symTrades.forEach(trade => {
      if (trade.signal === 'BUY') {
        totalCost += trade.price * trade.quantity
        position += trade.quantity
        lastBuyTime = trade.executed_at
      } else if (trade.signal === 'SELL' && position > 0) {
        const avgCost = position > 0 ? totalCost / position : 0
        const sellQty = Math.min(trade.quantity, position)
        const pnl = (trade.price - avgCost) * sellQty
        const holdHours = lastBuyTime
          ? (new Date(trade.executed_at).getTime() - new Date(lastBuyTime).getTime()) / 3600000
          : 0

        results.push({
          symbol,
          sellPrice: trade.price,
          buyPrice: avgCost,
          quantity: sellQty,
          pnl,
          holdHours,
          profitable: pnl > 0,
          executed_at: trade.executed_at
        })

        const costReduced = avgCost * sellQty
        totalCost -= costReduced
        position -= sellQty
        if (position < 0.000001) {
          position = 0
          totalCost = 0
        }
      }
    })
  })

  return results
}

export default function WinRate() {
  const [stats, setStats] = useState<any>(null)

  useEffect(() => {
    const fetchTrades = async () => {
      try {
        const res = await fetch('http://localhost:8004/trades?limit=1000&offset=0')
        const data = await res.json()
        const trades = data.trades || []
        if (trades.length === 0) return

        const buys  = trades.filter((t: any) => t.signal === 'BUY')
        const sells = trades.filter((t: any) => t.signal === 'SELL')

        const matched = calculatePositionPnL(trades)
        const wins = matched.filter(t => t.profitable).length
        const winRate = matched.length > 0
          ? (wins / matched.length * 100).toFixed(1) : 'N/A'

        const totalVolume = trades.reduce((s: number, t: any) =>
          s + (t.price * t.quantity || 0), 0)

        const avgConf = trades.reduce((s: number, t: any) =>
          s + (t.confidence || 0), 0) / trades.length

        setStats({
          totalTrades: trades.length,
          buys: buys.length,
          sells: sells.length,
          winRate,
          totalVolume,
          avgConf: avgConf.toFixed(1),
        })
      } catch (e) {
        console.error('WinRate fetch error:', e)
      }
    }

    fetchTrades()
    const interval = setInterval(fetchTrades, 60000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800 mb-6">
      <p className="text-gray-400 text-sm mb-3">Trading Statistics</p>
      {stats ? (
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-gray-800 rounded-lg p-3 text-center">
            <p className="text-gray-500 text-xs">Total Trades</p>
            <p className="text-white text-xl font-bold">{stats.totalTrades}</p>
            <p className="text-gray-500 text-xs">{stats.buys}B / {stats.sells}S</p>
          </div>
          <div className="bg-gray-800 rounded-lg p-3 text-center">
            <p className="text-gray-500 text-xs">Win Rate</p>
            <p className={`text-xl font-bold ${
              stats.winRate === 'N/A' ? 'text-gray-400' :
              parseFloat(stats.winRate) >= 50 ? 'text-green-400' : 'text-red-400'
            }`}>{stats.winRate}{stats.winRate !== 'N/A' ? '%' : ''}</p>
            <p className="text-gray-500 text-xs">Position matched</p>
          </div>
          <div className="bg-gray-800 rounded-lg p-3 text-center">
            <p className="text-gray-500 text-xs">Avg Confidence</p>
            <p className="text-blue-400 text-xl font-bold">{stats.avgConf}%</p>
            <p className="text-gray-500 text-xs">ML model confidence</p>
          </div>
          <div className="bg-gray-800 rounded-lg p-3 text-center col-span-2">
            <p className="text-gray-500 text-xs">Total Volume Traded</p>
            <p className="text-purple-400 text-lg font-bold">
              ${stats.totalVolume > 1000000
                ? (stats.totalVolume / 1000000).toFixed(2) + 'M'
                : stats.totalVolume.toLocaleString(undefined, { maximumFractionDigits: 0 })}
            </p>
            <p className="text-gray-500 text-xs">Testnet paper trading</p>
          </div>
          <div className="bg-gray-800 rounded-lg p-3 text-center">
            <p className="text-gray-500 text-xs">Exchange</p>
            <p className="text-green-400 text-sm font-bold">Testnet</p>
            <p className="text-gray-500 text-xs">Binance ✓</p>
          </div>
        </div>
      ) : (
        <div className="text-center text-gray-600 py-4">Loading stats...</div>
      )}
    </div>
  )
}