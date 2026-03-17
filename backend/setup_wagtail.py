"""
Setup script for Wagtail CMS
Run this after migrations to create the initial site structure
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alphalpgas.settings')
django.setup()

from wagtail.models import Page, Site
from cms.models import BlogIndexPage


def setup_wagtail():
    print("Setting up Wagtail CMS...")
    
    # Get the root page
    root_page = Page.objects.get(id=1)
    
    # Check if BlogIndexPage already exists
    if BlogIndexPage.objects.filter(slug='blog').exists():
        print("Blog already exists at /blog")
        return
    
    # Create the blog index page
    blog_index = BlogIndexPage(
        title="Blog",
        slug="blog",
        intro="<p>Welcome to the Alpha LPGas blog. Stay updated with our latest news and insights.</p>",
    )
    
    # Add it as a child of the root page
    root_page.add_child(instance=blog_index)
    blog_index.save_revision().publish()
    
    print(f"✓ Blog index page created at /blog")
    print(f"✓ You can now access:")
    print(f"  - Wagtail Admin: http://localhost:8000/cms/")
    print(f"  - Blog: http://localhost:8000/blog/")
    print(f"\nNext steps:")
    print(f"1. Create a superuser if you haven't: python manage.py createsuperuser")
    print(f"2. Login to Wagtail admin at /cms/")
    print(f"3. Create blog posts under the Blog page")


if __name__ == '__main__':
    setup_wagtail()
