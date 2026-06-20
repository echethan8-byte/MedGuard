import { ChangeEvent, FormEvent } from 'react'

export interface ChatMessage {
  role: 'user' | 'assistant'
  text: string
}

interface ChatbotPanelProps {
  open: boolean
  messages: ChatMessage[]
  input: string
  onInputChange: (value: string) => void
  onToggle: () => void
  onSend: () => void
}

export default function ChatbotPanel({
  open,
  messages,
  input,
  onInputChange,
  onToggle,
  onSend,
}: ChatbotPanelProps) {
  return (
    <>
      <button className="chatbot-toggle" onClick={onToggle} type="button">
        <span className="chatbot-toggle-icon">💬</span>
        <span className="chatbot-toggle-label">Chat</span>
      </button>

      {open && (
        <div className="chatbot-panel">
          <div className="chatbot-header">
            <div>
              <div className="chatbot-title">MedGuard Assistant</div>
              <div className="chatbot-subtitle">Ask about documents, audits, and compliance.</div>
            </div>
            <button className="chatbot-close" onClick={onToggle} type="button">
              ✕
            </button>
          </div>

          <div className="chatbot-messages">
            {messages.map((message, index) => (
              <div key={index} className={`chatbot-message ${message.role}`}>
                <div className="message-role">{message.role === 'user' ? 'You' : 'Assistant'}</div>
                <div className="message-text">{message.text}</div>
              </div>
            ))}
          </div>

          <form
            className="chatbot-input-row"
            onSubmit={(event: FormEvent<HTMLFormElement>) => {
              event.preventDefault()
              onSend()
            }}
          >
            <input
              className="input chatbot-input"
              placeholder="Ask a question..."
              value={input}
              onChange={(event: ChangeEvent<HTMLInputElement>) => onInputChange(event.target.value)}
            />
            <button className="btn btn-primary chatbot-send" type="submit">
              Send
            </button>
          </form>
        </div>
      )}
    </>
  )
}
