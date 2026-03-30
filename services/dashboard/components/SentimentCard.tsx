/* eslint-disable @typescript-eslint/no-explicit-any */

'use client'

export default function SentimentCard({ btc, eth }: { btc: any, eth: any }) {
  const getSentimentColor = (score: number) => {
    if (score > 0.1) return 'text-green-400'
    if (score < -0.1) return 'text-red-400'
    return 'text-yellow-400'
  }

  const getSentimentLabel = (score: number) => {
    if (score > 0.2) return 'Bullish'
    if (score > 0.05) return 'Slightly Bullish'
    if (score < -0.2) return 'Bearish'
    if (score < -0.05) return 'Slightly Bearish'
    return 'Neutral'
  }

  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
      <p className="text-gray-400 text-sm mb-3">Reddit Sentiment (7 days)</p>

      <div className="mb-3">
        <p className="text-orange-400 text-xs font-bold">BTC</p>
        <p className={`text-lg font-bold ${getSentimentColor(btc?.avg_score || 0)}`}>
          {getSentimentLabel(btc?.avg_score || 0)}
        </p>
        <div className="flex gap-2 text-xs mt-1">
          <span className="text-green-400">+{btc?.positive || 0}</span>
          <span className="text-red-400">-{btc?.negative || 0}</span>
          <span className="text-gray-500">~{btc?.neutral || 0}</span>
        </div>
      </div>

      <div>
        <p className="text-blue-400 text-xs font-bold">ETH</p>
        <p className={`text-lg font-bold ${getSentimentColor(eth?.avg_score || 0)}`}>
          {getSentimentLabel(eth?.avg_score || 0)}
        </p>
        <div className="flex gap-2 text-xs mt-1">
          <span className="text-green-400">+{eth?.positive || 0}</span>
          <span className="text-red-400">-{eth?.negative || 0}</span>
          <span className="text-gray-500">~{eth?.neutral || 0}</span>
        </div>
      </div>
    </div>
  )
}