/* eslint-disable @typescript-eslint/no-explicit-any */
'use client'

export default function PortfolioCard({ title, data, price }: {
  title: string, data: any, price: number
}) {
  const portfolioValue = data 
    ? (data.capital || 0) + (data.position || 0) * (price || 0) 
    : 0

  // Initial capital = what was originally deposited
  // If we have a position: initial = position * avg_price + current cash
  // If no position: initial = current cash
  const initialCapital = data?.avg_price > 0
    ? (data.position * data.avg_price) + data.capital
    : data?.capital || 0

  const pnl = initialCapital > 0 ? portfolioValue - initialCapital : 0
  const pnlPct = initialCapital > 0 
    ? ((pnl / initialCapital) * 100).toFixed(2) 
    : '0.00'

  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
      <p className="text-gray-400 text-sm">{title}</p>
      <p className="text-2xl font-bold text-white mt-1">
        ${portfolioValue.toLocaleString(undefined, { maximumFractionDigits: 2 })}
      </p>
      <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
        <div>
          <p className="text-gray-500">Cash</p>
          <p className="text-white">${(data?.capital || 0).toLocaleString(undefined, { maximumFractionDigits: 2 })}</p>
        </div>
        <div>
          <p className="text-gray-500">Position</p>
          <p className="text-white">{(data?.position || 0).toFixed(6)} coins</p>
        </div>
        <div>
          <p className="text-gray-500">Avg Price</p>
          <p className="text-white">${(data?.avg_price || 0).toLocaleString()}</p>
        </div>
        <div>
          <p className="text-gray-500">P&L</p>
          <p className={pnl >= 0 ? 'text-green-400' : 'text-red-400'}>
            {initialCapital > 0 ? `${pnl >= 0 ? '+' : ''}${pnlPct}%` : 'N/A'}
          </p>
        </div>
      </div>
    </div>
  )
}