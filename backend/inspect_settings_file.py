import os, sys
print('cwd=', os.getcwd())
sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE','healthcare_rag.settings')
import django
import healthcare_rag.settings as s
print('settings file=', s.__file__)
print('ALLOWED_HOSTS=', s.ALLOWED_HOSTS)
