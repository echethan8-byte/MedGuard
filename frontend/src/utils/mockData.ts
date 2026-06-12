export interface Document {
  id: string
  name: string
  type: 'PDF' | 'DOCX' | 'TXT'
  size: string
  status: 'processing' | 'ready' | 'error' | 'indexed'
  uploadedAt: string
  chunks?: number
}

export interface Violation {
  id: string
  regulationId: string
  title: string
  description: string
  risk: 'critical' | 'high' | 'medium' | 'low'
  evidence: string
  citation: string
  correctiveAction: string
  category: string
}

export interface ComplianceReport {
  id: string
  documentName: string
  score: number
  generatedAt: string
  violations: Violation[]
  summary: string
  citations: string[]
  processingTime: string
}

export const mockDocuments: Document[] = [
  {
    id: 'doc-001',
    name: 'ICU_Infection_Control_Procedure.pdf',
    type: 'PDF',
    size: '2.4 MB',
    status: 'indexed',
    uploadedAt: '2025-06-09',
    chunks: 147,
  },
  {
    id: 'doc-002',
    name: 'Surgical_Site_Prevention_Protocol.pdf',
    type: 'PDF',
    size: '1.8 MB',
    status: 'indexed',
    uploadedAt: '2025-06-09',
    chunks: 98,
  },
  {
    id: 'doc-003',
    name: 'Antibiotic_Stewardship_Policy_v3.docx',
    type: 'DOCX',
    size: '890 KB',
    status: 'processing',
    uploadedAt: '2025-06-10',
  },
  {
    id: 'doc-004',
    name: 'Hand_Hygiene_Compliance_Report_Q2.pdf',
    type: 'PDF',
    size: '560 KB',
    status: 'ready',
    uploadedAt: '2025-06-10',
    chunks: 34,
  },
  {
    id: 'doc-005',
    name: 'PPE_Usage_Guidelines_2024.pdf',
    type: 'PDF',
    size: '3.1 MB',
    status: 'error',
    uploadedAt: '2025-06-10',
  },
]

export const mockViolations: Violation[] = [
  {
    id: 'v-001',
    regulationId: 'WHO-IPC-2.3',
    title: 'Hand Hygiene Protocol Gap',
    description: 'Document specifies hand hygiene only before invasive procedures, omitting the WHO-mandated "5 Moments" framework including before patient contact and after touching patient surroundings.',
    risk: 'critical',
    evidence: 'Section 4.2: "Staff must wash hands before any invasive procedure using hospital-grade antiseptic soap for minimum 15 seconds." — Missing: after touching patient, after body fluid exposure, after touching patient surroundings.',
    citation: 'WHO IPC Guidelines 2022, Section 2.3: "The Five Moments for Hand Hygiene"',
    correctiveAction: 'Update Section 4.2 to include all five WHO moments. Implement poster compliance in all wards. Schedule refresher training within 30 days.',
    category: 'Infection Control',
  },
  {
    id: 'v-002',
    regulationId: 'CDC-NHSN-4.1',
    title: 'CLABSI Prevention Incomplete',
    description: 'Central-line insertion checklist is missing maximal barrier precautions and chlorhexidine skin antisepsis requirements per CDC NHSN protocol.',
    risk: 'high',
    evidence: 'Appendix B Checklist: sterile gloves ✓, sterile gown ✓ — Missing entries for: sterile drape (full body), chlorhexidine prep, mask and cap requirement.',
    citation: 'CDC NHSN CLABSI Protocol 2023, Section 4.1.2',
    correctiveAction: 'Revise Appendix B to include full CDC NHSN insertion bundle. Validate with infection control nurse before re-issue.',
    category: 'HAI Prevention',
  },
  {
    id: 'v-003',
    regulationId: 'HHS-HAP-7.2',
    title: 'Ventilator Bundle Non-Compliance',
    description: 'Ventilator-associated pneumonia (VAP) prevention bundle is missing oral care with chlorhexidine every 6 hours as mandated by HHS guidelines.',
    risk: 'high',
    evidence: 'Section 7.1 VAP Bundle: Head-of-bed elevation 30-45° ✓, Daily sedation vacation ✓, DVT prophylaxis ✓ — Oral care with chlorhexidine: NOT LISTED.',
    citation: 'HHS Hospital-Acquired Pneumonia Prevention Guideline, Section 7.2',
    correctiveAction: 'Add oral care protocol to VAP bundle. Source chlorhexidine 0.12% oral rinse. Train ICU nursing staff.',
    category: 'Critical Care',
  },
  {
    id: 'v-004',
    regulationId: 'OSHA-BBP-1910.1030',
    title: 'Bloodborne Pathogen Exposure Procedures',
    description: 'Post-exposure prophylaxis timeline listed as "within 4 hours" — OSHA mandates "as soon as possible, within 2 hours" for maximum efficacy.',
    risk: 'medium',
    evidence: 'Section 9.3: "In the event of needlestick or sharps injury, staff must report to occupational health within 4 hours for PEP evaluation."',
    citation: 'OSHA 29 CFR 1910.1030 Bloodborne Pathogens Standard, Appendix B',
    correctiveAction: 'Amend Section 9.3 to reflect 2-hour window. Update signage in all clinical areas. Notify HR for policy revision.',
    category: 'Occupational Safety',
  },
  {
    id: 'v-005',
    regulationId: 'TJC-IC.02.02.01',
    title: 'Isolation Precaution Signage',
    description: 'Policy does not specify required door signage types for different transmission-based precautions (contact, droplet, airborne) per Joint Commission standards.',
    risk: 'medium',
    evidence: 'Section 6.1: "Isolation rooms will be clearly marked." — No specification of precaution type, required PPE notice, or visitor restriction instructions.',
    citation: 'The Joint Commission IC.02.02.01, EP 4',
    correctiveAction: 'Develop distinct signage templates for each precaution type. Include PPE requirements and visitor policy on each sign.',
    category: 'Isolation Precautions',
  },
  {
    id: 'v-006',
    regulationId: 'CDC-MDRO-3.5',
    title: 'MDRO Screening Frequency',
    description: 'MRSA screening on admission is listed as optional for low-risk patients. CDC guidelines mandate universal admission screening in ICU settings.',
    risk: 'low',
    evidence: 'Section 3.2: "MRSA nasal swab screening on admission is recommended for high-risk patients as defined by clinician assessment."',
    citation: 'CDC MDRO Management Guideline 2023, Section 3.5',
    correctiveAction: 'Change ICU admission protocol to mandatory universal MRSA screening. Update order sets in EHR.',
    category: 'MDRO Control',
  },
]

export const mockReport: ComplianceReport = {
  id: 'rpt-001',
  documentName: 'ICU_Infection_Control_Procedure.pdf',
  score: 61,
  generatedAt: '2025-06-10T09:42:31Z',
  violations: mockViolations,
  summary: 'The ICU Infection Control Procedure document demonstrates partial compliance with current healthcare regulatory standards. Critical gaps were identified in hand hygiene protocols (WHO 5 Moments), CLABSI prevention bundles, and VAP prevention care bundles. Immediate corrective action is recommended for the 2 critical and 2 high-risk findings before next audit cycle.',
  citations: [
    'WHO IPC Guidelines 2022',
    'CDC NHSN Protocol 2023',
    'HHS HAP Prevention Guideline',
    'OSHA 29 CFR 1910.1030',
    'The Joint Commission IC.02.02.01',
    'CDC MDRO Management Guideline 2023',
  ],
  processingTime: '4.2s',
}

export const mockReports: ComplianceReport[] = [
  mockReport,
  {
    id: 'rpt-002',
    documentName: 'Surgical_Site_Prevention_Protocol.pdf',
    score: 78,
    generatedAt: '2025-06-08T14:20:00Z',
    violations: mockViolations.slice(0, 3),
    summary: 'Surgical site prevention protocol shows good alignment with CDC SSI Prevention guidelines with minor gaps in pre-operative skin prep documentation.',
    citations: ['CDC SSI Guidelines 2023', 'WHO Surgical Safety Checklist'],
    processingTime: '3.7s',
  },
  {
    id: 'rpt-003',
    documentName: 'Hand_Hygiene_Compliance_Report_Q2.pdf',
    score: 91,
    generatedAt: '2025-06-05T10:15:00Z',
    violations: mockViolations.slice(4, 6),
    summary: 'Q2 hand hygiene compliance report demonstrates strong adherence to WHO 5 Moments framework with minor documentation gaps.',
    citations: ['WHO IPC Guidelines 2022', 'AHRQ Hand Hygiene Toolkit'],
    processingTime: '2.1s',
  },
]
