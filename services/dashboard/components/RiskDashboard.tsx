/* eslint-disable @typescript-eslint/no-explicit-any */
'use client'
import { useEffect, useState } from 'react'

const MAX_DAILY_LOSS = 0.10
const INITIAL_CAPITAL = 10000

export default function RiskDashboard() {
  const [risk, setRisk] = useState<any>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [balanceRes, tradesRes] = await Promise.all([
          fetch('http://localhost:8004/balance'),
          fetch('http://localhost:8004/trades?limit=100&offset=0')
        ])
        const balance = await balanceRes.json()
        const tradesData = await tradesRes.json()
        const trades = tradesData.trades || []

        const totalPortfolio = (balance.USDT || 0) +
          (balance.BTC || 0) * (balance.BTC_PRICE || 0) +
          (balance.ETH || 0) * (balance.ETH_PRICE || 0)

        const btcValue = (balance.BTC || 0) * (balance.BTC_PRICE || 0)
        const ethValue = (balance.ETH || 0) * (balance.ETH_PRICE || 0)
        const exposure = totalPortfolio > 0 ? ((btcValue + ethValue) / totalPortfolio * 100) : 0

        // Today's trades
        const today = new Date().toDateString()
        const todayTrades = trades.filter((t: any) =>
          new Date(t.executed_at).toDateString() === today
        )
        const todayVolume = todayTrades.reduce((s: number, t: any) =>
          s + (t.price * t.quantity || 0), 0)

        // Daily P&L estimate
        const todaySells = todayTrades.filter((t: any) => t.signal === 'SELL')
        const todayBuys  = todayTrades.filter((t: any) => t.signal === 'BUY')
        const avgBuy = todayBuys.length > 0
          ? todayBuys.reduce((s: number, b: any) => s + b.price, 0) / todayBuys.length : 0
        const dailyPnL = todaySells.reduce((s: number, t: any) =>
          s + (avgBuy > 0 ? (t.price - avgBuy) * t.quantity : 0), 0)
        const dailyLossPct = Math.abs(Math.min(0, dailyPnL)) / INITIAL_CAPITAL * 100

        setRisk({
          totalPortfolio,
          exposure: exposure.toFixed(1),
          btcValue,
          ethValue,
          usdtValue: balance.USDT || 0,
          todayVolume,
          dailyPnL,
          dailyLossPct: dailyLossPct.toFixed(2),
          dailyLossLimit: MAX_DAILY_LOSS * 100,
          todayTrades: todayTrades.length,
        })
      } catch (e) {
        console.error('RiskDashboard error:', e)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  if (!risk) return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800 mb-6">
      <p className="text-gray-400 text-sm mb-3">Risk Dashboard</p>
      <div className="text-center text-gray-600 py-4">Loading...</div>
    </div>
  )

  const lossBarWidth = Math.min(100, (parseFloat(risk.dailyLossPct) / risk.dailyLossLimit) * 100)
  const exposureBarWidth = Math.min(100, parseFloat(risk.exposure))

  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800 mb-6">
      <p className="text-gray-400 text-sm mb-3">Risk Dashboard</p>
      <div className="grid grid-cols-2 gap-4">

        {/* Left column */}
        <div className="space-y-3">
          <div className="bg-gray-800 rounded-lg p-3">
            <p className="text-gray-500 text-xs mb-1">Portfolio Exposure</p>
            <p className="text-white font-bold">{risk.exposure}% in Crypto</p>
            <div className="mt-1 bg-gray-700 rounded-full h-2">
              <div
                className="h-2 rounded-full bg-blue-500"
                style={{ width: `${exposureBarWidth}%` }}
              />
            </div>
            <div className="flex justify-between text-xs text-gray-600 mt-0.5">
              <span>USDT: ${risk.usdtValue.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
              <span>Crypto: ${(risk.btcValue + risk.ethValue).toFixed(0)}</span>
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-3">
            <p className="text-gray-500 text-xs mb-1">Daily Loss Limit</p>
            <p className={`font-bold ${parseFloat(risk.dailyLossPct) > 5 ? 'text-red-400' : 'text-green-400'}`}>
              {risk.dailyLossPct}% / {risk.dailyLossLimit}%
            </p>
            <div className="mt-1 bg-gray-700 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${lossBarWidth > 70 ? 'bg-red-500' : lossBarWidth > 40 ? 'bg-yellow-500' : 'bg-green-500'}`}
                style={{ width: `${lossBarWidth}%` }}
              />
            </div>
          </div>
        </div>

        {/* Right column */}
        <div className="space-y-3">
          <div className="bg-gray-800 rounded-lg p-3">
            <p className="text-gray-500 text-xs">Today&apos;s Volume</p>
            <p className="text-white font-bold text-lg">
              ${risk.todayVolume.toLocaleString(undefined, { maximumFractionDigits: 0 })}
            </p>
            <p className="text-gray-600 text-xs">{risk.todayTrades} trades today</p>
          </div>

          <div className="bg-gray-800 rounded-lg p-3">
            <p className="text-gray-500 text-xs">Today&apos;s P&L</p>
            <p className={`font-bold text-lg ${risk.dailyPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {risk.dailyPnL >= 0 ? '+' : ''}${risk.dailyPnL.toFixed(2)}
            </p>
            <p className="text-gray-600 text-xs">From today&apos;s sells</p>
          </div>

          <div className="bg-gray-800 rounded-lg p-3">
            <p className="text-gray-500 text-xs">Total Portfolio</p>
            <p className="text-white font-bold">
              ${risk.totalPortfolio.toLocaleString(undefined, { maximumFractionDigits: 0 })}
            </p>
          </div>
        </div>

      </div>
    </div>
  )
}