import os, sys, json
sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE','healthcare_rag.settings')
import django
django.setup()
from django.test import Client
c = Client()
r = c.get('/api/documents/', SERVER_NAME='testserver')
print('GET', r.status_code)
print(r.content[:1000])
r = c.post('/api/rag/qa/', data=json.dumps({'query': 'What is in the document?'}), content_type='application/json', SERVER_NAME='testserver')
print('POST', r.status_code)
print(r.content[:1000])
