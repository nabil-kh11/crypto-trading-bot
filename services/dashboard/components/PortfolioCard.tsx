/* eslint-disable @typescript-eslint/no-explicit-any */
'use client'
import { useEffect, useState, useRef } from 'react'

export default function PortfolioCard({ title, asset, price }: {
  title: string
  asset: string
  price: number
}) {
  const [balance, setBalance] = useState<any>(null)
  const initialValueRef = useRef<number | null>(null)

  useEffect(() => {
    const fetchBalance = () => {
      fetch('http://localhost:8004/balance')
        .then(r => r.json())
        .then(data => {
          setBalance(data)
        })
        .catch(() => null)
    }
    fetchBalance()
    const interval = setInterval(fetchBalance, 30000)
    return () => clearInterval(interval)
  }, [])

  const assetBalance  = balance?.[asset] || 0
  const usdtBalance   = balance?.USDT || 0
  const positionValue = assetBalance * (price || 0)

  // Set initial value on first load
  if (initialValueRef.current === null && positionValue > 0) {
    initialValueRef.current = positionValue
  }

  const initialValue = initialValueRef.current || positionValue
  const pnl    = positionValue - initialValue
  const pnlPct = initialValue > 0 ? ((pnl / initialValue) * 100).toFixed(2) : '0.00'

  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
      <p className="text-gray-400 text-sm">{title}</p>
      <p className="text-xs text-green-500 mb-2">● Binance Testnet</p>
      <p className="text-2xl font-bold text-white">
        ${positionValue.toLocaleString(undefined, {maximumFractionDigits: 2})}
      </p>
      <div className="grid grid-cols-2 gap-2 text-xs mt-3">
        <div>
          <p className="text-gray-500">USDT Balance</p>
          <p className="text-white font-bold">
            ${usdtBalance.toLocaleString(undefined, {maximumFractionDigits: 2})}
          </p>
        </div>
        <div>
          <p className="text-gray-500">{asset} Balance</p>
          <p className="text-white font-bold">{assetBalance.toFixed(6)}</p>
        </div>
        <div>
          <p className="text-gray-500">{asset} Value</p>
          <p className="text-white">
            ${positionValue.toLocaleString(undefined, {maximumFractionDigits: 2})}
          </p>
        </div>
        <div>
          <p className="text-gray-500">P&L (session)</p>
          <p className={pnl >= 0 ? 'text-green-400' : 'text-red-400'}>
            {pnl >= 0 ? '+' : ''}{pnlPct}%
          </p>
        </div>
      </div>
    </div>
  )
}