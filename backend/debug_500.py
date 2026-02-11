#!/usr/bin/env python
"""Debug script to find 500 error on quote detail"""
import os, django, traceback, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alphalpgas.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.first()

if not user:
    print("ERROR: No users found")
    sys.exit(1)

print(f"Using user: {user}")

# Test 1: Check if Quote with pk=1 exists
from core.models import Quote
try:
    q = Quote.objects.get(pk=1)
    print(f"Quote found: {q}")
    print(f"  client: {q.client}")
    print(f"  client.name: {q.client.name}")
    print(f"  quote_number: {q.quote_number}")
    print(f"  status: {q.status}")
    print(f"  items count: {q.items.count()}")
except Quote.DoesNotExist:
    print("ERROR: Quote with pk=1 does not exist")
    sys.exit(1)
except Exception as e:
    print(f"ERROR accessing quote: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 2: Try rendering the template
from django.template.loader import get_template
try:
    t = get_template('core/quote_detail.html')
    print("Template loaded OK")
except Exception as e:
    print(f"ERROR loading template: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 3: Try the full view
from core.views_forms import quote_detail
factory = RequestFactory()
request = factory.get('/accounting/quotes/1/')
request.user = user

# Add session and messages support
from django.contrib.sessions.backends.db import SessionStore
request.session = SessionStore()
from django.contrib.messages.storage.fallback import FallbackStorage
setattr(request, '_messages', FallbackStorage(request))

try:
    response = quote_detail(request, pk=1)
    print(f"Response status: {response.status_code}")
    if hasattr(response, 'render'):
        response.render()
        print(f"Rendered OK, content length: {len(response.content)}")
except Exception as e:
    print(f"ERROR in view: {e}")
    traceback.print_exc()
