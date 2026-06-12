import { Page } from '../App'

interface SidebarProps {
  currentPage: Page
  onNavigate: (page: Page) => void
}

const navItems: { id: Page; icon: string; label: string; badge?: string }[] = [
  { id: 'dashboard', icon: '⬡', label: 'Overview' },
  { id: 'documents', icon: '⬢', label: 'Documents', badge: '3' },
  { id: 'audit', icon: '◈', label: 'Run Audit' },
  { id: 'reports', icon: '◉', label: 'Reports' },
]

export default function Sidebar({ currentPage, onNavigate }: SidebarProps) {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-mark">
          <div className="logo-icon">⚕</div>
          <div>
            <div className="logo-text">MedGuard</div>
            <div className="logo-sub">RAG · Compliance</div>
          </div>
        </div>
      </div>

      <nav className="sidebar-nav">
        <div className="nav-section-label">Navigation</div>
        {navItems.map(item => (
          <button
            key={item.id}
            className={`nav-item ${currentPage === item.id ? 'active' : ''}`}
            onClick={() => onNavigate(item.id)}
          >
            <span className="nav-icon">{item.icon}</span>
            {item.label}
            {item.badge && <span className="nav-badge">{item.badge}</span>}
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="system-status">
          <span className="status-dot" />
          <span>System operational</span>
        </div>
        <div style={{ height: 8 }} />
        <div className="system-status" style={{ fontSize: 10, opacity: 0.6 }}>
          API · v2.4.1 · Gemini 2.5
        </div>
      </div>
    </aside>
  )
}
