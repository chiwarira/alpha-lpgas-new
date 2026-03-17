"""
Test what the API returns for blog posts with images
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alphalpgas.settings')
django.setup()

import json
from cms.models import BlogPage
from wagtail.api.v2.views import PagesAPIViewSet
from django.test import RequestFactory

# Get a blog page
blog_posts = BlogPage.objects.all()
if blog_posts.exists():
    post = blog_posts.first()
    print(f"Testing blog post: {post.title}")
    print(f"Body content:")
    for block in post.body:
        print(f"  - Type: {block.block_type}")
        if block.block_type == 'image':
            print(f"    Value type: {type(block.value)}")
            print(f"    Value: {block.value}")
            if hasattr(block.value, 'id'):
                print(f"    Image ID: {block.value.id}")
                print(f"    Image file: {block.value.file}")
                print(f"    Image URL: {block.value.file.url}")
else:
    print("No blog posts found")
