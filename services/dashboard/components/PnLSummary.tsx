/* eslint-disable @typescript-eslint/no-explicit-any */
'use client'
import { useEffect, useState } from 'react'

export default function PnLSummary() {
  const [stats, setStats] = useState<any>(null)

  useEffect(() => {
    const fetch_data = async () => {
      try {
        const [tradesRes, balanceRes] = await Promise.all([
          fetch('http://localhost:8004/trades?limit=1000&offset=0'),
          fetch('http://localhost:8004/balance')
        ])
        const tradesData = await tradesRes.json()
        const balance = await balanceRes.json()
        const trades = tradesData.trades || []
        if (trades.length === 0) return

        const buys  = trades.filter((t: any) => t.signal === 'BUY')
        const sells = trades.filter((t: any) => t.signal === 'SELL')

        const avgBuyPrice = buys.length > 0
          ? buys.reduce((s: number, b: any) => s + b.price, 0) / buys.length : 0

        // P&L per sell trade
        const sellPnLs = sells.map((t: any) => ({
          ...t,
          pnl: avgBuyPrice > 0 ? (t.price - avgBuyPrice) * t.quantity : 0
        }))

        const totalPnL = sellPnLs.reduce((s: number, t: any) => s + t.pnl, 0)
        const bestTrade  = sellPnLs.reduce((best: any, t: any) => t.pnl > (best?.pnl || -Infinity) ? t : best, null)
        const worstTrade = sellPnLs.reduce((worst: any, t: any) => t.pnl < (worst?.pnl || Infinity) ? t : worst, null)

        // Win rate by symbol
        const btcSells = sells.filter((t: any) => t.symbol === 'BTC/USDT')
        const ethSells = sells.filter((t: any) => t.symbol === 'ETH/USDT')
        const btcWins  = btcSells.filter((t: any) => t.price > avgBuyPrice).length
        const ethWins  = ethSells.filter((t: any) => t.price > avgBuyPrice).length

        // Avg hold time
        const holdTimes = sells.map((sell: any) => {
          const matchBuy = buys.find((b: any) => b.symbol === sell.symbol)
          if (!matchBuy) return 0
          return (new Date(sell.executed_at).getTime() - new Date(matchBuy.executed_at).getTime()) / 3600000
        }).filter((t: number) => t > 0)
        const avgHoldTime = holdTimes.length > 0
          ? holdTimes.reduce((s: number, t: number) => s + t, 0) / holdTimes.length : 0

        // Current portfolio
        const totalPortfolio = (balance.USDT || 0) +
          (balance.BTC || 0) * (balance.BTC_PRICE || 0) +
          (balance.ETH || 0) * (balance.ETH_PRICE || 0)

        setStats({
          totalPnL,
          totalPortfolio,
          bestTrade,
          worstTrade,
          btcWinRate: btcSells.length > 0 ? (btcWins / btcSells.length * 100).toFixed(1) : 'N/A',
          ethWinRate: ethSells.length > 0 ? (ethWins / ethSells.length * 100).toFixed(1) : 'N/A',
          avgHoldTime: avgHoldTime.toFixed(1),
          totalTrades: trades.length,
        })
      } catch (e) {
        console.error('PnLSummary error:', e)
      }
    }
    fetch_data()
    const interval = setInterval(fetch_data, 60000)
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
      <p className="text-gray-400 text-sm mb-3">P&L Summary</p>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">

        <div className="bg-gray-800 rounded-lg p-3 text-center">
          <p className="text-gray-500 text-xs">Total P&L</p>
          <p className={`text-xl font-bold ${stats.totalPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {stats.totalPnL >= 0 ? '+' : ''}${stats.totalPnL.toFixed(2)}
          </p>
          <p className="text-gray-500 text-xs">From sells</p>
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
            {stats.bestTrade ? `${stats.bestTrade.symbol}` : '---'}
          </p>
        </div>

        <div className="bg-gray-800 rounded-lg p-3 text-center">
          <p className="text-gray-500 text-xs">Worst Trade</p>
          <p className="text-xl font-bold text-red-400">
            {stats.worstTrade ? `$${stats.worstTrade.pnl.toFixed(2)}` : 'N/A'}
          </p>
          <p className="text-gray-500 text-xs">
            {stats.worstTrade ? `${stats.worstTrade.symbol}` : '---'}
          </p>
        </div>

        <div className="bg-gray-800 rounded-lg p-3 text-center">
          <p className="text-gray-500 text-xs">BTC Win Rate</p>
          <p className={`text-xl font-bold ${parseFloat(stats.btcWinRate) >= 50 ? 'text-green-400' : 'text-red-400'}`}>
            {stats.btcWinRate}{stats.btcWinRate !== 'N/A' ? '%' : ''}
          </p>
          <p className="text-gray-500 text-xs">BTC trades</p>
        </div>

        <div className="bg-gray-800 rounded-lg p-3 text-center">
          <p className="text-gray-500 text-xs">ETH Win Rate</p>
          <p className={`text-xl font-bold ${parseFloat(stats.ethWinRate) >= 50 ? 'text-green-400' : 'text-red-400'}`}>
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