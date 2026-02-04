from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
import json
from django.views.decorators.http import require_http_methods
import secrets

# Simple in-memory token store (in production, use database)
active_tokens = {}

@csrf_exempt
@require_http_methods(["POST"])
def login_view(request):
    """API endpoint for user login"""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return JsonResponse({
                'error': 'Username and password are required'
            }, status=400)

        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Generate a simple token for this user
            token = secrets.token_hex(32)
            active_tokens[token] = {
                'user_id': user.id,
                'username': user.username,
                'created': str(user.date_joined)
            }
            
            return JsonResponse({
                'success': True,
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                },
                'token': token
            })
        else:
            return JsonResponse({
                'error': 'Invalid credentials'
            }, status=401)

    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def logout_view(request):
    """API endpoint for user logout"""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        if token in active_tokens:
            del active_tokens[token]
    
    return JsonResponse({
        'success': True,
        'message': 'Logout successful'
    })

@csrf_exempt
@require_http_methods(["GET"])
def user_view(request):
    """API endpoint to get current user information"""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        if token in active_tokens:
            token_data = active_tokens[token]
            return JsonResponse({
                'user': {
                    'id': token_data['user_id'],
                    'username': token_data['username']
                }
            })
    
    return JsonResponse({
        'error': 'Not authenticated'
    }, status=401)

@require_http_methods(["GET"])
def health_check(request):
    """Health check endpoint"""
    return JsonResponse({
        'status': 'healthy',
        'message': 'Django API is running'
    })
