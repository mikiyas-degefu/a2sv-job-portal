from django.core.signing import TimestampSigner, SignatureExpired, BadSignature
from django.core.mail import send_mail
from django.conf import settings

signer = TimestampSigner()

def generate_verification_token(email):
    return signer.sign(email)

def verify_verification_token(token, max_age=3600):  # 1 hour = 3600 seconds
    try:
        email = signer.unsign(token, max_age=max_age)
        return email
    except (SignatureExpired, BadSignature):
        return None
    
def send_verification_email(user):
    token = generate_verification_token(user.email)
    verify_url = f"https://localhost/api/verify-email?token={token}"

    subject = "Verify your email"
    message = (
        f"Hi {user.first_name},\n\n"
        f"Please verify your email address by clicking the link below:\n\n"
        f"{verify_url}\n\n"
        f"This link will expire in 1 hour.\n\n"
        "Thank you!"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])