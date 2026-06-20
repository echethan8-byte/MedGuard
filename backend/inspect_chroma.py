import os, sys, json
sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE','healthcare_rag.settings')
import django
django.setup()
from core.models import Document
from core.utils import get_chroma_client, get_or_create_collection

doc = Document.objects.get(id='1a5f7990-df49-4f44-a892-be92401584b7')
print('doc:', doc.id, doc.status, doc.chunk_count, repr(doc.error_message), doc.chroma_doc_id)

col = get_or_create_collection('hospital_documents')
print('collection name:', col.name)
try:
    count = col.count()
    print('collection.count:', count)
except Exception as e:
    print('collection.count failed:', e)

try:
    results = col.get(include=['metadatas','documents','ids'], where={'doc_id': str(doc.id)})
    print('get results keys:', results.keys())
    print('ids len:', len(results.get('ids', [])))
    print('metadatas len:', len(results.get('metadatas', [])))
    print('documents len:', len(results.get('documents', [])))
    print('first metadata:', results.get('metadatas', [])[:2])
except Exception as e:
    print('collection.get error:', e)

try:
    q = col.query(query_embeddings=[[0]*384], n_results=1, include=['metadatas'])
    print('query shape:', q.keys())
except Exception as e:
    print('query test error:', e)
