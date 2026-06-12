import { useState, useEffect, useRef } from 'react'
import ScoreRing from '../components/ScoreRing'
import { Document, mockViolations, mockReport } from '../utils/mockData'

type AuditStage = 'idle' | 'retrieval' | 'reranking' | 'cot' | 'validation' | 'done'

type AuditPageProps = {
  documents: Document[]
}

const STAGE_MESSAGES: Record<AuditStage, string[]> = {
  idle: [],
  retrieval: [
    '> Embedding query vector (all-MiniLM-L6-v2)…',
    '> Searching ChromaDB · healthcare_policies collection…',
    '> Retrieved 20 candidate chunks from 5,847 pages',
    '> Applying metadata filters: source=WHO,CDC,HHS,OSHA,TJC',
  ],
  reranking: [
    '> Loading FlashRank cross-encoder model…',
    '> Reranking 20 → 8 top relevant passages',
    '> Chunk similarity scores: [0.94, 0.91, 0.87, 0.83, 0.79, 0.76, 0.72, 0.68]',
  ],
  cot: [
    '> Constructing Chain-of-Thought prompt (Gemini 2.5 Flash)…',
    '> Step 1: Summarizing hospital document procedures…',
    '> Step 2: Mapping each procedure to retrieved policies…',
    '> Step 3: Identifying compliance gaps and mismatches…',
    '> Step 4: Assessing risk levels (Critical/High/Medium/Low)…',
    '> Step 5: Generating corrective action recommendations…',
    '> LLM response received · 2,847 tokens',
  ],
  validation: [
    '> Running output guardrails validation…',
    '> Checking citation accuracy against retrieved chunks…',
    '> PII scan: no protected health information detected',
    '> NLI validation: all violations grounded in evidence ✓',
    '> Structuring JSON report…',
  ],
  done: [],
}

export default function AuditPage({ documents }: AuditPageProps) {
  const [selectedDocId, setSelectedDocId] = useState('')
  const [stage, setStage] = useState<AuditStage>('idle')
  const [terminalLines, setTerminalLines] = useState<{ text: string; type: string }[]>([])
  const [stageProgress, setStageProgress] = useState(0)
  const [showResults, setShowResults] = useState(false)
  const [expandedViolation, setExpandedViolation] = useState<string | null>(null)
  const termRef = useRef<HTMLDivElement>(null)

  const indexedDocs = documents.filter(d => d.status === 'indexed')
  const selectedDoc = documents.find(d => d.id === selectedDocId)

  const addLines = (lines: string[], type = 'default', delay = 300) => {
    lines.forEach((line, i) => {
      setTimeout(() => {
        setTerminalLines(prev => [...prev, { text: line, type }])
        if (termRef.current) termRef.current.scrollTop = termRef.current.scrollHeight
      }, i * delay)
    })
    return lines.length * delay
  }

  const runAudit = async () => {
    if (!selectedDocId) return
    setShowResults(false)
    setTerminalLines([])
    setStageProgress(0)

    const stages: AuditStage[] = ['retrieval', 'reranking', 'cot', 'validation']
    let elapsed = 0

    setTerminalLines([{ text: `> Initiating compliance audit for: ${selectedDoc?.name || 'selected document'}`, type: 'success' }])
    elapsed += 400

    for (let si = 0; si < stages.length; si++) {
      const s = stages[si]
      setTimeout(() => {
        setStage(s)
        setStageProgress(si + 1)
      }, elapsed)
      elapsed += 200

      const msgs = STAGE_MESSAGES[s]
      msgs.forEach((line, i) => {
        setTimeout(() => {
          const lineType = line.includes('✓') ? 'success' : line.includes('!') ? 'warn' : 'default'
          setTerminalLines(prev => [...prev, { text: line, type: lineType }])
          if (termRef.current) termRef.current.scrollTop = termRef.current.scrollHeight
        }, elapsed + i * 280)
      })
      elapsed += msgs.length * 280 + 300
    }

    setTimeout(() => {
      setTerminalLines(prev => [
        ...prev,
        { text: '> ─────────────────────────────────────────', type: 'default' },
        { text: `> Audit complete · Score: ${mockReport.score}/100 · ${mockReport.violations.length} violations found`, type: 'success' },
        { text: `> Processing time: ${mockReport.processingTime}`, type: 'default' },
      ])
      setStage('done')
      setTimeout(() => setShowResults(true), 600)
    }, elapsed)
  }

  const stageLabels = ['Retrieval', 'Reranking', 'CoT Analysis', 'Guardrails']

  const downloadJSON = () => {
    const payload = {
      report: mockReport,
      document: selectedDoc?.name || 'selected document',
      generatedAt: new Date().toISOString(),
    }
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `audit-report-${selectedDoc?.id || 'unknown'}.json`
    anchor.click()
    URL.revokeObjectURL(url)
  }

  const downloadHTML = (html: string, filename: string) => {
    const blob = new Blob([html], { type: 'text/html' })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = filename
    anchor.click()
    URL.revokeObjectURL(url)
  }

  const downloadReport = () => {
    const docName = selectedDoc?.name || 'document'
    const html = `
      <html>
        <head>
          <title>Audit Report - ${docName}</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 24px; color: #111; background: #f3f4f6; }
            .container { max-width: 900px; margin: auto; background: #fff; padding: 32px 34px; border-radius: 20px; box-shadow: 0 24px 48px rgba(15, 23, 42, 0.08); }
            h1 { font-size: 30px; margin-bottom: 4px; color: #0f172a; }
            h2 { font-size: 18px; margin-top: 28px; margin-bottom: 10px; color: #111827; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px; }
            p, li { font-size: 13px; line-height: 1.75; color: #334155; }
            .meta { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; margin-top: 18px; }
            .meta-item { background: #f8fafc; padding: 14px 16px; border-radius: 14px; border: 1px solid #e2e8f0; }
            .meta-item strong { display: block; font-size: 11px; text-transform: uppercase; color: #64748b; margin-bottom: 4px; }
            .highlight { font-size: 30px; font-weight: 700; color: #0f172a; }
            .badge { display: inline-flex; align-items: center; gap: 6px; padding: 6px 10px; border-radius: 999px; font-size: 11px; font-weight: 700; color: #fff; text-transform: uppercase; }
            .badge-critical { background: #dc2626; }
            .badge-high { background: #f97316; }
            .badge-medium { background: #fbbf24; color: #0f2937; }
            .badge-low { background: #22c55e; }
            .table { width: 100%; border-collapse: collapse; margin-top: 12px; }
            .table th, .table td { text-align: left; padding: 12px 14px; border-bottom: 1px solid #e2e8f0; }
            .table th { background: #f8fafc; font-size: 12px; color: #475569; text-transform: uppercase; letter-spacing: 0.05em; }
            .finding { margin-top: 20px; padding: 18px 20px; border-radius: 16px; background: #f8fafc; border: 1px solid #e2e8f0; }
            .finding h3 { margin: 0 0 10px 0; font-size: 16px; color: #0f172a; }
            .finding p { margin: 6px 0; }
            .footer { margin-top: 32px; font-size: 12px; color: #64748b; }
          </style>
        </head>
        <body>
          <div class="container">
            <h1>Compliance Audit Report</h1>
            <p style="margin: 0 0 16px 0; color: #475569;">Standard healthcare compliance report for regulatory review and corrective action planning.</p>

            <div class="meta">
              <div class="meta-item"><strong>Document</strong>${docName}</div>
              <div class="meta-item"><strong>Score</strong><span class="highlight">${mockReport.score}/100</span></div>
              <div class="meta-item"><strong>Processing Time</strong>${mockReport.processingTime}</div>
              <div class="meta-item"><strong>Findings</strong>${mockViolations.length} issues</div>
            </div>

            <div style="margin-top: 26px;">
              <h2>Executive Summary</h2>
              <p>${mockReport.summary}</p>
            </div>

            <div style="margin-top: 26px;">
              <h2>Findings Overview</h2>
              <table class="table">
                <thead>
                  <tr><th>Severity</th><th>Title</th><th>Category</th><th>Citation</th></tr>
                </thead>
                <tbody>
                  ${mockReport.violations.map(v => `
                    <tr>
                      <td><span class="badge badge-${v.risk}">${v.risk.toUpperCase()}</span></td>
                      <td>${v.title}</td>
                      <td>${v.category}</td>
                      <td>${v.citation || 'N/A'}</td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            </div>

            <div style="margin-top: 26px;">
              <h2>Detailed Findings & Corrective Actions</h2>
              ${mockReport.violations.map(v => `
                <div class="finding">
                  <h3>${v.title} <span style="font-size:12px; color:#475569;">(${v.risk.toUpperCase()})</span></h3>
                  <p><strong>Regulation:</strong> ${v.regulationId} | <strong>Category:</strong> ${v.category}</p>
                  <p><strong>Description:</strong> ${v.description}</p>
                  <p><strong>Evidence:</strong> ${v.evidence}</p>
                  <p><strong>Citation:</strong> ${v.citation}</p>
                  <p><strong>Corrective Action:</strong> ${v.correctiveAction}</p>
                </div>
              `).join('')}
            </div>

            <div style="margin-top: 26px;">
              <h2>Citations</h2>
              <p>${mockReport.citations.join(', ')}</p>
            </div>

            <div class="footer">Generated on ${new Date().toLocaleString()} · Healthcare RAG Compliance Report</div>
          </div>
        </body>
      </html>`

    downloadHTML(html, `audit-report-${selectedDoc?.id || 'unknown'}.html`)
  }

  const downloadPDF = () => {
    downloadReport()
  }

  const riskBadge = (risk: string) => {
    const map: Record<string, string> = { critical: 'badge-critical', high: 'badge-high', medium: 'badge-medium', low: 'badge-low' }
    return <span className={`badge ${map[risk] || 'badge-low'}`}>{risk.toUpperCase()}</span>
  }

  const riskOrder = ['critical', 'high', 'medium', 'low']
  const sortedViolations = [...mockViolations].sort(
    (a, b) => riskOrder.indexOf(a.risk) - riskOrder.indexOf(b.risk)
  )

  return (
    <div className="fade-in">
      <div className="page-header">
        <div className="page-eyebrow">RAG · Chain-of-Thought</div>
        <div className="page-title">Compliance Audit</div>
        <div className="page-subtitle">Retrieve · Rerank · Analyze · Validate against 5,847 policy pages</div>
      </div>

      {/* Config Panel */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
        <div className="card">
          <div className="card-title" style={{ marginBottom: 14 }}>Audit Configuration</div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>
              Select Document
            </label>
            <select
              className="input"
              value={selectedDocId}
              onChange={e => setSelectedDocId(e.target.value)}
              disabled={stage !== 'idle' && stage !== 'done'}
            >
              <option value="">— Choose indexed document —</option>
              {indexedDocs.map(d => (
                <option key={d.id} value={d.id}>{d.name}</option>
              ))}
            </select>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 14 }}>
            <div>
              <label style={{ display: 'block', fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>LLM Model</label>
              <select className="input"><option>Gemini 2.5 Flash</option><option>Gemini 1.5 Pro</option><option>GPT-4o</option></select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>Top-K Chunks</label>
              <select className="input"><option>8 (recommended)</option><option>5 (fast)</option><option>12 (thorough)</option></select>
            </div>
          </div>
          <button
            className="btn btn-primary"
            style={{ width: '100%', justifyContent: 'center', fontSize: 14 }}
            onClick={runAudit}
            disabled={!selectedDocId || (stage !== 'idle' && stage !== 'done')}
          >
            {stage !== 'idle' && stage !== 'done' ? (
              <><span className="spinner" /> Running Analysis…</>
            ) : '◈ Run Compliance Audit'}
          </button>
        </div>

        <div className="card">
          <div className="card-title" style={{ marginBottom: 14 }}>Pipeline Progress</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {stageLabels.map((label, i) => {
              const isActive = stageProgress === i + 1
              const isDone = stageProgress > i + 1 || stage === 'done'
              return (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <div style={{
                    width: 28, height: 28, borderRadius: 6,
                    background: isDone ? 'var(--green-dim)' : isActive ? 'var(--teal-dim)' : 'var(--bg-elevated)',
                    border: `1px solid ${isDone ? 'rgba(16,185,129,0.35)' : isActive ? 'var(--border-active)' : 'var(--border)'}`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 12, fontFamily: 'var(--font-mono)', fontWeight: 600,
                    color: isDone ? '#10B981' : isActive ? 'var(--teal)' : 'var(--text-muted)',
                    flexShrink: 0, transition: 'all 0.3s',
                  }}>
                    {isDone ? '✓' : i + 1}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 12, fontWeight: 500, color: isDone || isActive ? 'var(--text-primary)' : 'var(--text-muted)' }}>{label}</div>
                  </div>
                  {isActive && <span className="spinner" />}
                </div>
              )
            })}
          </div>
          {stage === 'done' && (
            <div style={{ marginTop: 14, padding: '10px 14px', background: 'var(--green-dim)', border: '1px solid rgba(16,185,129,0.3)', borderRadius: 8, fontSize: 12, color: '#10B981', fontFamily: 'var(--font-mono)' }}>
              ✓ Analysis complete · {mockReport.processingTime}
            </div>
          )}
        </div>
      </div>

      {/* Terminal */}
      {terminalLines.length > 0 && (
        <div className="card scan-effect" style={{ marginBottom: 20, padding: 0 }}>
          <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 8 }}>
            <div className="status-dot" />
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)' }}>ANALYSIS TERMINAL</span>
          </div>
          <div className="terminal-block" ref={termRef} style={{ maxHeight: 180, borderRadius: 0, borderLeft: 'none', borderRight: 'none', borderBottom: 'none' }}>
            {terminalLines.map((line, i) => (
              <div key={i} className={
                line.type === 'success' ? 'terminal-line-success' :
                line.type === 'warn' ? 'terminal-line-warn' :
                line.type === 'error' ? 'terminal-line-error' : 'terminal-line-muted'
              }>{line.text}</div>
            ))}
          </div>
        </div>
      )}

      {/* Results */}
      {showResults && (
        <div className="fade-in">
          {/* Score + summary */}
          <div className="score-ring-wrapper" style={{ marginBottom: 16 }}>
            <ScoreRing score={mockReport.score} size={110} />
            <div style={{ flex: 1 }}>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 18, fontWeight: 700, marginBottom: 4 }}>
                Compliance Score: <span style={{ color: '#F59E0B' }}>{mockReport.score}/100</span>
              </div>
              <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.7, marginBottom: 10 }}>
                {mockReport.summary}
              </div>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {['critical', 'high', 'medium', 'low'].map(risk => {
                  const count = mockViolations.filter(v => v.risk === risk).length
                  return count > 0 ? (
                    <span key={risk} className={`badge badge-${risk}`}>{count} {risk}</span>
                  ) : null
                })}
              </div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, flexShrink: 0 }}>
              <button className="btn btn-primary btn-sm" onClick={downloadPDF}>⬇ Export PDF</button>
              <button className="btn btn-secondary btn-sm" onClick={downloadJSON}>Export JSON</button>
            </div>
          </div>

          {/* Violations */}
          <div style={{ marginBottom: 8, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div className="card-title">Violations Detected</div>
            <span className="code-label">{mockViolations.length} findings</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {sortedViolations.map(v => (
              <div key={v.id} className="violation-card">
                <div className="violation-card-header" onClick={() => setExpandedViolation(expandedViolation === v.id ? null : v.id)}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3 }}>
                      {riskBadge(v.risk)}
                      <span className="code-label" style={{ fontSize: 10 }}>{v.regulationId}</span>
                      <span style={{ fontSize: 10, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{v.category}</span>
                    </div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>{v.title}</div>
                  </div>
                  <span style={{ color: 'var(--text-muted)', fontSize: 14, flexShrink: 0 }}>
                    {expandedViolation === v.id ? '▲' : '▼'}
                  </span>
                </div>

                {expandedViolation === v.id && (
                  <div className="violation-card-body fade-in">
                    <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 12, lineHeight: 1.7 }}>
                      {v.description}
                    </div>
                    <div className="violation-evidence">
                      <div className="violation-evidence-label">Evidence from Document</div>
                      {v.evidence}
                    </div>
                    <div style={{ marginTop: 10 }}>
                      <div style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--teal)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 4 }}>Policy Citation</div>
                      <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{v.citation}</div>
                    </div>
                    <div style={{ marginTop: 10, padding: '10px 12px', background: 'var(--green-dim)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: 6 }}>
                      <div style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: '#10B981', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 4 }}>Corrective Action</div>
                      <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{v.correctiveAction}</div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
