import { useState, useRef, useEffect } from 'react'

const SIDEBAR_W = 220

const styles = {
  layout: {
    display: 'flex',
    height: '100vh',
    width: '100vw',
  },
  sidebar: {
    width: SIDEBAR_W,
    minWidth: SIDEBAR_W,
    background: '#16161a',
    borderRight: '1px solid #2a2a32',
    display: 'flex',
    flexDirection: 'column',
    padding: '0',
  },
  sidebarTitle: {
    padding: '20px 18px 16px',
    fontSize: '13px',
    fontWeight: '700',
    letterSpacing: '0.12em',
    color: '#7c7c8a',
    textTransform: 'uppercase',
    borderBottom: '1px solid #2a2a32',
  },
  navItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '10px 18px',
    fontSize: '14px',
    cursor: 'pointer',
    borderRadius: '6px',
    margin: '6px 8px',
    color: '#e2e2e6',
    background: '#1e1e26',
    userSelect: 'none',
    transition: 'background 0.15s',
  },
  navDot: {
    width: '7px',
    height: '7px',
    borderRadius: '50%',
    background: '#6366f1',
    flexShrink: 0,
  },
  main: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    minWidth: 0,
    background: '#0f0f12',
  },
  header: {
    padding: '14px 24px',
    borderBottom: '1px solid #1e1e26',
    fontSize: '15px',
    fontWeight: '600',
    color: '#c4c4cc',
    flexShrink: 0,
  },
  thread: {
    flex: 1,
    overflowY: 'auto',
    padding: '24px',
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  emptyState: {
    flex: 1,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: '#3a3a48',
    fontSize: '14px',
    pointerEvents: 'none',
  },
  bubble: (role) => ({
    maxWidth: '72%',
    alignSelf: role === 'user' ? 'flex-end' : 'flex-start',
    background: role === 'user' ? '#1e1e6e' : '#1a1a22',
    border: `1px solid ${role === 'user' ? '#2d2d8c' : '#2a2a32'}`,
    borderRadius: role === 'user' ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
    padding: '10px 15px',
    fontSize: '14px',
    lineHeight: '1.6',
    color: role === 'user' ? '#c8c8ff' : '#e2e2e6',
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
  }),
  roleLabel: (role) => ({
    fontSize: '11px',
    color: '#4a4a5a',
    marginBottom: '4px',
    alignSelf: role === 'user' ? 'flex-end' : 'flex-start',
    textTransform: 'uppercase',
    letterSpacing: '0.06em',
  }),
  loadingDots: {
    alignSelf: 'flex-start',
    display: 'flex',
    gap: '5px',
    padding: '12px 16px',
    background: '#1a1a22',
    border: '1px solid #2a2a32',
    borderRadius: '18px 18px 18px 4px',
  },
  dot: (i) => ({
    width: '6px',
    height: '6px',
    borderRadius: '50%',
    background: '#4a4a6a',
    animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite`,
  }),
  inputRow: {
    display: 'flex',
    gap: '10px',
    padding: '16px 24px',
    borderTop: '1px solid #1e1e26',
    background: '#0f0f12',
    flexShrink: 0,
  },
  input: {
    flex: 1,
    background: '#1a1a22',
    border: '1px solid #2a2a32',
    borderRadius: '10px',
    color: '#e2e2e6',
    fontSize: '14px',
    padding: '10px 14px',
    outline: 'none',
    resize: 'none',
    fontFamily: 'inherit',
    lineHeight: '1.5',
    minHeight: '42px',
    maxHeight: '160px',
  },
  sendBtn: (loading) => ({
    background: loading ? '#2a2a42' : '#4a4aaa',
    color: loading ? '#5a5a7a' : '#fff',
    border: 'none',
    borderRadius: '10px',
    padding: '0 18px',
    fontSize: '14px',
    fontWeight: '600',
    cursor: loading ? 'not-allowed' : 'pointer',
    flexShrink: 0,
    transition: 'background 0.15s',
    minWidth: '72px',
  }),
}

function LoadingDots() {
  return (
    <div style={styles.loadingDots}>
      <style>{`
        @keyframes bounce {
          0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
          40% { transform: translateY(-5px); opacity: 1; }
        }
      `}</style>
      {[0, 1, 2].map((i) => (
        <div key={i} style={styles.dot(i)} />
      ))}
    </div>
  )
}

export default function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const threadRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    if (threadRef.current) {
      threadRef.current.scrollTop = threadRef.current.scrollHeight
    }
  }, [messages, loading])

  const send = async () => {
    const text = input.trim()
    if (!text || loading) return

    const userMsg = { role: 'user', content: text }
    const nextMessages = [...messages, userMsg]
    setMessages(nextMessages)
    setInput('')
    setLoading(true)

    try {
      const history = messages.map((m) => ({ role: m.role, content: m.content }))
      const res = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, history }),
      })
      const data = await res.json()
      setMessages([...nextMessages, { role: 'assistant', content: data.response }])
    } catch (err) {
      setMessages([
        ...nextMessages,
        { role: 'assistant', content: `Error: ${err.message}` },
      ])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  return (
    <div style={styles.layout}>
      <aside style={styles.sidebar}>
        <div style={styles.sidebarTitle}>MSNCTRL</div>
        <div style={styles.navItem}>
          <div style={styles.navDot} />
          Maker
        </div>
      </aside>

      <main style={styles.main}>
        <div style={styles.header}>Maker — ICT Market Chat</div>

        <div ref={threadRef} style={styles.thread}>
          {messages.length === 0 && !loading && (
            <div style={styles.emptyState}>Ask about NQ or ES market conditions</div>
          )}
          {messages.map((m, i) => (
            <div key={i} style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
              <div style={styles.roleLabel(m.role)}>
                {m.role === 'user' ? 'You' : 'Maker'}
              </div>
              <div style={styles.bubble(m.role)}>{m.content}</div>
            </div>
          ))}
          {loading && <LoadingDots />}
        </div>

        <div style={styles.inputRow}>
          <textarea
            ref={inputRef}
            style={styles.input}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Ask about market structure, levels, bias…"
            rows={1}
            disabled={loading}
          />
          <button style={styles.sendBtn(loading)} onClick={send} disabled={loading}>
            {loading ? '…' : 'Send'}
          </button>
        </div>
      </main>
    </div>
  )
}
