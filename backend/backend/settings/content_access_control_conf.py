from django.conf import settings


CASBIN_MODEL = str(settings.BASE_DIR / 'dauthz_model.conf')

DAUTHZ = {
    # DEFAULT Dauthz enforcer
    'DEFAULT': {
        # Casbin model setting.
        'MODEL': {
            # Available Settings: "file", "text"
            'CONFIG_TYPE': 'file',
            'CONFIG_FILE_PATH': CASBIN_MODEL,
            'CONFIG_TEXT': '',
        },
        # Casbin adapter .
        'ADAPTER': {
            'NAME': 'casbin_adapter.adapter.Adapter',
        },
        'LOG': {
            'ENABLED': False,
        },
    },
}
