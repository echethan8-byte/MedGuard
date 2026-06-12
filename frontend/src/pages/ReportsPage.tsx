import { useState } from 'react'
import ScoreRing from '../components/ScoreRing'
import { mockReports, mockViolations, ComplianceReport } from '../utils/mockData'

export default function ReportsPage() {
  const [selected, setSelected] = useState<ComplianceReport>(mockReports[0])
  const [expandedViolation, setExpandedViolation] = useState<string | null>(null)

  const riskBadge = (risk: string) => {
    const map: Record<string, string> = { critical: 'badge-critical', high: 'badge-high', medium: 'badge-medium', low: 'badge-low' }
    return <span className={`badge ${map[risk] || 'badge-low'}`}>{risk.toUpperCase()}</span>
  }

  const riskOrder = ['critical', 'high', 'medium', 'low']
  const sortedViolations = [...selected.violations].sort(
    (a, b) => riskOrder.indexOf(a.risk) - riskOrder.indexOf(b.risk)
  )

  const riskCounts = (violations: typeof selected.violations) => ({
    critical: violations.filter(v => v.risk === 'critical').length,
    high: violations.filter(v => v.risk === 'high').length,
    medium: violations.filter(v => v.risk === 'medium').length,
    low: violations.filter(v => v.risk === 'low').length,
  })

  const downloadJSON = (report: ComplianceReport) => {
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `report-${report.id}.json`
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

  const downloadReport = (report: ComplianceReport) => {
    const html = `
      <html>
        <head>
          <title>Compliance Report - ${report.documentName}</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 24px; color: #111; background: #f8fafc; }
            .container { max-width: 900px; margin: auto; background: #fff; padding: 32px 34px; border-radius: 20px; box-shadow: 0 24px 48px rgba(15, 23, 42, 0.08); }
            h1 { font-size: 30px; margin-bottom: 4px; color: #0f172a; }
            h2 { font-size: 18px; margin-top: 28px; margin-bottom: 10px; color: #111827; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px; }
            p, li { font-size: 13px; line-height: 1.75; color: #334155; }
            .meta { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; margin-top: 18px; }
            .meta-item { background: #f1f5f9; padding: 14px 16px; border-radius: 14px; border: 1px solid #e2e8f0; }
            .meta-item strong { display: block; font-size: 11px; text-transform: uppercase; color: #64748b; margin-bottom: 4px; }
            .highlight { font-size: 28px; font-weight: 700; color: #0f172a; }
            .badge { display: inline-flex; align-items: center; gap: 6px; padding: 6px 10px; border-radius: 999px; font-size: 11px; font-weight: 700; text-transform: uppercase; }
            .badge-critical { background: #dc2626; color: #fff; }
            .badge-high { background: #f97316; color: #fff; }
            .badge-medium { background: #facc15; color: #0f172a; }
            .badge-low { background: #22c55e; color: #fff; }
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
            <h1>Compliance Report</h1>
            <p style="margin: 0 0 16px 0; color: #475569;">Standard healthcare compliance report for regulatory review, evidence, and corrective actions.</p>

            <div class="meta">
              <div class="meta-item"><strong>Document</strong>${report.documentName}</div>
              <div class="meta-item"><strong>Score</strong><span class="highlight">${report.score}/100</span></div>
              <div class="meta-item"><strong>Generated</strong>${new Date(report.generatedAt).toLocaleString()}</div>
              <div class="meta-item"><strong>Processing</strong>${report.processingTime}</div>
            </div>

            <div style="margin-top: 26px;">
              <h2>Summary</h2>
              <p>${report.summary}</p>
            </div>

            <div style="margin-top: 26px;">
              <h2>Findings Overview</h2>
              <table class="table">
                <thead>
                  <tr><th>Severity</th><th>Title</th><th>Category</th><th>Citation</th></tr>
                </thead>
                <tbody>
                  ${report.violations.map(v => `
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
              ${report.violations.map(v => `
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
              <h2>Referenced Citations</h2>
              <p>${report.citations.join(', ')}</p>
            </div>

            <div class="footer">Healthcare RAG compliance report · generated on ${new Date().toLocaleString()}</div>
          </div>
        </body>
      </html>`

    downloadHTML(html, `report-${report.id}.html`)
  }

  return (
    <div className="fade-in">
      <div className="page-header">
        <div className="page-eyebrow">Audit History</div>
        <div className="page-title">Compliance Reports</div>
        <div className="page-subtitle">Full audit trail with evidence, citations and corrective actions</div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: 16, alignItems: 'start' }}>

        {/* Report List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em', padding: '0 4px', marginBottom: 2 }}>
            {mockReports.length} Reports
          </div>
          {mockReports.map(report => {
            const counts = riskCounts(report.violations)
            const isSelected = selected.id === report.id
            return (
              <div
                key={report.id}
                onClick={() => { setSelected(report); setExpandedViolation(null) }}
                style={{
                  background: isSelected ? 'var(--bg-elevated)' : 'var(--bg-card)',
                  border: `1px solid ${isSelected ? 'var(--border-active)' : 'var(--border)'}`,
                  borderRadius: 'var(--radius)',
                  padding: '14px',
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <ScoreRing score={report.score} size={52} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginBottom: 3 }}>
                      {report.documentName}
                    </div>
                    <div style={{ fontSize: 10, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                      {new Date(report.generatedAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                    </div>
                    <div style={{ display: 'flex', gap: 4, marginTop: 6, flexWrap: 'wrap' }}>
                      {counts.critical > 0 && <span className="badge badge-critical" style={{ fontSize: 9, padding: '1px 6px' }}>{counts.critical} C</span>}
                      {counts.high > 0 && <span className="badge badge-high" style={{ fontSize: 9, padding: '1px 6px' }}>{counts.high} H</span>}
                      {counts.medium > 0 && <span className="badge badge-medium" style={{ fontSize: 9, padding: '1px 6px' }}>{counts.medium} M</span>}
                      {counts.low > 0 && <span className="badge badge-low" style={{ fontSize: 9, padding: '1px 6px' }}>{counts.low} L</span>}
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Report Detail */}
        <div>
          {/* Header */}
          <div className="card" style={{ marginBottom: 14 }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 20 }}>
              <ScoreRing score={selected.score} size={90} />
              <div style={{ flex: 1 }}>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--teal)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 4 }}>{selected.id}</div>
                <div style={{ fontFamily: 'var(--font-display)', fontSize: 17, fontWeight: 700, marginBottom: 6 }}>{selected.documentName}</div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.7, marginBottom: 12 }}>{selected.summary}</div>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 12 }}>
                  {['critical', 'high', 'medium', 'low'].map(risk => {
                    const c = selected.violations.filter(v => v.risk === risk).length
                    return c > 0 ? <span key={risk} className={`badge badge-${risk}`}>{c} {risk}</span> : null
                  })}
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button className="btn btn-primary btn-sm" onClick={() => downloadReport(selected)}>⬇ Download Report</button>
                  <button className="btn btn-secondary btn-sm" onClick={() => downloadJSON(selected)}>Export JSON</button>
                  <button className="btn btn-secondary btn-sm">⊞ Share Report</button>
                </div>
              </div>
              <div style={{ flexShrink: 0, minWidth: 140 }}>
                <div style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8 }}>Report Details</div>
                {[
                  ['Generated', new Date(selected.generatedAt).toLocaleDateString()],
                  ['Violations', selected.violations.length],
                  ['Citations', selected.citations.length],
                  ['Processing', selected.processingTime],
                ].map(([k, v]) => (
                  <div key={k as string} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                    <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{k}</span>
                    <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>{v}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Citations */}
          <div className="card" style={{ marginBottom: 14 }}>
            <div className="card-title" style={{ marginBottom: 10 }}>Policy Sources Referenced</div>
            <div className="tag-group">
              {selected.citations.map((c, i) => (
                <span key={i} className="code-label" style={{ fontSize: 11 }}>{c}</span>
              ))}
            </div>
          </div>

          {/* Violations */}
          <div style={{ marginBottom: 8, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div className="card-title">Findings & Recommendations</div>
            <span className="code-label">{sortedViolations.length} violations</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {sortedViolations.map(v => (
              <div key={v.id} className="violation-card">
                <div className="violation-card-header" onClick={() => setExpandedViolation(expandedViolation === v.id ? null : v.id)}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3, flexWrap: 'wrap' }}>
                      {riskBadge(v.risk)}
                      <span className="code-label" style={{ fontSize: 10 }}>{v.regulationId}</span>
                      <span style={{ fontSize: 10, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{v.category}</span>
                    </div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>{v.title}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {v.description.substring(0, 90)}…
                    </div>
                  </div>
                  <span style={{ color: 'var(--text-muted)', fontSize: 14, flexShrink: 0, marginLeft: 8 }}>
                    {expandedViolation === v.id ? '▲' : '▼'}
                  </span>
                </div>
                {expandedViolation === v.id && (
                  <div className="violation-card-body fade-in">
                    <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 12, lineHeight: 1.7 }}>{v.description}</div>
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
      </div>
    </div>
  )
}
