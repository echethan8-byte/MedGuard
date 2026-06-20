import os, sys
print('env ALLOWED_HOSTS=', os.getenv('ALLOWED_HOSTS'))
sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE','healthcare_rag.settings')
import django
django.setup()
from django.conf import settings
print('settings.ALLOWED_HOSTS=', settings.ALLOWED_HOSTS)
