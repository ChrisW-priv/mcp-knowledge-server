REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'file_processing.google_auth.GoogleOIDCAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
        # 'content_access_control.permissions.DAuthzPermission',
    ],
}
