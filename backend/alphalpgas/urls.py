"""
URL configuration for Alpha LPGas project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls
from .views import api_root, home

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),
    
    # Wagtail CMS
    path('cms/', include(wagtailadmin_urls)),
    path('documents/', include(wagtaildocs_urls)),
    
    # API Root
    path('api/', api_root, name='api-root'),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # API Endpoints
    path('api/auth/', include('core.urls.auth')),
    path('api/accounting/', include('core.urls.accounting')),
    path('api/public/', include('core.urls.public')),
    
    # Form-based views for accounting
    path('accounting/', include('core.urls.forms')),
    
    # Driver portal
    path('driver/', include('core.urls.driver_portal')),
    
    # Django allauth (for login/logout)
    path('accounts/', include('allauth.urls')),
    
    # Wagtail pages
    path('pages/', include(wagtail_urls)),
    
    # Home page (root URL)
    path('', home, name='home'),
]

# Serve media files (in production, use WhiteNoise for static files)
# Media files should always be served by Django
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
