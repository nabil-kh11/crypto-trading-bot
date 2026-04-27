/* eslint-disable @typescript-eslint/no-explicit-any */
'use client'
import { useEffect, useState } from 'react'

export default function SignalCard({ title }: { title: string }) {
  const [data, setData] = useState<any>(null)
  const symbol = title.includes('BTC') ? 'BTC-USDT' : 'ETH-USDT'

  useEffect(() => {
    const fetchSignal = () => {
      fetch(`http://localhost:8090/api/ml/signal/${symbol}`)
        .then(r => r.json())
        .then(setData)
        .catch(() => null)
    }
    fetchSignal()
    const interval = setInterval(fetchSignal, 60000)
    return () => clearInterval(interval)
  }, [symbol])

  const signalColor = data?.signal === 'BUY' ? 'text-green-400' :
                      data?.signal === 'SELL' ? 'text-red-400' : 'text-yellow-400'

  const bgColor = data?.signal === 'BUY' ? 'bg-green-900/20 border-green-800' :
                  data?.signal === 'SELL' ? 'bg-red-900/20 border-red-800' :
                  'bg-yellow-900/20 border-yellow-800'

  return (
    <div className={`rounded-xl p-4 border ${bgColor}`}>
      <p className="text-gray-400 text-sm">{title}</p>
      <p className={`text-3xl font-bold mt-1 ${signalColor}`}>
        {data?.signal || '---'}
      </p>
      <p className="text-gray-500 text-xs mt-1">
        Confidence: {data?.confidence?.toFixed(1) || '---'}%
      </p>
      <p className="text-gray-500 text-xs">
        Model: {data?.model || '---'}
      </p>
      <p className="text-gray-600 text-xs mt-1">
        Price: ${data?.price?.toLocaleString() || '---'}
      </p>
    </div>
  )
}