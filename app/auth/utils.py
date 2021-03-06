
from datetime import datetime
from time import sleep

from sqlalchemy.orm.exc import NoResultFound
from flask_jwt_extended import decode_token
from pymemcache.client.base import Client
from flask import session

from app import app, db, jwt
from app.auth.exceptions import TokenNotFound
from app.auth.services import sync_engine_account_dispatch, sync_engine_delete_account
from app.auth.models import Token
from app.api.models import User, Account, Settings

import hashlib
import base64
import bcrypt
import uuid
import traceback

def login_smtp(username, password, smtp_host=None, smtp_port=None):
    import smtplib

    smtp_host = smtp_host or app.config['SMTP_HOST']

    if app.config['SMTP_SEC_CONN']:
        smtp_port = smtp_port or app.config['SMTPS_PORT']
        server = smtplib.SMTP_SSL(smtp_host, smtp_port)
    else:
        smtp_port = smtp_port or app.config['SMTP_PORT']
        server = smtplib.SMTP(smtp_host, smtp_port)

    try:
        server.login(username, password)
        server.quit()
        return True, 0

    except smtplib.SMTPAuthenticationError:
        server.quit()
        return False, -1

    except (smtplib.SMTPHeloError, smtplib.SMTPNotSupportedError, smtplib.SMTPException) as e:
        server.quit()
        return False, -2

def create_user_account (username, password):
    data = {
        "email": username,
        "password": password
    }
    status, user_data = sync_engine_account_dispatch(owner_mail=username, account_type="generic", data=data, update=False)

    if status:
        try:
            name, surname =get_name_from_mailcow_db(username)
            user = User(username=username, name=name, surname=surname)
            main_account = Account(email=username, password=hashlib.sha256(password.encode()).hexdigest(), is_main=True, uuid=user_data['account_id'])
            initial_settings = [('email', 'email-filters', []),
                                ('email', 'email-vacation', {}),
                                ('email', 'email-forward', {}),
                                ('email', 'email-general', {"accounts": [], "auto_refresh_every": "30m", "browser_notification": True, "enabled": False})]
            for settings_type in initial_settings:
                new_settings = Settings(enabled=False, section=settings_type[0], setting_type=settings_type[1], value=settings_type[2])
                new_settings.accounts.append(main_account)
                user.settings.append(new_settings)

            user.accounts.append(main_account)
            db.session.add(user)
            db.session.commit()
            return True
        except:
            traceback.print_exc()
            sync_engine_delete_account(user_data['account_id'])
            db.session.rollback()
            return False
    return False

def update_user_account (username, password, change_mailcow = False):
    data = {
        "email": username,
        "password": password
    }

    try:
        if change_mailcow:
            ret = change_mailcow_passwd(username, password)
            if not ret:
                raise False
            
        status, user_data = sync_engine_account_dispatch(owner_mail=username, account_type="generic", data=data, update=True)
        
        if not status:
            raise False

        main_account = Account.query.filter_by(email=username).first()
        main_account.password = hashlib.sha256(password.encode()).hexdigest()
        db.session.commit()
        session['main_user'] = data
        return True    
       
    except Exception as e:
        db.session.rollback()
        return False

def create_imap_account (owner_username, email, password, data):
    status, user_data = sync_engine_account_dispatch(owner_mail=owner_username, update=False, data=data, account_type="generic")

    if status:
        user = User.query.filter(User.username == owner_username).first()
        new_account = Account.query.filter(Account.email == email).first()
        if not new_account:
            new_account = Account(email=email, password=hashlib.sha256(password.encode()).hexdigest(), is_main=False, uuid=user_data['account_id'])
        user.accounts.append(new_account)
        db.session.commit()
        return True
    return False

def create_gmail_account(owner_username, email, data):
    status, user_data = sync_engine_account_dispatch(owner_mail=owner_username, update=False, data=data, account_type="gmail")

    if status:
        user = User.query.filter(User.username == owner_username).first()
        new_account = Account.query.filter(Account.email == email).first()
        if not new_account:
            new_account = Account(email=email, password=hashlib.sha256("dummy".encode()).hexdigest(), is_main=False, uuid=user_data['account_id'])
        user.accounts.append(new_account)
        db.session.commit()
        return True
    return False

def create_microsoft_account(owner_username, email, data):
    status, user_data = sync_engine_account_dispatch(owner_mail=owner_username, update=False, data=data, account_type="microsoft")

    if status:
        user = User.query.filter(User.username == owner_username).first()
        new_account = Account.query.filter(Account.email == email).first()
        if not new_account:
            new_account = Account(email=email, password=hashlib.sha256("dummy".encode()).hexdigest(), is_main=False, uuid=user_data['account_id'])
        user.accounts.append(new_account)
        db.session.commit()
        return True
    return False

def delete_account(owner_username, email):
    account_to_be_deleted = Account.query.filter(Account.email == email).first()

    status = sync_engine_delete_account(account_to_be_deleted.uuid)
    if status:
        try:
            db.session.delete(account_to_be_deleted)
            db.session.commit()
            return True
        except Exception as e:
            traceback.print_exc()
            return False
    return False

def get_name_from_mailcow_db(username):
    try:
        res = db.session.execute("SELECT name from mailcow.mailbox where username='{}';".format(username)).first().split(" ")
        fullname = res[0]
        surname = fullname.pop(-1)
        name = ' '.join(fullname)
        return  name, surname
    except Exception as e:
        traceback.print_exc()
        return username.split('@')[0], ""

def change_mailcow_passwd(username, new_passwd):
    passwd_scheme = app.config['MAILCOW_PASS_SCHEME']
    hashed_passwd = ""
    if passwd_scheme == "SSHA":
        salt = (uuid.uuid4().hex[:8]).encode()
        shaHH = hashlib.sha1((new_passwd.encode() + salt)).digest() + salt
        hashed_passwd = "{SSHA}" + base64.b64encode(shaHH).decode()
    elif passwd_scheme == "SSHA256":
        salt = (uuid.uuid4().hex[:8]).encode()
        shaHH = hashlib.sha256((new_passwd.encode() + salt)).digest() + salt
        hashed_passwd = "{SSHA256}" + base64.b64encode(shaHH).decode()
    elif passwd_scheme == "SSHA512":
        salt = (uuid.uuid4().hex[:8]).encode()
        shaHH = hashlib.sha512((new_passwd.encode() + salt)).digest() + salt
        hashed_passwd = "{SSHA512}" + base64.b64encode(shaHH).decode()
    elif passwd_scheme == "BLF-CRYPT":
        hashed_passwd = "{BLF-CRYPT}" + bcrypt.hashpw(new_passwd.encode(), bcrypt.gensalt()).decode()
    
    try:
        db.session.execute("UPDATE mailbox SET password='{}' where username='{}'".format(hashed_passwd, username))
        if not app.config['SKIP_SOGO']:
            return update_sogo_static_view()
        return True
    except Exception as e:
        traceback.print_exc()
        return False
    
def update_sogo_static_view():
    sogo_query1 =  "SELECT 'OK' FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'sogo_view';"
    sogo_query2 = """REPLACE INTO _sogo_static_view (`c_uid`, `domain`, `c_name`, `c_password`, `c_cn`, `mail`, `aliases`, `ad_aliases`, `ext_acl`, `kind`, `multiple_bookings`) 
    SELECT `c_uid`, `domain`, `c_name`, `c_password`, `c_cn`, `mail`, `aliases`, `ad_aliases`, `ext_acl`, `kind`, `multiple_bookings` 
    from sogo_view"""
    sogo_query3 = "DELETE FROM _sogo_static_view WHERE `c_uid` NOT IN (SELECT `username` FROM `mailbox` WHERE `active` = '1');"
    
    try:
        result_count = db.session.execute(sogo_query1).fetchall()
        if result_count != 0:
            db.session.execute(sogo_query2)
            db.session.execute(sogo_query3)
        flush_memcached()
        return True
    except Exception as e:
        traceback.print_exc()
        return False

def flush_memcached():
    c = Client(("memcached", "11211"))
    c.flush_all()

@jwt.token_in_blacklist_loader
def check_if_token_revoked(decoded_token):
    return is_token_revoked(decoded_token)

def _epoch_utc_to_datetime(epoch_utc):
    return datetime.fromtimestamp(epoch_utc)

def add_token_to_database(encoded_token):

    identity_claim = app.config['JWT_IDENTITY_CLAIM']
    decoded_token = decode_token(encoded_token)
    jti = decoded_token['jti']
    token_type = decoded_token['type']
    user_identity = decoded_token[identity_claim]
    expires = _epoch_utc_to_datetime(decoded_token['exp'])
    revoked = False

    db_token = Token(
        jti=jti,
        token_type=token_type,
        user_identity=user_identity,
        expires=expires,
        revoked=revoked,
    )
    db.session.add(db_token)
    db.session.commit()

def is_token_revoked(decoded_token):

    jti = decoded_token['jti']
    try:
        token = Token.query.filter_by(jti=jti).one()
        return token.revoked
    except NoResultFound:
        return True

def get_user_tokens(user_identity):
    return Token.query.filter_by(user_identity=user_identity).all()

def revoke_token_status(decoded_token, user, status):

    jti = decoded_token['jti']
    try:
        token = Token.query.filter_by(jti=jti, user_identity=user).one()
        token.revoked = status
        db.session.commit()
    except NoResultFound:
        raise TokenNotFound("Could not find the token {}".format(jti))

def prune_database():
    """
        Delete tokens that have expired from the database.
        How (and if) you call this is entirely up you. You could expose it to an
        endpoint that only administrators could call, you could run it as a cron,
        set it up with flask cli, etc.
    """
    now = datetime.now()
    expired = Token.query.filter(Token.expires < now).all()
    for token in expired:
        db.session.delete(token)
    db.session.commit()

def check_database_status(max_tries=5):
    is_database_working = True
    try_count = 0

    while try_count < max_tries:
        try_count += 1
        try:
            # to check database we will execute a sample query
            User.query.all()
            is_database_working = True
            break
        except Exception as e:
            db.session.rollback()
            traceback.print_exc()
            is_database_working = False
        sleep(1)
    return is_database_working
