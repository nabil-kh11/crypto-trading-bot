/* eslint-disable @typescript-eslint/no-explicit-any */
'use client'
import { useEffect, useState } from 'react'

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
        const sells = trades.filter((t: any) => t.signal === 'SELL' || t.trade_type === 'STOP_LOSS')

        const avgBuyPrice = buys.length > 0
          ? buys.reduce((s: number, b: any) => s + b.price, 0) / buys.length
          : 0

        const profitableSells = sells.filter((t: any) =>
          avgBuyPrice > 0 ? t.price > avgBuyPrice : t.capital_after > t.capital_before
        )

        const winRate = sells.length > 0
          ? (profitableSells.length / sells.length * 100).toFixed(1)
          : 'N/A'

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
    const interval = setInterval(fetchTrades, 60000) // refresh every 1 min
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
            <p className="text-gray-500 text-xs">Sell above avg buy</p>
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