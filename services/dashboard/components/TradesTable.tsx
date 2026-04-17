/* eslint-disable @typescript-eslint/no-explicit-any */
'use client'
import { useState, useEffect } from 'react'

const PAGE_SIZE = 10

export default function TradesTable() {
  const [page, setPage] = useState(1)
  const [trades, setTrades] = useState<any[]>([])
  const [total, setTotal] = useState(0)

  const fetchPage = async (p: number) => {
    try {
      const res = await fetch(
        `http://localhost:8004/trades?limit=${PAGE_SIZE}&offset=${(p - 1) * PAGE_SIZE}`
      )
      const data = await res.json()
      setTrades(data.trades || [])
      setTotal(data.total || 0)
    } catch {
      setTrades([])
    }
  }

  const handlePage = (newPage: number) => {
    setPage(newPage)
    fetchPage(newPage)
  }

  useEffect(() => {
    fetchPage(1)
  }, [])

  const totalPages = Math.ceil(total / PAGE_SIZE)

  const getPageNumbers = () => {
    const pages = []
    let start = Math.max(1, page - 2)
    const end = Math.min(totalPages, start + 4)
    if (end - start < 4) start = Math.max(1, end - 4)
    for (let i = start; i <= end; i++) pages.push(i)
    return pages
  }

  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800 mb-6" style={{ minHeight: '400px' }}>
      <div className="flex justify-between items-center mb-3">
        <p className="text-gray-400 text-sm">Recent Trades</p>
        <p className="text-gray-500 text-xs">{total} total trades</p>
      </div>
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
              <tr>
                <td colSpan={7} className="text-gray-600 py-4 text-center">
                  No trades yet
                </td>
              </tr>
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
                <td className="py-2 text-gray-500">{new Date(trade.executed_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex justify-center items-center gap-2 mt-4">
          <button onClick={() => handlePage(1)} disabled={page === 1}
            className="px-2 py-1 text-xs rounded bg-gray-800 text-gray-400 disabled:opacity-30 hover:bg-gray-700">«</button>
          <button onClick={() => handlePage(page - 1)} disabled={page === 1}
            className="px-3 py-1 text-xs rounded bg-gray-800 text-gray-400 disabled:opacity-30 hover:bg-gray-700">Previous</button>
          {getPageNumbers().map(p => (
            <button key={p} onClick={() => handlePage(p)}
              className={`px-3 py-1 text-xs rounded ${p === page ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'}`}>
              {p}
            </button>
          ))}
          <button onClick={() => handlePage(page + 1)} disabled={page === totalPages}
            className="px-3 py-1 text-xs rounded bg-gray-800 text-gray-400 disabled:opacity-30 hover:bg-gray-700">Next</button>
          <button onClick={() => handlePage(totalPages)} disabled={page === totalPages}
            className="px-2 py-1 text-xs rounded bg-gray-800 text-gray-400 disabled:opacity-30 hover:bg-gray-700">»</button>
          <span className="text-gray-500 text-xs ml-2">Page {page} of {totalPages}</span>
        </div>
      )}
    </div>
  )
}