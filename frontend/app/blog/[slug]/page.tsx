import Link from 'next/link';
import { notFound } from 'next/navigation';
import Header from '@/components/Header';
import Footer from '@/components/Footer';

interface BlogPostData {
  id: number;
  title: string;
  date: string;
  intro: string;
  body: Array<{
    type: string;
    value: any;
    id?: string;
  }>;
  meta: {
    type: string;
    slug: string;
    first_published_at: string;
  };
}

async function getBlogPost(slug: string): Promise<BlogPostData | null> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const baseUrl = apiUrl.replace('/api', ''); // Remove /api if present
  
  try {
    const res = await fetch(
      `${baseUrl}/api/cms/pages/?type=cms.BlogPage&slug=${slug}&fields=date,intro,body`,
      { cache: 'no-store' }
    );
    
    if (!res.ok) {
      return null;
    }
    
    const data = await res.json();
    const post = data.items?.[0] || null;
    
    // Process body blocks to fetch image details
    if (post && post.body) {
      for (let block of post.body) {
        if (block.type === 'image' && typeof block.value === 'number') {
          // Fetch image details from the images API
          try {
            const imgRes = await fetch(`${baseUrl}/api/cms/images/${block.value}/`, {
              cache: 'no-store'
            });
            if (imgRes.ok) {
              const imgData = await imgRes.json();
              // Construct absolute URL for the image
              const imageUrl = imgData.meta?.download_url?.startsWith('http') 
                ? imgData.meta.download_url 
                : `${baseUrl}${imgData.meta?.download_url || ''}`;
              
              block.value = {
                id: imgData.id,
                title: imgData.title,
                url: imageUrl,
                width: imgData.width,
                height: imgData.height,
              };
            }
          } catch (err) {
            console.error('Error fetching image:', err);
          }
        }
      }
    }
    
    return post;
  } catch (error) {
    console.error('Error fetching blog post:', error);
    return null;
  }
}

function renderBodyBlock(block: any, index: number) {
  switch (block.type) {
    case 'heading':
      return (
        <h2 key={index} className="text-3xl font-bold mt-8 mb-4 text-gray-900">
          {block.value}
        </h2>
      );
    
    case 'paragraph':
      return (
        <div 
          key={index} 
          className="prose max-w-none mb-4 text-gray-700"
          dangerouslySetInnerHTML={{ __html: block.value }}
        />
      );
    
    case 'image':
      if (block.value?.url) {
        return (
          <figure key={index} className="my-8">
            <img 
              src={block.value.url} 
              alt={block.value.title || block.value.alt || ''} 
              className="rounded-lg shadow-md w-full max-w-3xl mx-auto"
            />
            {(block.value.title || block.value.caption) && (
              <figcaption className="text-sm text-gray-600 mt-2 text-center">
                {block.value.title || block.value.caption}
              </figcaption>
            )}
          </figure>
        );
      }
      return null;
    
    case 'code':
      return (
        <pre key={index} className="bg-gray-100 p-4 rounded-lg overflow-x-auto my-4">
          <code className="text-sm">{block.value}</code>
        </pre>
      );
    
    default:
      return null;
  }
}

export default async function BlogPostPage({ params }: { params: { slug: string } }) {
  const post = await getBlogPost(params.slug);

  if (!post) {
    notFound();
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      {/* Article */}
      <main className="flex-grow bg-gray-50 py-12">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <article className="bg-white rounded-xl shadow-sm p-8 md:p-12">
            {/* Breadcrumb */}
            <div className="mb-6">
              <Link 
                href="/blog"
                className="text-rose-600 hover:text-rose-700 font-medium inline-flex items-center"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                Back to Blog
              </Link>
            </div>

            {/* Article Header */}
            <header className="mb-8 pb-6 border-b border-gray-200">
              <h1 className="text-4xl md:text-5xl font-bold mb-4 text-gray-900">
                {post.title}
              </h1>
              
              <div className="flex items-center text-gray-600">
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <time dateTime={post.date}>
                  {new Date(post.date).toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                  })}
                </time>
              </div>
              
              {post.intro && (
                <p className="text-xl text-gray-700 italic mt-4 leading-relaxed">
                  {post.intro}
                </p>
              )}
            </header>
            
            {/* Article Content */}
            <div className="prose prose-lg max-w-none">
              {post.body && post.body.length > 0 ? (
                post.body.map((block, index) => renderBodyBlock(block, index))
              ) : (
                <p className="text-gray-600">No content available.</p>
              )}
            </div>
            
            {/* Article Footer */}
            <div className="mt-12 pt-6 border-t border-gray-200">
              <Link 
                href="/blog"
                className="inline-flex items-center text-rose-600 hover:text-rose-700 font-semibold"
              >
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                Back to all articles
              </Link>
            </div>
          </article>
        </div>
      </main>
      
      <Footer />
    </div>
  );
}

// Generate static params for all blog posts (optional - for static generation)
export async function generateStaticParams() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const baseUrl = apiUrl.replace('/api', ''); // Remove /api if present
  
  try {
    const res = await fetch(`${baseUrl}/api/cms/pages/?type=cms.BlogPage&fields=_,slug`);
    const data = await res.json();
    
    return (data.items || []).map((post: any) => ({
      slug: post.meta.slug,
    }));
  } catch (error) {
    return [];
  }
}
