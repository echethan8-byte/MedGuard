import os
import sys

# Ensure project root is on path and Django settings are loaded
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'healthcare_rag.settings')

import django
django.setup()

from core.models import ComplianceReport

reports = ComplianceReport.objects.all()
print('COUNT:' + str(reports.count()))
for r in reports:
    p = getattr(r.pdf_report, 'path', None)
    exists = os.path.exists(p) if p else False
    print(f'{r.id} {r.status} pdf_present={bool(r.pdf_report)} path={p} exists={exists}')
