from django.conf import settings


CASBIN_MODEL = str(settings.BASE_DIR / "dauthz_model.conf")
CASBIN_ENFORCER_EAGER_LOAD = False
