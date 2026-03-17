# Wagtail Blog Setup Guide

## Overview

Your Wagtail CMS blog is now configured to run at **`/blog`** as a subfolder (not a subdomain).

- **Local Blog URL**: http://localhost:8000/blog/
- **Production Blog URL**: https://www.alphalpgas.co.za/blog/
- **Wagtail Admin**: http://localhost:8000/cms/

## What Was Installed

### 1. Django Apps Added
- `wagtail` - Core CMS functionality
- `wagtail.admin` - Admin interface
- `wagtail.images` - Image management
- `wagtail.documents` - Document management
- `modelcluster` & `taggit` - Required dependencies

### 2. Blog Models Created (`backend/cms/models.py`)
- **BlogIndexPage** - The main blog listing page at `/blog`
- **BlogPage** - Individual blog post pages

### 3. Templates Created
- `cms/templates/cms/blog_index_page.html` - Blog listing with TailwindCSS styling
- `cms/templates/cms/blog_page.html` - Individual blog post view

### 4. URL Configuration
- `/cms/` - Wagtail admin interface
- `/blog/` - Blog pages (handled by Wagtail)
- All other existing URLs remain unchanged

## Setup Instructions

### Step 1: Run the Setup Script

```bash
cd backend
python setup_wagtail.py
```

This will create the Blog page at `/blog`.

### Step 2: Create a Superuser (if you don't have one)

```bash
python manage.py createsuperuser
```

Follow the prompts to create your admin account.

### Step 3: Start the Development Server

```bash
python manage.py runserver
```

### Step 4: Access Wagtail Admin

1. Go to http://localhost:8000/cms/
2. Login with your superuser credentials
3. You'll see the Wagtail admin dashboard

### Step 5: Create Your First Blog Post

1. In Wagtail admin, navigate to **Pages** in the sidebar
2. You'll see the page tree with "Blog" under "Root"
3. Click the **"..."** menu next to "Blog"
4. Select **"Add child page"**
5. Choose **"Blog Page"**
6. Fill in:
   - **Title**: Your blog post title
   - **Date**: Publication date
   - **Intro**: A short summary (max 250 characters)
   - **Body**: Your blog content using the StreamField editor
     - Add headings, paragraphs, images, and code blocks
7. Click **"Publish"** (or "Save draft" to save without publishing)

### Step 6: View Your Blog

- Blog listing: http://localhost:8000/blog/
- Individual posts: http://localhost:8000/blog/your-post-slug/

## Blog Features

### StreamField Content Blocks

The blog post body supports:
- **Heading** - Section headings
- **Paragraph** - Rich text with formatting
- **Image** - Upload and display images
- **Code** - Code snippets with syntax highlighting

### Responsive Design

Templates use TailwindCSS for modern, responsive styling that matches your existing site design.

## URL Structure

The blog uses a **subfolder structure**, not a subdomain:

✅ **Correct**: `https://www.alphalpgas.co.za/blog/`
❌ **Not**: `https://blog.alphalpgas.co.za/`

This is configured through Wagtail's page tree system. The Blog page has slug `blog`, so all blog content appears under `/blog/`.

## Production Deployment

When deploying to production:

1. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

2. **Run the setup script**:
   ```bash
   python setup_wagtail.py
   ```

3. **Collect static files**:
   ```bash
   python manage.py collectstatic --noinput
   ```

4. **Update environment variables** in Railway:
   - Ensure `WAGTAILADMIN_BASE_URL` is set to your production domain
   - Already configured in settings.py to use `SITE_URL`

## Customization

### Adding More Content Types

You can extend the blog by adding more page types in `backend/cms/models.py`:

```python
class NewsPage(Page):
    # Add fields for news articles
    pass

class EventPage(Page):
    # Add fields for events
    pass
```

### Modifying Templates

Templates are in `backend/cms/templates/cms/`. Customize them to match your brand:
- `blog_index_page.html` - Blog listing layout
- `blog_page.html` - Individual post layout

### Adding Images to Blog Posts

1. In Wagtail admin, go to **Images** in the sidebar
2. Upload images
3. When creating a blog post, add an **Image** block in the body
4. Select from your uploaded images

## Troubleshooting

### Blog page shows 404
- Ensure you ran `python setup_wagtail.py`
- Check that migrations are applied: `python manage.py migrate`

### Can't access /cms/
- Verify Wagtail apps are in `INSTALLED_APPS`
- Check that URLs are configured correctly
- Restart the development server

### Images not displaying
- Check `MEDIA_URL` and `MEDIA_ROOT` settings
- In development, ensure media files are served
- In production, configure Cloudinary (already set up)

## Next Steps

1. ✅ Create your first blog post
2. ✅ Customize the blog templates to match your brand
3. ✅ Add more content types (news, events, etc.)
4. ✅ Set up SEO fields (can be added to models)
5. ✅ Configure social sharing (can be added to templates)

## Resources

- [Wagtail Documentation](https://docs.wagtail.org/)
- [Wagtail Tutorial](https://docs.wagtail.org/en/stable/getting_started/tutorial.html)
- [StreamField Guide](https://docs.wagtail.org/en/stable/topics/streamfield.html)
