"""URL configuration for the Account Charging System."""
import os
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.http import FileResponse, Http404


def serve_frontend_asset(request, path):
    """Serve static assets from the frontend build directory."""
    file_path = settings.FRONTEND_DIR / path
    if file_path.exists() and file_path.is_file():
        return FileResponse(open(file_path, 'rb'))
    raise Http404


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.urls')),
    path('api/wallet/', include('wallet.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/transfers/', include('transfers.urls')),
    path('api/affiliates/', include('affiliates.urls')),
    path('api/banking/', include('banking.urls')),
]

# Serve media files
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Serve frontend build (React SPA) — catch-all must be last
if settings.FRONTEND_DIR.exists():
    urlpatterns += [
        # Serve Vite assets (JS, CSS, images, etc.)
        re_path(r'^assets/(?P<path>.*)$', lambda request, path: serve_frontend_asset(request, f'assets/{path}')),
        # Serve other frontend static files (favicon, etc.)
        re_path(r'^(?P<path>vite\.svg|favicon\.ico|robots\.txt|manifest\.json|29962979\.txt)$', serve_frontend_asset),
        # Catch-all: serve index.html for React Router
        re_path(r'^(?!api/|admin/|static/|media/).*$', TemplateView.as_view(template_name='index.html')),
    ]
