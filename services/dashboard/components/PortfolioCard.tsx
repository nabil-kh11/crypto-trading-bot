/* eslint-disable @typescript-eslint/no-explicit-any */
'use client'
import { useEffect, useState } from 'react'

export default function PortfolioCard({ title, asset, price }: {
  title: string
  asset: string
  price: number
}) {
  const [balance, setBalance] = useState<any>(null)

  useEffect(() => {
    const fetchBalance = () => {
      fetch('http://localhost:8004/balance')
        .then(r => r.json())
        .then(data => setBalance(data))
        .catch(() => null)
    }
    fetchBalance()
    const interval = setInterval(fetchBalance, 10000)
    return () => clearInterval(interval)
  }, [])

  const assetBalance  = balance?.[asset] || 0
  const usdtBalance   = balance?.USDT || 0

  // Use WebSocket price (updates every 2s) for position value
  const positionValue = assetBalance * (price || 0)

  // Total portfolio using real-time prices
  const btcPrice = asset === 'BTC' ? (price || 0) : (balance?.BTC_PRICE || 0)
  const ethPrice = asset === 'ETH' ? (price || 0) : (balance?.ETH_PRICE || 0)
  const totalPortfolio = usdtBalance +
    (balance?.BTC || 0) * btcPrice +
    (balance?.ETH || 0) * ethPrice

  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
      <p className="text-gray-400 text-sm">{title}</p>
      <p className="text-xs text-green-500 mb-2">● Binance Testnet</p>
      <p className="text-2xl font-bold text-white">
        ${positionValue.toLocaleString(undefined, { maximumFractionDigits: 2 })}
      </p>
      <div className="grid grid-cols-2 gap-2 text-xs mt-3">
        <div>
          <p className="text-gray-500">USDT Balance</p>
          <p className="text-white font-bold">
            ${usdtBalance.toLocaleString(undefined, { maximumFractionDigits: 2 })}
          </p>
        </div>
        <div>
          <p className="text-gray-500">{asset} Balance</p>
          <p className="text-white font-bold">{assetBalance.toFixed(6)}</p>
        </div>
        <div>
          <p className="text-gray-500">{asset} Price</p>
          <p className="text-white">
            ${price?.toLocaleString(undefined, { maximumFractionDigits: 2 })}
          </p>
        </div>
        <div>
          <p className="text-gray-500">{asset} Value</p>
          <p className="text-white">
            ${positionValue.toLocaleString(undefined, { maximumFractionDigits: 2 })}
          </p>
        </div>
      </div>
      <div className="mt-2 pt-2 border-t border-gray-800">
        <div className="flex justify-between items-center">
          <p className="text-gray-500 text-xs">Total Portfolio</p>
          <p className="text-white font-bold text-sm">
            ${totalPortfolio.toLocaleString(undefined, { maximumFractionDigits: 2 })}
          </p>
        </div>
      </div>
    </div>
  )
}