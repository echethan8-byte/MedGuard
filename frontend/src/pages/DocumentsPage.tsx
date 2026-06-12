import { useState, useRef, type Dispatch, type SetStateAction } from 'react'
import { Document } from '../utils/mockData'

type DocumentsPageProps = {
  documents: Document[]
  setDocuments: Dispatch<SetStateAction<Document[]>>
}

export default function DocumentsPage({ documents, setDocuments }: DocumentsPageProps) {
  const [dragOver, setDragOver] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [toast, setToast] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const showToast = (msg: string) => {
    setToast(msg)
    setTimeout(() => setToast(null), 3000)
  }

  const handleFiles = (files: FileList) => {
    const allowed = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']
    const validFiles = Array.from(files).filter(f => allowed.includes(f.type) || f.name.endsWith('.pdf') || f.name.endsWith('.docx'))
    if (!validFiles.length) { showToast('Only PDF, DOCX, TXT files are accepted.'); return }

    setUploading(true)
    validFiles.forEach(file => {
      const ext = file.name.split('.').pop()?.toUpperCase() as Document['type']
      const newDoc: Document = {
        id: `doc-${Date.now()}-${Math.random().toString(36).slice(2,6)}`,
        name: file.name,
        type: ext || 'PDF',
        size: `${(file.size / 1024 / 1024).toFixed(1)} MB`,
        status: 'processing',
        uploadedAt: new Date().toISOString().split('T')[0],
      }
      setDocuments(prev => [newDoc, ...prev])
      // Simulate processing
      setTimeout(() => {
        setDocuments(prev => prev.map(d =>
          d.id === newDoc.id ? { ...d, status: 'indexed', chunks: Math.floor(Math.random() * 120 + 30) } : d
        ))
      }, 3000)
    })
    setTimeout(() => { setUploading(false); showToast(`${validFiles.length} file(s) queued for indexing`) }, 500)
  }

  const handleDelete = (id: string) => {
    setDocuments(prev => prev.filter(d => d.id !== id))
    showToast('Document removed from index')
  }

  const statusBadge = (status: Document['status']) => {
    const map = {
      processing: { cls: 'badge-processing', label: '⟳ Processing' },
      ready: { cls: 'badge-medium', label: '◎ Ready' },
      indexed: { cls: 'badge-low', label: '✓ Indexed' },
      error: { cls: 'badge-critical', label: '✕ Error' },
    }
    const s = map[status]
    return <span className={`badge ${s.cls}`}>{s.label}</span>
  }

  const typeIcon = (t: Document['type']) =>
    ({ PDF: '📄', DOCX: '📝', TXT: '📃' }[t] || '📄')

  const indexed = documents.filter(d => d.status === 'indexed').length
  const processing = documents.filter(d => d.status === 'processing').length

  return (
    <div className="fade-in">
      <div className="page-header">
        <div className="page-eyebrow">Document Management</div>
        <div className="page-title">Hospital Documents</div>
        <div className="page-subtitle">Upload and manage hospital policy documents for compliance analysis</div>
      </div>

      {/* Stats strip */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
        {[
          { label: 'Total Documents', value: documents.length, color: 'var(--text-primary)' },
          { label: 'Indexed', value: indexed, color: '#10B981' },
          { label: 'Processing', value: processing, color: '#A78BFA' },
          { label: 'Total Chunks', value: documents.reduce((s, d) => s + (d.chunks || 0), 0), color: 'var(--teal)' },
        ].map((s, i) => (
          <div key={i} style={{
            flex: 1, background: 'var(--bg-card)', border: '1px solid var(--border)',
            borderRadius: 'var(--radius)', padding: '14px 16px'
          }}>
            <div style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 6 }}>{s.label}</div>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 22, fontWeight: 700, color: s.color }}>{s.value}</div>
          </div>
        ))}
      </div>

      {/* Upload Zone */}
      <div
        className={`upload-zone ${dragOver ? 'dragover' : ''}`}
        style={{ marginBottom: 20 }}
        onDragOver={e => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={e => { e.preventDefault(); setDragOver(false); handleFiles(e.dataTransfer.files) }}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.docx,.txt"
          style={{ display: 'none' }}
          onChange={e => e.target.files && handleFiles(e.target.files)}
        />
        {uploading ? (
          <>
            <div style={{ marginBottom: 10 }}><span className="spinner" /></div>
            <div className="upload-zone-title">Uploading files…</div>
          </>
        ) : (
          <>
            <div className="upload-zone-icon">⬆</div>
            <div className="upload-zone-title">Drop hospital policy documents here</div>
            <div className="upload-zone-sub">PDF · DOCX · TXT — Max 50 MB per file</div>
            <div style={{ marginTop: 14 }}>
              <span className="btn btn-secondary btn-sm" style={{ pointerEvents: 'none' }}>Browse files</span>
            </div>
          </>
        )}
      </div>

      {/* Documents Table */}
      <div className="card" style={{ padding: 0 }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div className="card-title">Document Index</div>
          <span className="code-label">{documents.length} files</span>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Document</th>
              <th>Type</th>
              <th>Size</th>
              <th>Status</th>
              <th>Chunks</th>
              <th>Uploaded</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {documents.map(doc => (
              <tr key={doc.id}>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontSize: 16 }}>{typeIcon(doc.type)}</span>
                    <span style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--text-primary)', maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {doc.name}
                    </span>
                  </div>
                </td>
                <td><span className="code-label" style={{ fontSize: 10 }}>{doc.type}</span></td>
                <td style={{ color: 'var(--text-muted)', fontSize: 12 }}>{doc.size}</td>
                <td>{statusBadge(doc.status)}</td>
                <td style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--teal)' }}>
                  {doc.chunks ? doc.chunks.toLocaleString() : '—'}
                </td>
                <td style={{ color: 'var(--text-muted)', fontSize: 11, fontFamily: 'var(--font-mono)' }}>{doc.uploadedAt}</td>
                <td>
                  <div style={{ display: 'flex', gap: 6 }}>
                    {doc.status === 'error' && (
                      <button className="btn btn-secondary btn-sm" title="Retry">↺</button>
                    )}
                    <button className="btn btn-danger btn-sm" onClick={() => handleDelete(doc.id)} title="Delete">✕</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {toast && (
        <div className="toast">
          <span style={{ color: 'var(--teal)' }}>◉</span>
          <span>{toast}</span>
        </div>
      )}
    </div>
  )
}
