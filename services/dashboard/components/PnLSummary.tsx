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

export default function PnLSummary() {
  const [stats, setStats] = useState<any>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [tradesRes, balanceRes] = await Promise.all([
          fetch('http://localhost:8004/trades?limit=1000&offset=0'),
          fetch('http://localhost:8004/balance')
        ])
        const tradesData = await tradesRes.json()
        const balance = await balanceRes.json()
        const trades = tradesData.trades || []
        if (trades.length === 0) return

        const matched = calculatePositionPnL(trades)

        const totalPnL = matched.reduce((s, t) => s + t.pnl, 0)

        const bestTrade  = matched.reduce((best, t) =>
          t.pnl > (best?.pnl ?? -Infinity) ? t : best, null)
        const worstTrade = matched.reduce((worst, t) =>
          t.pnl < (worst?.pnl ?? Infinity) ? t : worst, null)

        const btcMatched = matched.filter(t => t.symbol === 'BTC/USDT')
        const ethMatched = matched.filter(t => t.symbol === 'ETH/USDT')
        const btcWins = btcMatched.filter(t => t.profitable).length
        const ethWins = ethMatched.filter(t => t.profitable).length

        const holdTimes = matched.map(t => t.holdHours).filter(h => h > 0)
        const avgHoldTime = holdTimes.length > 0
          ? holdTimes.reduce((s, h) => s + h, 0) / holdTimes.length
          : 0

        const totalPortfolio = (balance.USDT || 0) +
          (balance.BTC || 0) * (balance.BTC_PRICE || 0) +
          (balance.ETH || 0) * (balance.ETH_PRICE || 0)

        setStats({
          totalPnL,
          totalPortfolio,
          bestTrade,
          worstTrade,
          btcWinRate: btcMatched.length > 0
            ? (btcWins / btcMatched.length * 100).toFixed(1) : 'N/A',
          ethWinRate: ethMatched.length > 0
            ? (ethWins / ethMatched.length * 100).toFixed(1) : 'N/A',
          avgHoldTime: avgHoldTime.toFixed(1),
          totalTrades: trades.length,
          matchedTrades: matched.length,
        })
      } catch (e) {
        console.error('PnLSummary error:', e)
      }
    }
    fetchData()
    const interval = setInterval(fetchData, 60000)
    return () => clearInterval(interval)
  }, [])

  if (!stats) return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800 mb-6">
      <p className="text-gray-400 text-sm mb-3">P&L Summary</p>
      <div className="text-center text-gray-600 py-4">Loading...</div>
    </div>
  )

  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800 mb-6">
      <p className="text-gray-400 text-sm mb-1">P&L Summary</p>
      <p className="text-gray-600 text-xs mb-3">
        Position tracking — {stats.matchedTrades} matched sells
      </p>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">

        <div className="bg-gray-800 rounded-lg p-3 text-center">
          <p className="text-gray-500 text-xs">Total P&L</p>
          <p className={`text-xl font-bold ${stats.totalPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {stats.totalPnL >= 0 ? '+' : ''}${stats.totalPnL.toFixed(2)}
          </p>
          <p className="text-gray-500 text-xs">Position matched</p>
        </div>

        <div className="bg-gray-800 rounded-lg p-3 text-center">
          <p className="text-gray-500 text-xs">Portfolio Value</p>
          <p className="text-xl font-bold text-white">
            ${stats.totalPortfolio.toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </p>
          <p className="text-gray-500 text-xs">USDT + Crypto</p>
        </div>

        <div className="bg-gray-800 rounded-lg p-3 text-center">
          <p className="text-gray-500 text-xs">Best Trade</p>
          <p className="text-xl font-bold text-green-400">
            {stats.bestTrade ? `+$${stats.bestTrade.pnl.toFixed(2)}` : 'N/A'}
          </p>
          <p className="text-gray-500 text-xs">
            {stats.bestTrade ? stats.bestTrade.symbol : '---'}
          </p>
        </div>

        <div className="bg-gray-800 rounded-lg p-3 text-center">
          <p className="text-gray-500 text-xs">Worst Trade</p>
          <p className="text-xl font-bold text-red-400">
            {stats.worstTrade
              ? `${stats.worstTrade.pnl >= 0 ? '+' : ''}$${stats.worstTrade.pnl.toFixed(2)}`
              : 'N/A'}
          </p>
          <p className="text-gray-500 text-xs">
            {stats.worstTrade ? stats.worstTrade.symbol : '---'}
          </p>
        </div>

        <div className="bg-gray-800 rounded-lg p-3 text-center">
          <p className="text-gray-500 text-xs">BTC Win Rate</p>
          <p className={`text-xl font-bold ${
            stats.btcWinRate === 'N/A' ? 'text-gray-400' :
            parseFloat(stats.btcWinRate) >= 50 ? 'text-green-400' : 'text-red-400'
          }`}>
            {stats.btcWinRate}{stats.btcWinRate !== 'N/A' ? '%' : ''}
          </p>
          <p className="text-gray-500 text-xs">BTC trades</p>
        </div>

        <div className="bg-gray-800 rounded-lg p-3 text-center">
          <p className="text-gray-500 text-xs">ETH Win Rate</p>
          <p className={`text-xl font-bold ${
            stats.ethWinRate === 'N/A' ? 'text-gray-400' :
            parseFloat(stats.ethWinRate) >= 50 ? 'text-green-400' : 'text-red-400'
          }`}>
            {stats.ethWinRate}{stats.ethWinRate !== 'N/A' ? '%' : ''}
          </p>
          <p className="text-gray-500 text-xs">ETH trades</p>
        </div>

        <div className="bg-gray-800 rounded-lg p-3 text-center">
          <p className="text-gray-500 text-xs">Avg Hold Time</p>
          <p className="text-xl font-bold text-blue-400">{stats.avgHoldTime}h</p>
          <p className="text-gray-500 text-xs">Per position</p>
        </div>

        <div className="bg-gray-800 rounded-lg p-3 text-center">
          <p className="text-gray-500 text-xs">Total Trades</p>
          <p className="text-xl font-bold text-white">{stats.totalTrades}</p>
          <p className="text-gray-500 text-xs">Executed</p>
        </div>

      </div>
    </div>
  )
}