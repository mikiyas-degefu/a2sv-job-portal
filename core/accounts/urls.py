from django.urls import path
from .views import user_registration_view, verify_email_view

urlpatterns = [
    path('register/', user_registration_view, name='user-register'),
    path('verify-email/', verify_email_view, name='verify-email'),
]