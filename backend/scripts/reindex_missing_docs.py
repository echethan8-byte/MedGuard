"""
Reindex documents with chunk_count == 0 by invoking the Celery task.
Run: python scripts/reindex_missing_docs.py
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'healthcare_rag.settings')
import django
django.setup()
from core.models import Document
from documents.tasks import process_document_task

q = Document.objects.filter(chunk_count=0).exclude(status=Document.Status.ERROR)
print(f"Found {q.count()} documents with chunk_count=0")
for doc in q:
    print(f"Reindexing: {doc.id} - {doc.name} (status={doc.status})")
    try:
        # Use .delay() so settings' CELERY_TASK_ALWAYS_EAGER runs it synchronously in dev
        process_document_task.delay(str(doc.id))
        doc.refresh_from_db()
        print(f" -> After run: status={doc.status}, chunk_count={doc.chunk_count}, error={doc.error_message}")
    except Exception as e:
        print(f"Failed to process {doc.id}: {e}")

print('Reindexing complete.')
