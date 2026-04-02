/* eslint-disable @typescript-eslint/no-explicit-any */
'use client'

import { useEffect, useState } from 'react'
import PriceChart from '@/components/PriceChart'
import SignalCard from '@/components/SignalCard'
import PortfolioCard from '@/components/PortfolioCard'
import ChatBot from '@/components/ChatBot'
import TradesTable from '@/components/TradesTable'
import ServiceHealth from '@/components/ServiceHealth'
import PortfolioChart from '@/components/PortfolioChart'
import RSIChart from '@/components/RSIChart'
import SignalHistory from '@/components/SignalHistory'
import ConfidenceTrend from '@/components/ConfidenceTrend'
import WinRate from '@/components/WinRate'
import SentimentGauge from '@/components/SentimentGauge'
export default function Dashboard() {
  const [btcPrice, setBtcPrice] = useState<any>(null)
  const [ethPrice, setEthPrice] = useState<any>(null)
  const [btcSentiment, setBtcSentiment] = useState<any>(null)
  const [ethSentiment, setEthSentiment] = useState<any>(null)
  const [trades, setTrades] = useState<any[]>([])
  const [lastUpdate, setLastUpdate] = useState<string>('')

 const fetchData = async () => {
  try {
    const safeFetch = (url: string) => 
      fetch(url).then(r => r.json()).catch(() => null)

const [btcP, ethP, btcSent, ethSent, tradesData] = await Promise.all([
  safeFetch('http://localhost:8001/price/BTC-USDT'),
  safeFetch('http://localhost:8001/price/ETH-USDT'),
  safeFetch('http://localhost:8003/summary/BTC'),
  safeFetch('http://localhost:8003/summary/ETH'),
  safeFetch('http://localhost:8004/trades?limit=50'),
])

    if (btcP) setBtcPrice(btcP)
    if (ethP) setEthPrice(ethP)

    if (btcSent) setBtcSentiment(btcSent)
    if (ethSent) setEthSentiment(ethSent)
    if (tradesData) setTrades(tradesData.trades || [])
    setLastUpdate(new Date().toLocaleTimeString())
  } catch (e) {
    console.error('Fetch error:', e)
  }
}

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  return (
    <main className="min-h-screen bg-gray-950 text-white p-4">
      <div className="max-w-7xl mx-auto">

        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-white">Crypto Trading Bot</h1>
            <p className="text-gray-400 text-sm">Advanced ML-powered trading platform</p>
          </div>
          <div className="text-right">
            <p className="text-gray-400 text-xs">Last updated: {lastUpdate}</p>
            <div className="flex gap-2 mt-1">
              <span className="w-2 h-2 rounded-full bg-green-500 inline-block mt-1"></span>
              <span className="text-green-400 text-xs">Live</span>
            </div>
          </div>
        </div>
        <ServiceHealth />
        {/* Win Rate Statistics */}
<WinRate trades={trades} />
        
        {/* Price Cards */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
            <p className="text-gray-400 text-sm">BTC / USDT</p>
            <p className="text-3xl font-bold text-orange-400">
              ${btcPrice?.price?.toLocaleString() || '---'}
            </p>
            <p className="text-gray-500 text-xs mt-1">
              H: ${btcPrice?.high?.toLocaleString()} | L: ${btcPrice?.low?.toLocaleString()}
            </p>
          </div>
          <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
            <p className="text-gray-400 text-sm">ETH / USDT</p>
            <p className="text-3xl font-bold text-blue-400">
              ${ethPrice?.price?.toLocaleString() || '---'}
            </p>
            <p className="text-gray-500 text-xs mt-1">
              H: ${ethPrice?.high?.toLocaleString()} | L: ${ethPrice?.low?.toLocaleString()}
            </p>
          </div>
        </div>
        {/* RSI Charts */}
<div className="grid grid-cols-2 gap-4 mb-6">
  <RSIChart symbol="BTC-USDT" color="#f97316" label="BTC" />
  <RSIChart symbol="ETH-USDT" color="#60a5fa" label="ETH" />
</div>

{/* Signal History + Confidence */}
<div className="grid grid-cols-2 gap-4 mb-6">
  <SignalHistory symbol="BTC/USDT" />
  <SignalHistory symbol="ETH/USDT" />
</div>

<div className="grid grid-cols-2 gap-4 mb-6">
  <ConfidenceTrend symbol="BTC/USDT" color="#f97316" />
  <ConfidenceTrend symbol="ETH/USDT" color="#60a5fa" />
</div>
        {/* Charts */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <PriceChart symbol="BTC-USDT" color="#f97316" label="BTC" />
          <PriceChart symbol="ETH-USDT" color="#60a5fa" label="ETH" />
        </div>

       {/* Signals + Sentiment Gauge */}
<div className="grid grid-cols-3 gap-4 mb-6">
  <SignalCard title="BTC Signal" signal={null} />
  <SignalCard title="ETH Signal" signal={null} />
  <SentimentGauge btc={btcSentiment} eth={ethSentiment} />
</div>

        {/* Portfolio */}
<div className="grid grid-cols-2 gap-4 mb-6">
  <PortfolioCard title="BTC Portfolio" asset="BTC" price={btcPrice?.price} />
  <PortfolioCard title="ETH Portfolio" asset="ETH" price={ethPrice?.price} />
</div>

        {/* Trades Table */}
        <TradesTable trades={trades} />
        <PortfolioChart trades={trades} />

        {/* Chatbot */}
        <ChatBot />

      </div>
    </main>
  )
}