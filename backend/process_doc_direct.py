import os, sys, json
sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE','healthcare_rag.settings')
import django
django.setup()
from core.models import Document
from documents.tasks import process_document_task
from core.utils import get_or_create_collection

doc = Document.objects.get(id='1a5f7990-df49-4f44-a892-be92401584b7')
print('before status:', doc.status, doc.chunk_count, doc.chroma_doc_id)
process_document_task.run(None, str(doc.id))
print('after direct run')
doc.refresh_from_db()
print('after status:', doc.status, doc.chunk_count, doc.chroma_doc_id, repr(doc.error_message))
col = get_or_create_collection('hospital_documents')
results = col.get(include=['metadatas','documents'], where={'doc_id': str(doc.id)})
print('chroma count for doc:', len(results.get('metadatas', [])))
if results.get('metadatas'):
    print('first meta', results['metadatas'][0])
