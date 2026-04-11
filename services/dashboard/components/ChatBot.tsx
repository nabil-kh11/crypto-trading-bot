/* eslint-disable @typescript-eslint/no-explicit-any */
'use client'
import { useState } from 'react'

export default function ChatBot() {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<{ role: string, text: string }[]>([
    { role: 'bot', text: 'Hello! Ask me about Bitcoin or Ethereum sentiment.' }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  const sendMessage = async () => {
    if (!input.trim()) return
    const userMsg = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', text: userMsg }])
    setLoading(true)

    try {
      const res = await fetch('http://localhost:8090/api/chat/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: userMsg })
      })
      const data = await res.json()
      setMessages(prev => [...prev, { role: 'bot', text: data.answer }])
    } catch {
      setMessages(prev => [...prev, { role: 'bot', text: 'Error connecting to chatbot.' }])
    }
    setLoading(false)
  }

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {open && (
        <div className="bg-gray-900 border border-gray-700 rounded-xl w-80 h-96 flex flex-col mb-2">
          <div className="p-3 border-b border-gray-700 flex justify-between">
            <p className="text-white text-sm font-bold">Sentiment Chatbot</p>
            <button onClick={() => setOpen(false)} className="text-gray-400 hover:text-white">✕</button>
          </div>
          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {messages.map((m, i) => (
              <div key={i} className={`text-xs p-2 rounded-lg max-w-[90%] ${
                m.role === 'user'
                  ? 'bg-blue-900 text-white ml-auto'
                  : 'bg-gray-800 text-gray-300'
              }`}>
                {m.text}
              </div>
            ))}
            {loading && <div className="text-gray-500 text-xs">Thinking...</div>}
          </div>
          <div className="p-3 border-t border-gray-700 flex gap-2">
            <input
              className="flex-1 bg-gray-800 text-white text-xs rounded-lg px-3 py-2 outline-none"
              placeholder="Ask about BTC or ETH sentiment..."
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && sendMessage()}
            />
            <button
              onClick={sendMessage}
              className="bg-blue-600 text-white text-xs px-3 py-2 rounded-lg hover:bg-blue-700"
            >Send</button>
          </div>
        </div>
      )}
      <button
        onClick={() => setOpen(!open)}
        className="bg-blue-600 text-white rounded-full w-12 h-12 flex items-center justify-center shadow-lg hover:bg-blue-700 float-right"
      >
        💬
      </button>
    </div>
  )
}