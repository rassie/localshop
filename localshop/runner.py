from logan.runner import run_app


def generate_settings():
    """
    This command is run when ``default_path`` doesn't exist, or ``init`` is
    run and returns a string representing the default data to put into their
    settings file.
    """
    CONFIG_TEMPLATE = """
import os
import os.path

from localshop.conf.server import *

ROOT = os.path.dirname(__file__)

DATABASES = {
    'default': {
        # You can swap out the engine for MySQL easily by changing this value
        # to ``django.db.backends.mysql`` or to PostgreSQL with
        # ``django.db.backends.postgresql_psycopg2``
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(ROOT, 'localshop.db'),
        'USER': 'postgres',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

# Where the packages are stored
MEDIA_ROOT = os.path.join(ROOT, 'files')

LOCALSHOP_RUN_DIR = os.path.join(ROOT, 'run')
LOCALSHOP_LOG_DIR = os.path.join(ROOT, 'log')

for dir in [MEDIA_ROOT, LOCALSHOP_RUN_DIR, LOCALSHOP_LOG_DIR]:
    if not os.path.exists(dir):
         os.makedirs(dir)

LOCALSHOP_WEB_HOST = '0.0.0.0'
LOCALSHOP_WEB_PORT = 8900

    """
    return CONFIG_TEMPLATE


def main():
    run_app(
        project='localshop',
        default_config_path='~/.localshop/localshop.conf.py',
        default_settings='localshop.conf.defaults',
        settings_initializer=generate_settings,
        settings_envvar='LOCALSHOP_CONF',
    )

if __name__ == '__main__':
    main()
