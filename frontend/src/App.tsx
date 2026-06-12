import { useState } from 'react'
import Dashboard from './pages/Dashboard'
import AuditPage from './pages/AuditPage'
import DocumentsPage from './pages/DocumentsPage'
import ReportsPage from './pages/ReportsPage'
import Sidebar from './components/Sidebar'
import { Document, mockDocuments } from './utils/mockData'
import './App.css'

export type Page = 'dashboard' | 'documents' | 'audit' | 'reports'

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('dashboard')
  const [documents, setDocuments] = useState<Document[]>(mockDocuments)

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard': return <Dashboard onNavigate={setCurrentPage} />
      case 'documents': return <DocumentsPage documents={documents} setDocuments={setDocuments} />
      case 'audit': return <AuditPage documents={documents} />
      case 'reports': return <ReportsPage />
      default: return <Dashboard onNavigate={setCurrentPage} />
    }
  }

  return (
    <div className="app-shell">
      <Sidebar currentPage={currentPage} onNavigate={setCurrentPage} />
      <main className="main-content">
        {renderPage()}
      </main>
    </div>
  )
}

export default App
