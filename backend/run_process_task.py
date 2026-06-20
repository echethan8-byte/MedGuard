import os, sys, json
sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE','healthcare_rag.settings')
import django
django.setup()
from core.models import Document
from documents.tasks import process_document_task
from core.utils import extract_text, clean_text, chunk_text

doc = Document.objects.get(id='1a5f7990-df49-4f44-a892-be92401584b7')
print('doc file:', doc.file.path)
print('doc status:', doc.status, 'chunk_count:', doc.chunk_count)
print('exists:', os.path.exists(doc.file.path))
print('file size:', os.path.getsize(doc.file.path) if os.path.exists(doc.file.path) else 'missing')
try:
    text = extract_text(doc.file.path)
    print('extracted length:', len(text))
    print(text[:500])
except Exception as e:
    print('extract_text failed:', e)

try:
    process_document_task(None, str(doc.id))
    print('task run complete')
except Exception as e:
    import traceback; traceback.print_exc()
    print('task run exception:', e)

# Reload document and inspect chroma
from core.utils import get_or_create_collection

doc.refresh_from_db()
print('after reload status:', doc.status, 'chunk_count:', doc.chunk_count, 'error:', repr(doc.error_message))
col = get_or_create_collection('hospital_documents')
try:
    results = col.get(include=['metadatas','documents'], where={'doc_id': str(doc.id)})
    print('chroma ids:', len(results.get('metadatas', [])))
    print('first metadata:', results.get('metadatas', [])[:2])
except Exception as e:
    print('chroma get error:', e)
