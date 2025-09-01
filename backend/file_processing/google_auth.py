from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from google.oauth2 import id_token
from google.auth.transport import requests

class GoogleOIDCAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None  # No Bearer token, let other auth classes try

        token = auth_header[len('Bearer '):]
        try:
            # Use your actual service URL as the audience!
            audience = 'https://your-cloudrun-url/your-webhook/'
            idinfo = id_token.verify_oauth2_token(token, requests.Request(), audience)
            email = idinfo.get('email')
            if not email:
                raise exceptions.AuthenticationFailed('No email in token')
            # Create a proxy user object
            user = type('ServiceAccountUser', (), {'username': email})()
            return (user, None)
        except Exception as e:
            raise exceptions.AuthenticationFailed(f'Invalid OIDC token: {e}')
