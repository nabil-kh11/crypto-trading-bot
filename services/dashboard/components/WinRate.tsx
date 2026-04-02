/* eslint-disable @typescript-eslint/no-explicit-any */
'use client'
import { useEffect, useState } from 'react'

export default function WinRate({ trades }: { trades: any[] }) {
  const [stats, setStats] = useState<any>(null)

  useEffect(() => {
    if (!trades || trades.length === 0) return

    const buys  = trades.filter(t => t.signal === 'BUY')
    const sells = trades.filter(t => t.signal === 'SELL')

    // Calculate profitable sells
    const profitableSells = sells.filter(t => t.capital_after > 0)
    const winRate = sells.length > 0
      ? (profitableSells.length / sells.length * 100).toFixed(1)
      : 'N/A'

    // Total volume
    const totalVolume = trades.reduce((s, t) => s + (t.price * t.quantity || 0), 0)

    // Best trade
    const bestTrade = sells.reduce((best: any, t: any) => {
      const pnl = t.capital_after - (t.quantity * (buys[0]?.price || t.price))
      return pnl > (best?.pnl || -Infinity) ? { ...t, pnl } : best
    }, null)

    // Average confidence on executed trades
    const avgConf = trades.reduce((s, t) => s + t.confidence, 0) / trades.length

    setStats({
      totalTrades: trades.length,
      buys: buys.length,
      sells: sells.length,
      winRate,
      totalVolume,
      avgConf: avgConf.toFixed(1),
      bestTrade
    })
  }, [trades])

  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
      <p className="text-gray-400 text-sm mb-3">Trading Statistics</p>
      {stats ? (
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-gray-800 rounded-lg p-3 text-center">
            <p className="text-gray-500 text-xs">Total Trades</p>
            <p className="text-white text-xl font-bold">{stats.totalTrades}</p>
            <p className="text-gray-500 text-xs">
              {stats.buys}B / {stats.sells}S
            </p>
          </div>
          <div className="bg-gray-800 rounded-lg p-3 text-center">
            <p className="text-gray-500 text-xs">Win Rate</p>
            <p className={`text-xl font-bold ${
              stats.winRate === 'N/A' ? 'text-gray-400' :
              parseFloat(stats.winRate) >= 50 ? 'text-green-400' : 'text-red-400'
            }`}>{stats.winRate}{stats.winRate !== 'N/A' ? '%' : ''}</p>
            <p className="text-gray-500 text-xs">Profitable sells</p>
          </div>
          <div className="bg-gray-800 rounded-lg p-3 text-center">
            <p className="text-gray-500 text-xs">Avg Confidence</p>
            <p className="text-blue-400 text-xl font-bold">{stats.avgConf}%</p>
            <p className="text-gray-500 text-xs">On executed trades</p>
          </div>
          <div className="bg-gray-800 rounded-lg p-3 text-center col-span-2">
            <p className="text-gray-500 text-xs">Total Volume Traded</p>
            <p className="text-purple-400 text-lg font-bold">
              ${stats.totalVolume > 1000000
                ? (stats.totalVolume / 1000000).toFixed(2) + 'M'
                : stats.totalVolume.toLocaleString(undefined, {maximumFractionDigits: 0})}
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
        <div className="text-center text-gray-600 py-4">No trades yet</div>
      )}
    </div>
  )
}