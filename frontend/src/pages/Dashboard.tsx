import { useState, useEffect } from 'react'
import ScoreRing from '../components/ScoreRing'
import { mockDocuments, mockReports, mockViolations } from '../utils/mockData'
import { Page } from '../App'

interface DashboardProps {
  onNavigate: (page: Page) => void
}

export default function Dashboard({ onNavigate }: DashboardProps) {
  const [mounted, setMounted] = useState(false)
  useEffect(() => { setMounted(true) }, [])

  const avgScore = Math.round(mockReports.reduce((s, r) => s + r.score, 0) / mockReports.length)
  const criticalCount = mockViolations.filter(v => v.risk === 'critical').length
  const highCount = mockViolations.filter(v => v.risk === 'high').length
  const readyDocs = mockDocuments.filter(d => d.status === 'indexed' || d.status === 'ready').length

  const categoryBreakdown = [
    { label: 'Infection Control', value: 42, color: '#EF4444' },
    { label: 'HAI Prevention', value: 67, color: '#F59E0B' },
    { label: 'Critical Care', value: 55, color: '#F59E0B' },
    { label: 'Occupational Safety', value: 80, color: '#10B981' },
    { label: 'Isolation Protocols', value: 73, color: '#10B981' },
    { label: 'MDRO Control', value: 88, color: '#10B981' },
  ]

  const recentActivity = [
    { time: '09:42', event: 'Audit completed', doc: 'ICU_Infection_Control_Procedure.pdf', score: 61 },
    { time: '08:15', event: 'Document indexed', doc: 'Antibiotic_Stewardship_Policy_v3.docx', score: null },
    { time: 'Jun 8', event: 'Audit completed', doc: 'Surgical_Site_Prevention_Protocol.pdf', score: 78 },
    { time: 'Jun 5', event: 'Audit completed', doc: 'Hand_Hygiene_Compliance_Report_Q2.pdf', score: 91 },
  ]

  return (
    <div className="fade-in">
      <div className="page-header">
        <div className="page-eyebrow">System Overview</div>
        <div className="page-title">Compliance Dashboard</div>
        <div className="page-subtitle">Healthcare policy violation detection · RAG-powered analysis</div>
      </div>

      {/* Stats Row */}
      <div className="stats-row">
        <div className="stat-card" style={{ '--accent': '#EF4444' } as React.CSSProperties}>
          <div className="stat-label">Critical Violations</div>
          <div className="stat-value" style={{ color: '#EF4444' }}>{criticalCount}</div>
          <div className="stat-sub">Across {mockReports.length} reports</div>
          <div className="stat-trend trend-down">▲ Requires immediate action</div>
        </div>
        <div className="stat-card" style={{ '--accent': '#F59E0B' } as React.CSSProperties}>
          <div className="stat-label">High Risk Findings</div>
          <div className="stat-value" style={{ color: '#F59E0B' }}>{highCount}</div>
          <div className="stat-sub">Action within 30 days</div>
          <div className="stat-trend trend-neutral">— Stable this week</div>
        </div>
        <div className="stat-card" style={{ '--accent': '#3B82F6' } as React.CSSProperties}>
          <div className="stat-label">Indexed Documents</div>
          <div className="stat-value">{readyDocs}</div>
          <div className="stat-sub">Of {mockDocuments.length} total</div>
          <div className="stat-trend trend-up">▲ 2 added today</div>
        </div>
        <div className="stat-card" style={{ '--accent': '#10B981' } as React.CSSProperties}>
          <div className="stat-label">Avg Compliance</div>
          <div className="stat-value" style={{ color: '#F59E0B' }}>{avgScore}%</div>
          <div className="stat-sub">Rolling 30-day average</div>
          <div className="stat-trend trend-up">▲ +4pts from last month</div>
        </div>
      </div>

      {/* Main Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>

        {/* Compliance by Category */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">Compliance by Category</div>
            <span className="code-label">6 domains</span>
          </div>
          {categoryBreakdown.map((item, i) => (
            <div key={i} className="chart-bar-wrap">
              <div className="chart-bar-label">{item.label}</div>
              <div className="chart-bar-track">
                <div
                  className="chart-bar-fill"
                  style={{
                    width: mounted ? `${item.value}%` : '0%',
                    background: item.color,
                    boxShadow: `0 0 6px ${item.color}60`,
                    transitionDelay: `${i * 80}ms`
                  }}
                />
              </div>
              <div className="chart-bar-value" style={{ color: item.color }}>{item.value}</div>
            </div>
          ))}
        </div>

        {/* Recent Reports */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">Recent Reports</div>
            <button className="btn btn-ghost btn-sm" onClick={() => onNavigate('reports')}>View all →</button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {mockReports.map(report => (
              <div key={report.id} style={{
                display: 'flex', alignItems: 'center', gap: 12,
                padding: '10px 12px', background: 'var(--bg-elevated)',
                borderRadius: 8, border: '1px solid var(--border)'
              }}>
                <ScoreRing score={report.score} size={52} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {report.documentName}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginTop: 2 }}>
                    {report.violations.length} violations · {new Date(report.generatedAt).toLocaleDateString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Activity + Quick Actions row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 16 }}>

        {/* Recent Activity */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">Audit Activity Log</div>
            <span className="code-label">Today</span>
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Event</th>
                <th>Document</th>
                <th>Score</th>
              </tr>
            </thead>
            <tbody>
              {recentActivity.map((item, i) => (
                <tr key={i}>
                  <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', fontSize: 11 }}>{item.time}</td>
                  <td style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{item.event}</td>
                  <td style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--teal)', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: 180, whiteSpace: 'nowrap' }}>
                    {item.doc}
                  </td>
                  <td>
                    {item.score !== null ? (
                      <span style={{
                        fontFamily: 'var(--font-mono)', fontWeight: 600, fontSize: 12,
                        color: item.score >= 80 ? '#10B981' : item.score >= 60 ? '#F59E0B' : '#EF4444'
                      }}>{item.score}</span>
                    ) : (
                      <span style={{ color: 'var(--text-muted)', fontSize: 11 }}>—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Quick Actions */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div className="card-title" style={{ marginBottom: 6 }}>Quick Actions</div>
          <button className="btn btn-primary" style={{ justifyContent: 'center' }} onClick={() => onNavigate('audit')}>
            ◈ Run Compliance Audit
          </button>
          <button className="btn btn-secondary" style={{ justifyContent: 'center' }} onClick={() => onNavigate('documents')}>
            ⬢ Upload Document
          </button>
          <button className="btn btn-secondary" style={{ justifyContent: 'center' }} onClick={() => onNavigate('reports')}>
            ◉ View Latest Report
          </button>
          <div className="divider" />
          <div style={{ background: 'var(--bg-elevated)', borderRadius: 8, padding: '12px 14px' }}>
            <div style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8 }}>Corpus Status</div>
            <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 6 }}>
              <span style={{ color: 'var(--teal)', fontFamily: 'var(--font-mono)' }}>5,847</span> policy pages indexed
            </div>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: '94%', background: 'var(--teal)' }} />
            </div>
            <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4, fontFamily: 'var(--font-mono)' }}>
              WHO · CDC · HHS · OSHA · TJC
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
