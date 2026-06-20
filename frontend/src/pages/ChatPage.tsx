import { ChangeEvent, FormEvent } from 'react'
import { ChatMessage } from '../components/ChatbotPanel'
import { Document } from '../utils/mockData'

interface ChatPageProps {
  messages: ChatMessage[]
  input: string
  onInputChange: (value: string) => void
  onSend: () => void
  documents: Document[]
  selectedDocumentId: string
  onSelectDocument: (id: string) => void
  loading: boolean
}

export default function ChatPage({
  messages,
  input,
  onInputChange,
  onSend,
  documents,
  selectedDocumentId,
  onSelectDocument,
  loading,
}: ChatPageProps) {
  return (
    <div className="fade-in">
      <div className="page-header">
        <div className="page-eyebrow">AI Assistant</div>
        <div className="page-title">MedGuard Chat</div>
        <div className="page-subtitle">Chat with the compliance assistant about audits, documents, and policy guidance.</div>
      </div>

      <div className="chat-page-shell">
        <div className="chat-page-panel">
          <div className="chat-panel-header">
            <div>
              <div className="chat-panel-title">MedGuard Assistant</div>
              <div className="chat-panel-subtitle">Ask anything about healthcare compliance and audit findings.</div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 16 }}>
            <label style={{ flex: '1 1 280px', display: 'flex', flexDirection: 'column', gap: 6 }}>
              <span style={{ color: 'var(--text-secondary)', fontSize: 12 }}>Document to reference</span>
              <select
                className="input"
                value={selectedDocumentId}
                onChange={(event: ChangeEvent<HTMLSelectElement>) => onSelectDocument(event.target.value)}
              >
                <option value="">Latest indexed document</option>
                {documents.map(doc => (
                  <option key={doc.id} value={doc.id}>{doc.name}</option>
                ))}
              </select>
            </label>
            <div style={{ alignSelf: 'flex-end', color: 'var(--text-secondary)', fontSize: 12 }}>
              {loading ? 'Thinking on the selected document…' : 'Answers are grounded in uploaded document text.'}
            </div>
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
              disabled={loading}
            />
            <button className="btn btn-primary chatbot-send" type="submit" disabled={loading}>
              {loading ? 'Working…' : 'Send'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
