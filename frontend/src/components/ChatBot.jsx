// c:\Users\rkris\Downloads\doctor-app\doctor-app\frontend\src\components\ChatBot.jsx
import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { chatAPI } from '../services/api'
import { useAuth } from '../context/AuthContext'

export default function ChatBot() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState([
    { role: 'bot', text: 'Hi! I can help you find a doctor. What are you looking for?' }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    if (isOpen) {
      setTimeout(scrollToBottom, 100) // Small delay to ensure render
    }
  }, [messages, isOpen])

  // Reset chat when user logs out or changes
  useEffect(() => {
    setMessages([
      { role: 'bot', text: user ? `Hi ${user.full_name}! How can I help you today?` : 'Hi! I can help you find a doctor.' }
    ])
    if (!user) setIsOpen(false)
  }, [user])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim()) return

    const userMsg = input
    setMessages(prev => [...prev, { role: 'user', text: userMsg }])
    setInput('')
    setLoading(true)
    
    // Add a placeholder message for the bot
    setMessages(prev => [...prev, { role: 'bot', text: '' }])

    try {
      const token = JSON.parse(localStorage.getItem('doctorbook_user') || '{}').access_token
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ message: userMsg })
      })

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let botText = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const chunk = decoder.decode(value, { stream: true })
        botText += chunk
        
        setMessages(prev => {
          const newMsgs = [...prev]
          newMsgs[newMsgs.length - 1].text = botText
          return newMsgs
        })
      }
    } catch (err) {
      setMessages(prev => {
        const newMsgs = [...prev]
        newMsgs[newMsgs.length - 1].text = 'Sorry, I encountered an error.'
        return newMsgs
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ position: 'fixed', bottom: 20, right: 20, zIndex: 9999, fontFamily: 'sans-serif' }}>
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          style={{
            width: 60, height: 60, borderRadius: '50%', backgroundColor: 'var(--teal)', color: 'white',
            border: 'none', cursor: 'pointer', boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
            fontSize: 24, display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}
        >
          💬
        </button>
      )}

      {isOpen && (
        <div style={{
          width: 350, height: 500, backgroundColor: 'white', borderRadius: 12,
          boxShadow: '0 5px 20px rgba(0,0,0,0.2)', display: 'flex', flexDirection: 'column',
          overflow: 'hidden', border: '1px solid #eee'
        }}>
          {/* Header */}
          <div style={{
            padding: '12px 16px', backgroundColor: 'var(--teal)', color: 'white',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center'
          }}>
            <span style={{ fontWeight: 600 }}>Doctor Assistant</span>
            <button 
              onClick={() => setIsOpen(false)}
              style={{ background: 'none', border: 'none', color: 'white', fontSize: 20, cursor: 'pointer' }}
            >
              ×
            </button>
          </div>

          {/* Messages */}
          <div style={{ flex: 1, overflowY: 'auto', padding: 16, display: 'flex', flexDirection: 'column', gap: 12, backgroundColor: '#f9fafb' }}>
            {messages.map((msg, idx) => {
              const hasButton = msg.text.includes('[BOOK_NOW]')
              const displayText = msg.text.replace('[BOOK_NOW]', '')
              // Only show the booking button to patients (or guests who need to login)
              const showButton = hasButton && (!user || user.role === 'patient')
              return (
                <div key={idx} style={{
                alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                maxWidth: '80%',
                padding: '10px 14px',
                borderRadius: 12,
                backgroundColor: msg.role === 'user' ? 'var(--teal)' : 'white',
                color: msg.role === 'user' ? 'white' : '#333',
                border: msg.role === 'bot' ? '1px solid #e5e7eb' : 'none',
                fontSize: 14,
                lineHeight: 1.4
              }}>
                {displayText}
                {showButton && (
                  <button
                    onClick={() => {
                      setIsOpen(false)
                      navigate('/doctors')
                    }}
                    style={{
                      display: 'block', marginTop: 10, padding: '8px 12px',
                      backgroundColor: 'var(--teal)', color: 'white',
                      border: 'none', borderRadius: 6, cursor: 'pointer', fontWeight: 600, fontSize: 12,
                      width: '100%'
                    }}
                  >
                    Book Appointment
                  </button>
                )}
              </div>
            )})}
            {loading && (
              <div style={{ alignSelf: 'flex-start', padding: '8px 12px', backgroundColor: 'white', borderRadius: 12, fontSize: 12, color: '#666' }}>
                Typing...
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <form onSubmit={handleSubmit} style={{ padding: 12, borderTop: '1px solid #eee', display: 'flex', gap: 8, backgroundColor: 'white' }}>
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Ask about doctors..."
              style={{ flex: 1, padding: '8px 12px', borderRadius: 20, border: '1px solid #ddd', outline: 'none' }}
            />
            <button 
              type="submit" 
              disabled={loading}
              style={{ 
                backgroundColor: 'var(--teal)', color: 'white', border: 'none', 
                borderRadius: 20, padding: '8px 16px', cursor: 'pointer', fontWeight: 600 
              }}
            >
              Send
            </button>
          </form>
        </div>
      )}
    </div>
  )
}
