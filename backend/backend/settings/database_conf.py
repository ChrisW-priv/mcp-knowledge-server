from django.conf import settings


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": settings.BASE_DIR / "db-main",
    }
}

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "postgres",
        "USER": "postgres",
        "PASSWORD": "password",
        "HOST": "localhost",
        "PORT": "5432",
    }
}
