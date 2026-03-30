/* eslint-disable @typescript-eslint/no-explicit-any */

'use client'

export default function TradesTable({ trades }: { trades: any[] }) {
  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800 mb-6">
      <p className="text-gray-400 text-sm mb-3">Recent Trades</p>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-gray-500 border-b border-gray-800">
              <th className="text-left pb-2">Symbol</th>
              <th className="text-left pb-2">Signal</th>
              <th className="text-left pb-2">Price</th>
              <th className="text-left pb-2">Quantity</th>
              <th className="text-left pb-2">Confidence</th>
              <th className="text-left pb-2">Status</th>
              <th className="text-left pb-2">Time</th>
            </tr>
          </thead>
          <tbody>
            {trades.length === 0 ? (
              <tr><td colSpan={7} className="text-gray-600 py-4 text-center">No trades yet</td></tr>
            ) : trades.map((trade, i) => (
              <tr key={i} className="border-b border-gray-800/50">
                <td className="py-2 text-white">{trade.symbol}</td>
                <td className={`py-2 font-bold ${
                  trade.signal === 'BUY' ? 'text-green-400' :
                  trade.signal === 'SELL' ? 'text-red-400' : 'text-yellow-400'
                }`}>{trade.signal}</td>
                <td className="py-2 text-gray-300">${trade.price?.toLocaleString()}</td>
                <td className="py-2 text-gray-300">{trade.quantity?.toFixed(6)}</td>
                <td className="py-2 text-gray-300">{trade.confidence?.toFixed(1)}%</td>
                <td className="py-2 text-green-400">{trade.status}</td>
                <td className="py-2 text-gray-500">
                  {new Date(trade.executed_at).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}