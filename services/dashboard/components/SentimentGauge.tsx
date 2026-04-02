/* eslint-disable @typescript-eslint/no-explicit-any */
'use client'

export default function SentimentGauge({ btc, eth }: { btc: any, eth: any }) {
  const getGaugeColor = (score: number) => {
    if (score > 0.3)  return '#22c55e'
    if (score > 0.1)  return '#86efac'
    if (score < -0.3) return '#ef4444'
    if (score < -0.1) return '#fca5a5'
    return '#eab308'
  }

  const getLabel = (score: number) => {
    if (score > 0.3)  return 'Very Bullish'
    if (score > 0.1)  return 'Bullish'
    if (score < -0.3) return 'Very Bearish'
    if (score < -0.1) return 'Bearish'
    return 'Neutral'
  }

  const getRotation = (score: number) => {
    // -1 to +1 maps to -90 to +90 degrees
    return score * 90
  }

  const GaugeItem = ({ data, asset, assetColor }: any) => {
    const score = data?.avg_score || 0
    const rotation = getRotation(score)
    const color = getGaugeColor(score)
    const total = (data?.positive || 0) + (data?.negative || 0) + (data?.neutral || 0)

    return (
      <div className="flex-1 text-center">
        <p style={{ color: assetColor }} className="text-xs font-bold mb-2">{asset}</p>

        {/* Simple gauge visualization */}
        <div className="relative mx-auto w-24 h-12 overflow-hidden">
          <div className="absolute bottom-0 left-0 w-24 h-24 rounded-full border-4 border-gray-700"
               style={{ borderTopColor: '#374151', borderRightColor: '#374151' }} />
          <div className="absolute bottom-0 left-0 w-24 h-24 rounded-full border-4 border-transparent"
               style={{
                 borderTopColor: color,
                 borderRightColor: score > 0 ? color : 'transparent',
                 borderLeftColor: score < 0 ? color : 'transparent',
                 transform: `rotate(${rotation}deg)`,
                 transition: 'transform 0.5s ease'
               }} />
          <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2">
            <div className="w-0.5 h-10 bg-white origin-bottom"
                 style={{ transform: `rotate(${rotation}deg)` }} />
          </div>
        </div>

        <p className="text-white font-bold text-sm mt-1"
           style={{ color }}>{getLabel(score)}</p>
        <p className="text-gray-500 text-xs">
          Score: {score > 0 ? '+' : ''}{score.toFixed(3)}
        </p>
        {total > 0 && (
          <div className="flex justify-center gap-2 mt-1 text-xs">
            <span className="text-green-400">+{data?.positive || 0}</span>
            <span className="text-red-400">-{data?.negative || 0}</span>
            <span className="text-gray-500">~{data?.neutral || 0}</span>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
      <p className="text-gray-400 text-sm mb-3">Sentiment Gauge (Reddit — 30 days)</p>
      <div className="flex gap-4">
        <GaugeItem data={btc} asset="BTC" assetColor="#f97316" />
        <div className="w-px bg-gray-700" />
        <GaugeItem data={eth} asset="ETH" assetColor="#60a5fa" />
      </div>
    </div>
  )
}