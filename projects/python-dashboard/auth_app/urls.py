from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('user/', views.user_view, name='user'),
]
