import os
import sys

# Setup Django
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'healthcare_rag.settings')
import django
django.setup()

from core.models import Document, ComplianceReport
from django.core.files import File
from django.core.files.base import ContentFile
from rag.report_generator import generate_pdf_report

# Ensure media/documents exists
media_docs = os.path.join(BASE_DIR, 'media', 'documents', 'sample')
os.makedirs(media_docs, exist_ok=True)

sample_txt_path = os.path.join(media_docs, 'sample.txt')
with open(sample_txt_path, 'w', encoding='utf-8') as f:
    f.write('This is a sample document used to generate a test compliance report.\n')

# Create Document
with open(sample_txt_path, 'rb') as f:
    djfile = File(f)
    doc = Document.objects.create(
        name='Sample Document for PDF Test',
        doc_type='txt',
        file_size=os.path.getsize(sample_txt_path),
        status=Document.Status.INDEXED,
    )
    # Save file to FileField
    doc.file.save('sample.txt', djfile, save=True)

# Create ComplianceReport
report = ComplianceReport.objects.create(
    document=doc,
    status=ComplianceReport.Status.RUNNING,
    requested_by=None,
)

# Generate PDF
report_data = {
    'compliance_score': 85,
    'summary': 'Automated sample report for testing PDF generation.',
    'violations': [
        {
            'regulation_id': 'REG-1',
            'title': 'Sample violation',
            'description': 'Description of sample violation.',
            'risk': 'low',
            'evidence': 'Sample evidence text extracted from document.',
            'citation': 'Sample Citation',
            'corrective_action': 'Sample corrective steps.',
            'category': 'Sample',
        }
    ],
    'citations': ['Sample Policy 1'],
    'llm_model': 'mock-model',
    'processing_time_ms': 1234,
}

pdf_bytes = generate_pdf_report(report_data, doc.name)
report.pdf_report.save(f'report_{report.id}.pdf', ContentFile(pdf_bytes), save=True)
report.status = ComplianceReport.Status.COMPLETED
report.compliance_score = report_data['compliance_score']
report.save()

print('Created report:', report.id)
print('PDF path:', report.pdf_report.path)
