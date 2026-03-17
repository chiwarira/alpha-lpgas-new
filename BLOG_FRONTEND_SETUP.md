# Blog Frontend Setup Guide

## Overview

Your Wagtail CMS blog is now configured to be served through your **Next.js frontend** at:
- **Local**: http://localhost:3000/blog
- **Production**: https://www.alphalpgas.co.za/blog

The blog content is managed in Wagtail CMS (backend) and consumed via API by the Next.js frontend.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Browser                             │
│              http://localhost:3000/blog                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Next.js Frontend (Port 3000)                    │
│  - /app/blog/page.tsx (Blog listing)                        │
│  - /app/blog/[slug]/page.tsx (Individual posts)             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Fetches data via API
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           Django Backend API (Port 8000)                     │
│  - /api/cms/pages/ (Wagtail API endpoints)                  │
│  - /cms/ (Wagtail admin interface)                          │
└─────────────────────────────────────────────────────────────┘
```

## What Was Set Up

### Backend (Django/Wagtail)

1. **Wagtail API** - Added `wagtail.api.v2` to expose blog content
2. **API Endpoints** - Created at `/api/cms/pages/`
3. **Blog Models** - `BlogIndexPage` and `BlogPage` with API fields
4. **Admin Interface** - Available at `http://localhost:8000/cms/`

### Frontend (Next.js)

1. **Blog Index Page** - `/app/blog/page.tsx`
   - Fetches all blog posts from API
   - Displays in a responsive grid layout
   - Shows post title, date, intro, and "Read more" link

2. **Blog Post Page** - `/app/blog/[slug]/page.tsx`
   - Dynamic route for individual posts
   - Renders StreamField content (headings, paragraphs, images, code)
   - Responsive article layout

## Getting Started

### 1. Start Both Servers

**Terminal 1 - Backend:**
```bash
cd backend
python manage.py runserver
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### 2. Create Blog Content

1. Go to **http://localhost:8000/cms/**
2. Login with your superuser credentials
3. Navigate to **Pages** → **Blog**
4. Click **"Add child page"** → **"Blog Page"**
5. Fill in:
   - **Title**: Your blog post title
   - **Date**: Publication date
   - **Intro**: Short summary (max 250 characters)
   - **Body**: Add content blocks:
     - **Heading** - Section titles
     - **Paragraph** - Rich text content
     - **Image** - Upload and insert images
     - **Code** - Code snippets
6. Click **"Publish"**

### 3. View Your Blog

- **Blog listing**: http://localhost:3000/blog
- **Individual post**: http://localhost:3000/blog/your-post-slug

## API Endpoints

The Wagtail API is available at:

### Get Blog Index Page
```
GET http://localhost:8000/api/cms/pages/?type=cms.BlogIndexPage&fields=*
```

### Get All Blog Posts
```
GET http://localhost:8000/api/cms/pages/?type=cms.BlogPage&fields=date,intro&order=-date
```

### Get Single Blog Post
```
GET http://localhost:8000/api/cms/pages/?type=cms.BlogPage&slug=my-post-slug&fields=date,intro,body
```

### Response Example
```json
{
  "meta": {
    "total_count": 1
  },
  "items": [
    {
      "id": 3,
      "meta": {
        "type": "cms.BlogPage",
        "slug": "my-first-post",
        "first_published_at": "2024-03-17T10:00:00Z"
      },
      "title": "My First Blog Post",
      "date": "2024-03-17",
      "intro": "This is a short introduction to my blog post.",
      "body": [
        {
          "type": "heading",
          "value": "Introduction"
        },
        {
          "type": "paragraph",
          "value": "<p>This is the first paragraph...</p>"
        }
      ]
    }
  ]
}
```

## Environment Variables

Your frontend `.env.local` should have:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

The blog pages automatically construct the correct API URL.

## Production Deployment

### Backend (Railway)

1. Ensure migrations are run:
   ```bash
   python manage.py migrate
   ```

2. Run the Wagtail setup script:
   ```bash
   python setup_wagtail.py
   ```

3. Update environment variables:
   - `SITE_URL` should be your production domain
   - `WAGTAILADMIN_BASE_URL` uses `SITE_URL`

### Frontend (Vercel/Netlify)

1. Set environment variable:
   ```
   NEXT_PUBLIC_API_URL=https://api.alphalpgas.co.za
   ```

2. Deploy as normal - the blog will be available at `/blog`

## Customization

### Styling

The blog pages use Tailwind CSS classes. Customize in:
- `frontend/app/blog/page.tsx` - Blog listing styles
- `frontend/app/blog/[slug]/page.tsx` - Individual post styles

### Adding More Content Blocks

Edit `backend/cms/models.py` to add more StreamField block types:

```python
body = StreamField([
    ('heading', blocks.CharBlock(form_classname="title")),
    ('paragraph', blocks.RichTextBlock()),
    ('image', ImageChooserBlock()),
    ('code', blocks.TextBlock()),
    ('quote', blocks.BlockQuoteBlock()),  # New block
    ('embed', blocks.URLBlock()),  # New block
], use_json_field=True, blank=True)
```

Then update the frontend renderer in `frontend/app/blog/[slug]/page.tsx`:

```typescript
case 'quote':
  return (
    <blockquote key={index} className="border-l-4 border-blue-500 pl-4 italic my-6">
      {block.value}
    </blockquote>
  );
```

### SEO Optimization

Add metadata to blog pages:

```typescript
// In frontend/app/blog/[slug]/page.tsx
export async function generateMetadata({ params }: { params: { slug: string } }) {
  const post = await getBlogPost(params.slug);
  
  return {
    title: post?.title || 'Blog Post',
    description: post?.intro || '',
  };
}
```

## Troubleshooting

### Blog shows "No blog posts yet"
- Ensure you've created and **published** posts in Wagtail admin
- Check the API endpoint: http://localhost:8000/api/cms/pages/?type=cms.BlogPage
- Verify the backend server is running

### API returns empty results
- Run `python setup_wagtail.py` to create the Blog index page
- Check that posts are published (not just saved as drafts)
- Verify CORS settings in Django allow frontend origin

### Images not loading
- Check that images are uploaded in Wagtail admin
- Verify `MEDIA_URL` is configured correctly
- In production, ensure Cloudinary is set up

### 404 on blog routes
- Restart the Next.js dev server: `npm run dev`
- Clear Next.js cache: `rm -rf .next`
- Check that files exist in `frontend/app/blog/`

## Features

### ✅ Implemented
- Blog listing page with grid layout
- Individual blog post pages
- StreamField content rendering (headings, paragraphs, images, code)
- Responsive design
- API-driven content
- Dynamic routing

### 🔄 Future Enhancements
- Categories and tags
- Search functionality
- Pagination
- Related posts
- Comments system
- Social sharing buttons
- RSS feed
- Reading time estimates

## Resources

- [Wagtail API Documentation](https://docs.wagtail.org/en/stable/advanced_topics/api/v2/configuration.html)
- [Next.js Dynamic Routes](https://nextjs.org/docs/app/building-your-application/routing/dynamic-routes)
- [StreamField Guide](https://docs.wagtail.org/en/stable/topics/streamfield.html)
