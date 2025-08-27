import os


DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD')
DB_DATABASE_NAME = os.getenv('POSTGRES_DATABASE_NAME', 'postgres')

db_conn_name = os.getenv('DB_CONN_NAME')
pre_db_conn_name = os.getenv('PRE_DB_CONN_NAME')
unix_socket_path = f'{pre_db_conn_name}{db_conn_name}'

DATABASES = {'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': DB_DATABASE_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': unix_socket_path,
        'PORT': '',
    }
}
