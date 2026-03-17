import Link from 'next/link';
import Header from '@/components/Header';
import Footer from '@/components/Footer';

interface BlogPost {
  id: number;
  meta: {
    type: string;
    detail_url: string;
    html_url: string;
    slug: string;
    first_published_at: string;
  };
  title: string;
  date?: string;
  intro?: string;
}

interface BlogIndexData {
  id: number;
  title: string;
  intro: string;
  meta: {
    type: string;
    detail_url: string;
  };
}

async function getBlogPosts() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const baseUrl = apiUrl.replace('/api', ''); // Remove /api if present
  
  try {
    // First, get the blog index page to find its ID
    const indexRes = await fetch(`${baseUrl}/api/cms/pages/?type=cms.BlogIndexPage&fields=*`, {
      cache: 'no-store',
    });
    
    if (!indexRes.ok) {
      console.error('Failed to fetch blog index');
      return { blogIndex: null, posts: [] };
    }
    
    const indexData = await indexRes.json();
    const blogIndex: BlogIndexData | null = indexData.items?.[0] || null;
    
    if (!blogIndex) {
      return { blogIndex: null, posts: [] };
    }
    
    // Get all blog posts
    const postsRes = await fetch(`${baseUrl}/api/cms/pages/?type=cms.BlogPage&fields=date,intro&order=-date`, {
      cache: 'no-store',
    });
    
    if (!postsRes.ok) {
      return { blogIndex, posts: [] };
    }
    
    const postsData = await postsRes.json();
    return { blogIndex, posts: postsData.items || [] };
  } catch (error) {
    console.error('Error fetching blog data:', error);
    return { blogIndex: null, posts: [] };
  }
}

export default async function BlogPage() {
  const { blogIndex, posts } = await getBlogPosts();

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      
      {/* Hero Section */}
      <div className="bg-gradient-to-br from-rose-600 to-rose-700 text-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-5xl md:text-6xl font-bold mb-4">
            {blogIndex?.title || 'Blog'}
          </h1>
          {blogIndex?.intro && (
            <div 
              className="text-xl text-rose-100 max-w-3xl prose prose-invert"
              dangerouslySetInnerHTML={{ __html: blogIndex.intro }}
            />
          )}
        </div>
      </div>

      {/* Blog Posts Grid */}
      <main className="flex-grow bg-gray-50 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {posts.length === 0 ? (
            <div className="text-center py-16 bg-white rounded-lg shadow-sm">
              <div className="text-6xl mb-4">📝</div>
              <h2 className="text-2xl font-bold text-gray-800 mb-2">No blog posts yet</h2>
              <p className="text-gray-600 mb-4">Check back soon for updates!</p>
              <p className="text-sm text-gray-500">
                Create your first post in the{' '}
                <a 
                  href="http://localhost:8000/cms/" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-rose-600 hover:text-rose-700 font-medium"
                >
                  Wagtail admin
                </a>
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {posts.map((post: BlogPost) => (
                <article 
                  key={post.id}
                  className="bg-white rounded-xl shadow-sm hover:shadow-xl transition-all duration-300 overflow-hidden group"
                >
                  {/* Card Header with gradient */}
                  <div className="h-2 bg-gradient-to-r from-rose-500 to-blue-500"></div>
                  
                  <div className="p-6">
                    {/* Date Badge */}
                    {post.date && (
                      <div className="flex items-center text-sm text-gray-500 mb-3">
                        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                        {new Date(post.date).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric'
                        })}
                      </div>
                    )}
                    
                    {/* Title */}
                    <h2 className="text-2xl font-bold mb-3 group-hover:text-rose-600 transition-colors">
                      <Link href={`/blog/${post.meta.slug}`}>
                        {post.title}
                      </Link>
                    </h2>
                    
                    {/* Excerpt */}
                    {post.intro && (
                      <p className="text-gray-600 mb-4 line-clamp-3">
                        {post.intro}
                      </p>
                    )}
                    
                    {/* Read More Link */}
                    <Link 
                      href={`/blog/${post.meta.slug}`}
                      className="inline-flex items-center text-rose-600 hover:text-rose-700 font-semibold group-hover:gap-2 transition-all"
                    >
                      Read Article
                      <svg className="w-5 h-5 ml-1 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                      </svg>
                    </Link>
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>
      </main>
      
      <Footer />
    </div>
  );
}
