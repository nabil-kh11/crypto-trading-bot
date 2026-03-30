/* eslint-disable @typescript-eslint/no-explicit-any */
'use client'

export default function StatsRow({ trades }: { trades: any[] }) {
  const totalTrades = trades.length
  const buyTrades = trades.filter(t => t.signal === 'BUY').length
  const sellTrades = trades.filter(t => t.signal === 'SELL').length
  
  const bestTrade = trades.reduce((best, t) => {
    const value = t.capital_after - t.capital_before
    return value > (best?.value || 0) ? { ...t, value } : best
  }, null)

  const totalVolume = trades.reduce((sum, t) => sum + (t.price * t.quantity || 0), 0)

  return (
    <div className="grid grid-cols-4 gap-4 mb-6">
      <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
        <p className="text-gray-400 text-xs">Total Trades</p>
        <p className="text-2xl font-bold text-white mt-1">{totalTrades}</p>
        <p className="text-gray-500 text-xs mt-1">
          {buyTrades} BUY / {sellTrades} SELL
        </p>
      </div>
      <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
        <p className="text-gray-400 text-xs">Total Volume</p>
        <p className="text-2xl font-bold text-white mt-1">
          ${totalVolume > 1000000 
            ? (totalVolume/1000000).toFixed(2) + 'M' 
            : totalVolume.toLocaleString()}
        </p>
        <p className="text-gray-500 text-xs mt-1">Paper trading</p>
      </div>
      <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
        <p className="text-gray-400 text-xs">Best Trade</p>
        <p className="text-2xl font-bold text-green-400 mt-1">
          {bestTrade ? `$${(bestTrade.value/1000000).toFixed(2)}M` : 'N/A'}
        </p>
        <p className="text-gray-500 text-xs mt-1">
          {bestTrade ? bestTrade.signal + ' ' + bestTrade.symbol : 'No sells yet'}
        </p>
      </div>
      <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
        <p className="text-gray-400 text-xs">Active Models</p>
        <p className="text-2xl font-bold text-purple-400 mt-1">2</p>
        <p className="text-gray-500 text-xs mt-1">NN (BTC) · RF (ETH)</p>
      </div>
    </div>
  )
}