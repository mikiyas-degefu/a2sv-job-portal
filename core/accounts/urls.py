from django.urls import path
from .views import *

urlpatterns = [
    path('register/', user_registration_view, name='user-register'),
    path('verify-email/', verify_email_view, name='verify-email'),
    path('login/', user_login_view, name='user-login'),
]