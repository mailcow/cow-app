# *-* coding: utf-8 *-*
# Ahmet Küçük <ahmetkucuk4@gmail.com>
# Zekeriya Akgül <zkry.akgul@gmail.com>
try:
	from dotenv import load_dotenv
	load_dotenv()
except Exception as e:
	print("Someting went wrong when try to load environments form .env file. Skipping...")

DEBUG = True

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Flask settings
SECRET_KEY = 'fgh7Ax809A8w16cv89as1ygASf7y8ASfg78g234'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Database
DB = os.environ.get('DATABASE_TYPE','mysql')
DB_HOST = os.environ.get('DATABASE_HOST','127.0.0.1')
DB_PORT = os.environ.get('DATABASE_PORT','3306')
DB_USER = os.environ.get('DATABASE_USER','mailcow')
DB_PASSWORD = os.environ.get('DATABASE_PASSWD','cFQf1p5ZqJHMBNkBgark3vRZXiPb')
DB_NAME = os.environ.get('DATABASE_NAME', 'mailcow')

# HTTP connection protocol
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
SMTP_SEC_CONN = (os.environ.get('SMTP_SEC_CONN', False) == "true")
SMTP_HOST = os.environ.get('SMTP_HOST', 'postfix')
SMTP_PORT = os.environ.get('SMTP_PORT', 25)
SMTPS_PORT = os.environ.get('SMTPS_PORT', 465)

# IMAP
IMAP_SEC_CONN = (os.environ.get('IMAP_SEC_CONN', False) == "true")
IMAP_HOST = os.environ.get('IMAP_HOST', 'dovecot')
IMAP_PORT = os.environ.get('IMAP_PORT', 143)
IMAPS_PORT = os.environ.get('IMAPS_PORT', 993)

# Sycn Engine
SYNC_ENGINE_WEB_PROTO = os.environ.get('SYNC_ENGINE_WEB_PROTO', 'http')
SYNC_ENGINE_HOST = os.environ.get('SYNC_ENGINE_HOST', 'syncengine')
SYNC_ENGINE_PORT = os.environ.get('SYNC_ENGINE_PORT', '5555')
SYNC_ENGINE_API_URL = "{}://{}:{}".format(SYNC_ENGINE_WEB_PROTO, SYNC_ENGINE_HOST, SYNC_ENGINE_PORT)

if DB == 'sqlite':
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, DB_NAME + '.db')
else:
    SQLALCHEMY_DATABASE_URI = DB + '://' + DB_USER + ':' + DB_PASSWORD + '@' + DB_HOST + ':' + str(DB_PORT) + '/' + DB_NAME