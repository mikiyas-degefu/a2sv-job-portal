from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserRegistrationSerializer
from .tasks.email import send_verification_email, verify_verification_token
from accounts.models import User
from django.http import HttpResponse

def base_response(success, message, obj=None, errors=None):
    return {
        "success": success,
        "message": message,
        "object": obj or {},
        "errors": errors or {}
    }

@api_view(['POST'])
def user_registration_view(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        send_verification_email(user)
        return Response(
            base_response(
                True,
                "User registered successfully. Please verify your email.",
                {"email": user.email, "role": user.role}
            ),
            status=status.HTTP_201_CREATED
        )
    else:
        return Response(
            base_response(False, "Registration failed", errors=serializer.errors),
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['GET'])
def verify_email_view(request):
    token = request.query_params.get('token')
    if not token:
        return Response({"detail": "Token is required."}, status=status.HTTP_400_BAD_REQUEST)

    email = verify_verification_token(token)
    if not email:
        return HttpResponse(
            "<h1>Verification Failed</h1><p>Your verification link is invalid or expired.</p>",
            status=400
        )

    try:
        user = User.objects.get(email=email)
        if user.is_active:
            return HttpResponse(
                "<h1>Email Already Verified</h1><p>Your email has already been verified.</p>",
                status=400
            )

        user.is_active = True
        user.save()
        return HttpResponse(
            "<h1>Email Verified Successfully</h1><p>Thank you for verifying your email.</p>",
            status=200
        )

    except User.DoesNotExist:
        return HttpResponse(
            "<h1>User Not Found</h1><p>The user associated with this verification link does not exist.</p>",
            status=404
        )

