import { useState, useRef, type Dispatch, type SetStateAction } from 'react'
import { Document } from '../utils/mockData'

type DocumentsPageProps = {
  documents: Document[]
  setDocuments: Dispatch<SetStateAction<Document[]>>
}

function mapBackendDocument(data: any): Document {
  const docType = (data.doc_type || '').toUpperCase()
  const rawFileUrl = data.file_url || data.file || ''
  const fileUrl = rawFileUrl && rawFileUrl !== '/media/' && rawFileUrl !== '/media'
    ? rawFileUrl.startsWith('/media/')
      ? `http://localhost:8000${rawFileUrl}`
      : rawFileUrl
    : ''

  return {
    id: data.id,
    name: data.name,
    doc_type: data.doc_type,
    type: docType === 'DOCX' ? 'DOCX' : docType === 'TXT' ? 'TXT' : 'PDF',
    size: data.file_size_display || data.size || `${Math.round((data.file_size || 0) / 1024)} KB`,
    file_size_display: data.file_size_display,
    file_url: fileUrl,
    status: data.status,
    uploadedAt: data.created_at ? data.created_at.split('T')[0] : new Date().toISOString().split('T')[0],
    chunk_count: data.chunk_count,
    chunks: data.chunk_count,
    created_at: data.created_at,
  }
}

function getDocumentResults(data: any): any[] {
  if (Array.isArray(data)) return data
  if (Array.isArray(data?.results)) return data.results
  return []
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

  const handleFiles = async (files: FileList) => {
    const allowed = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']
    const validFiles = Array.from(files).filter(f => {
      const name = f.name.toLowerCase()
      return allowed.includes(f.type) || name.endsWith('.pdf') || name.endsWith('.docx') || name.endsWith('.txt')
    })
    if (!validFiles.length) { showToast('Only PDF, DOCX, TXT files are accepted.'); return }

    setUploading(true)

    for (const file of validFiles) {
      const placeholderId = `doc-${Date.now()}-${Math.random().toString(36).slice(2,6)}`
      const ext = file.name.split('.').pop()?.toUpperCase() as Document['type']
      const placeholder: Document = {
        id: placeholderId,
        name: file.name,
        type: ext || 'PDF',
        size: `${(file.size / 1024 / 1024).toFixed(1)} MB`,
        status: 'processing',
        uploadedAt: new Date().toISOString().split('T')[0],
      }
      setDocuments(prev => [placeholder, ...prev])

      const formData = new FormData()
      formData.append('file', file)
      formData.append('hospital_name', '')
      formData.append('department', '')
      formData.append('notes', '')

      try {
        const response = await fetch('/api/documents/', {
          method: 'POST',
          body: formData,
        })

        if (!response.ok) {
          const errorData = await response.json().catch(() => null)
          showToast(`Upload failed: ${errorData?.error || response.statusText}`)
          setDocuments(prev => prev.filter(doc => doc.id !== placeholderId))
          continue
        }

        const data = await response.json()
        const savedDoc = mapBackendDocument(data)
        setDocuments(prev => prev.map(doc => doc.id === placeholderId ? savedDoc : doc))
        const listResponse = await fetch('/api/documents/')
        if (listResponse.ok) {
          const listData = await listResponse.json()
          setDocuments(getDocumentResults(listData).map(mapBackendDocument))
        }
      } catch (error) {
        console.error('Document upload failed:', error)
        showToast('Upload failed due to network error.')
        setDocuments(prev => prev.filter(doc => doc.id !== placeholderId))
      }
    }

    setUploading(false)
    showToast(`${validFiles.length} file(s) queued for indexing`)
  }

  const handleDelete = async (id: string) => {
    try {
      const response = await fetch(`/api/documents/${id}/`, { method: 'DELETE' })
      if (!response.ok) {
        showToast('Failed to delete document from backend.')
        return
      }
      setDocuments(prev => prev.filter(d => d.id !== id))
      showToast('Document removed from index')
    } catch (error) {
      console.error('Delete failed:', error)
      showToast('Failed to delete document due to network error.')
    }
  }

  const statusBadge = (status: Document['status']) => {
    const map: Record<Document['status'], { cls: string; label: string }> = {
      pending: { cls: 'badge-processing', label: 'Pending' },
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
                      {doc.file_url ? (
                        <a href={doc.file_url} target="_blank" rel="noreferrer" style={{ color: 'var(--text-primary)' }}>{doc.name}</a>
                      ) : (
                        doc.name
                      )}
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
