from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from google.oauth2 import id_token
from google.auth.transport import requests

import logging


logger = logging.getLogger(__name__)


class ServiceAccountUser:
    def __init__(self, email):
        self.username = email
        self.email = email

    @property
    def is_authenticated(self):
        return True


class GoogleOIDCAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        logger.info('Started to authenticate with custom OIDC Authentication')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None  # No Bearer token, let other auth classes try

        token = auth_header[len('Bearer '):]
        try:
            # Use your actual service URL as the audience!
            audience = 'https://knowledge-server-obr76apg5a-ez.a.run.app/'
            logger.info('Trying to verify the oauth2 token')
            idinfo = id_token.verify_oauth2_token(token, requests.Request(), audience)
            email = idinfo.get('email')
            if not email:
                raise exceptions.AuthenticationFailed('No email in token')
            logger.info(f'Successfuly retrieved the {email=}')
            user = ServiceAccountUser(email)
            return (user, None)
        except Exception as e:
            raise exceptions.AuthenticationFailed(f'Invalid OIDC token: {e}')
