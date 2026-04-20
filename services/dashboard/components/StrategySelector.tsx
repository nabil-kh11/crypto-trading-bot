/* eslint-disable @typescript-eslint/no-explicit-any */
'use client'
import { useEffect, useState } from 'react'

const STRATEGY_INFO = {
  scalping: {
    label: 'Scalping',
    description: 'Frequent trades, small profits',
    color: 'text-yellow-400',
    bg: 'bg-yellow-900/20 border-yellow-700',
    activeBg: 'bg-yellow-600',
    details: 'Confidence >35% | Stop 2% | TP 2/4/6% | No filters'
  },
  swing: {
    label: 'Swing Trading',
    description: 'Balanced risk/reward',
    color: 'text-blue-400',
    bg: 'bg-blue-900/20 border-blue-700',
    activeBg: 'bg-blue-600',
    details: 'Confidence >50% | Stop 5% | TP 10/15/20% | All filters'
  },
  position: {
    label: 'Position Trading',
    description: 'High conviction, long-term',
    color: 'text-green-400',
    bg: 'bg-green-900/20 border-green-700',
    activeBg: 'bg-green-600',
    details: 'Confidence >70% | Stop 10% | TP 20/30/50% | Strict filters'
  },
  off: {
    label: 'OFF',
    description: 'Bot disabled',
    color: 'text-red-400',
    bg: 'bg-red-900/20 border-red-700',
    activeBg: 'bg-red-600',
    details: 'No trades will be executed'
  }
}

export default function StrategySelector() {
  const [active, setActive] = useState<string>('swing')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<string>('')

  useEffect(() => {
    fetch('http://localhost:8004/strategy')
      .then(r => r.json())
      .then(data => setActive(data.active))
      .catch(() => null)
  }, [])

  const changeStrategy = async (name: string) => {
    setLoading(true)
    setMessage('')
    try {
      const res = await fetch(`http://localhost:8004/strategy/${name}`, {
        method: 'POST'
      })
      const data = await res.json()
      if (res.ok) {
        setActive(data.active)
        setMessage(`✓ Switched to ${STRATEGY_INFO[name as keyof typeof STRATEGY_INFO].label}`)
        setTimeout(() => setMessage(''), 3000)
      }
    } catch {
      setMessage('Error changing strategy')
    }
    setLoading(false)
  }

  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800 mb-6">
      <div className="flex justify-between items-center mb-3">
        <p className="text-gray-400 text-sm">Trading Strategy</p>
        {message && (
          <span className="text-green-400 text-xs">{message}</span>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {Object.entries(STRATEGY_INFO).map(([key, info]) => (
          <button
            key={key}
            onClick={() => changeStrategy(key)}
            disabled={loading || active === key}
            className={`rounded-lg p-3 border text-left transition-all ${
              active === key
                ? `${info.activeBg} border-transparent opacity-100`
                : `${info.bg} hover:opacity-80`
            } disabled:cursor-default`}
          >
            <p className={`text-sm font-bold ${active === key ? 'text-white' : info.color}`}>
              {info.label}
              {active === key && <span className="ml-2 text-xs">● Active</span>}
            </p>
            <p className="text-gray-400 text-xs mt-1">{info.description}</p>
            <p className="text-gray-600 text-xs mt-1">{info.details}</p>
          </button>
        ))}
      </div>

      {/* Active strategy details */}
      <div className="mt-3 pt-3 border-t border-gray-800">
        <p className="text-gray-500 text-xs">
          Active: <span className={`font-bold ${STRATEGY_INFO[active as keyof typeof STRATEGY_INFO]?.color}`}>
            {STRATEGY_INFO[active as keyof typeof STRATEGY_INFO]?.label}
          </span>
          {' — '}
          {STRATEGY_INFO[active as keyof typeof STRATEGY_INFO]?.details}
        </p>
      </div>
    </div>
  )
}