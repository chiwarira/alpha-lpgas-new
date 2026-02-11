#!/usr/bin/env python
"""Debug script to find 500 error on quote detail"""
import os, django, traceback, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alphalpgas.settings')
django.setup()

from core.models import Quote

# List all quotes
all_quotes = list(Quote.objects.all().values_list('pk', 'quote_number', 'status'))
print('All quotes:', all_quotes)
print('Quote count:', len(all_quotes))

if not all_quotes:
    print('No quotes exist on production')
    sys.exit(0)

# Test with first available quote
q = Quote.objects.first()
print('First quote pk:', q.pk)
print('First quote number:', q.quote_number)
print('Client:', q.client.name)

# Test rendering the view
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.messages.storage.fallback import FallbackStorage
from core.views_forms import quote_detail

User = get_user_model()
user = User.objects.first()
print('User:', user)

factory = RequestFactory()
request = factory.get('/test/')
request.user = user
request.session = SessionStore()
setattr(request, '_messages', FallbackStorage(request))

try:
    response = quote_detail(request, pk=q.pk)
    print('Response status:', response.status_code)
    if hasattr(response, 'render'):
        response.render()
        print('Rendered OK, length:', len(response.content))
except Exception as e:
    print('ERROR in view:', str(e))
    traceback.print_exc()
