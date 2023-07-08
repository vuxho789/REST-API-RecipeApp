"""
URL mappings for User API.
"""
from django.urls import path
from user import views

app_name = 'user'

urlpatterns = [
    path('register/', views.CreateUserView.as_view(), name='register'),
    path('token/', views.CreateTokenView.as_view(), name='token'),
]
