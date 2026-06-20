import os, sys, json
sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE','healthcare_rag.settings')
import django
django.setup()
from core.models import Document
from core.utils import extract_text, clean_text, chunk_text, add_chunks_to_chroma, get_or_create_collection
from django.conf import settings

doc = Document.objects.get(id='1a5f7990-df49-4f44-a892-be92401584b7')
print('doc status before:', doc.status, doc.chunk_count, doc.chroma_doc_id)
text = extract_text(doc.file.path)
print('text len:', len(text))
print('text preview:', repr(text[:120]))
cleaned = clean_text(text)
print('cleaned len:', len(cleaned))
chunks = chunk_text(cleaned, chunk_size=settings.CHUNK_SIZE, chunk_overlap=settings.CHUNK_OVERLAP)
print('chunks len:', len(chunks))
for i, c in enumerate(chunks):
    print(i, len(c['text']), repr(c['text'][:80]))
count = add_chunks_to_chroma(collection_name=settings.CHROMA_DOCUMENTS_COLLECTION, chunks=chunks, doc_id=str(doc.id), doc_metadata={'source':doc.name, 'doc_type':'hospital_document', 'hospital_name':doc.hospital_name or 'Unknown', 'department':doc.department or 'Unknown'}, embedding_model=settings.EMBEDDING_MODEL)
print('added count:', count)
col = get_or_create_collection(settings.CHROMA_DOCUMENTS_COLLECTION)
try:
    results = col.get(include=['metadatas','documents'], where={'doc_id': str(doc.id)})
    print('chroma hits:', len(results.get('metadatas', [])))
    if results.get('metadatas'):
        print('first metadata:', results['metadatas'][0])
except Exception as e:
    print('collection get error:', e)
try:
    q_results = col.query(query_embeddings=[ [0]*384 ], n_results=1, include=['metadatas','documents','distances'], where={'doc_id': str(doc.id)})
    print('query results keys:', q_results.keys())
except Exception as e:
    print('query error:', e)
