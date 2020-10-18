# *-* coding: utf-8 *-*
# Ahmet Küçük <ahmetkucuk4@gmail.com>
# Zekeriya Akgül <zkry.akgul@gmail.com>

DEBUG = True

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Database
DB = os.environ.get('DATABASE_TYPE','mysql')
DB_HOST = os.environ.get('DATABASE_HOST','127.0.0.1')
DB_PORT = os.environ.get('DATABASE_PORT','3406')
DB_USER = os.environ.get('DATABASE_USER','mailcow')
DB_PASSWORD = os.environ.get('DATABASE_PASSWD','cFQf1p5ZqJHMBNkBgark3vRZXiPb')
DB_NAME = os.environ.get('DATABASE_NAME', 'mailcow')

IS_SSL = (os.environ.get('SSL', False) == "true")

# Authentication 
JWT_ACCESS_COOKIE_PATH = '/'
JWT_REFRESH_COOKIE_PATH = '/'
JWT_COOKIE_CSRF_PROTECT = False
JWT_CSRF_IN_COOKIES = False
JWT_SECRET_KEY = os.environ.get('SECRET_KEY', 'CHANGE_ME')
JWT_BLACKLIST_ENABLED = True
JWT_COOKIE_SECURE = IS_SSL # Only allow JWT cookies to be sent over https. In production, this should likely be True
JWT_TOKEN_LOCATION =  ('headers', 'cookies')
JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']

# SMTP
SMTP_HOST = os.environ.get('SMTP_HOST', 'postfix')
SMTP_PORT = os.environ.get('SMTP_PORT', 25)
SMTPS_PORT = os.environ.get('SMTPS_PORT', 465)

# IMAP
IMAP_HOST = os.environ.get('IMAP_HOST', 'dovecot')
IMAP_PORT = os.environ.get('IMAP_PORT', 143)
IMAPS_PORT = os.environ.get('IMAPS_PORT', 993)

SYNC_ENGINE_API_URL = 'http://syncengine:5555'

if DB == 'sqlite':
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, DB_NAME + '.db')
else:
    SQLALCHEMY_DATABASE_URI = DB + '://' + DB_USER + ':' + DB_PASSWORD + '@' + DB_HOST + ':' + str(DB_PORT) + '/' + DB_NAME
