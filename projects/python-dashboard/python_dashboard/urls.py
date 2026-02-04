"""python_dashboard URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET"])
def health_check(request):
    """Health check endpoint"""
    return JsonResponse({
        'status': 'healthy',
        'message': 'Django API is running'
    })

def api_info(request):
    """API information endpoint"""
    return JsonResponse({
        'name': 'DevWorkspaces Django API',
        'version': '1.0.0',
        'description': 'Authentication API for DevWorkspaces Comprehensive Dashboard',
        'endpoints': {
            'health': '/api/health/',
            'login': '/api/auth/login/',
            'logout': '/api/auth/logout/',
            'user': '/api/auth/user/',
            'admin': '/admin/'
        },
        'documentation': 'API endpoints are available under /api/ prefix'
    })

urlpatterns = [
    path('', api_info, name='api_info'),
    path('api/health/', health_check, name='health_check'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('auth_app.urls')),
]
