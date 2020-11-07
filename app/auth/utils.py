
from datetime import datetime

from sqlalchemy.orm.exc import NoResultFound
from flask_jwt_extended import decode_token

from app import app, db, jwt
from app.auth.exceptions import TokenNotFound
from app.auth.services import sync_engine_account_dispatch, sync_engine_delete_account
from app.auth.models import Token
from app.api.models import User, Account

import hashlib
import traceback

def login_smtp(username, password):
    import smtplib

    if app.config['SMTP_SEC_CONN']:
        server = smtplib.SMTP_SSL(app.config['SMTP_HOST'], app.config['SMTPS_PORT'])
    else:
        server = smtplib.SMTP(app.config['SMTP_HOST'], app.config['SMTP_PORT'])

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
        user = User(username=username)
        main_account = Account(email=username, password=hashlib.sha256(password.encode()).hexdigest(), is_main=True, uuid=user_data['account_id'])

        user.accounts.append(main_account)
        db.session.add(user)
        db.session.commit()
        return True
    return False

def update_user_account (username, password):
    data = {
        "email": username,
        "password": password
    }
    status, user_data = sync_engine_account_dispatch(owner_mail=username, account_type="generic", data=data, update=True)

    if status:
        main_account = Account.query.filter_by(email=username).first()
        main_account.password = hashlib.sha256(password.encode()).hexdigest()
        db.session.commit()
        return True

    return False

def create_imap_account (owner_username, email, password, data):
    status, user_data = sync_engine_account_dispatch(owner_mail=owner_username, update=False, data=data, account_type="generic")

    if status:
        user = User.query.filter(User.username == owner_username).first()
        main_account = Account(email=email, password=hashlib.sha256(password.encode()).hexdigest(), is_main=False, uuid=user_data['account_id'])
        user.accounts.append(main_account)
        db.session.commit()
        return True
    return False

def create_gmail_account(owner_username, email, data):
    status, user_data = sync_engine_account_dispatch(owner_mail=owner_username, update=False, data=data, account_type="gmail")

    if status:
        user = User.query.filter(User.username == owner_username).first()
        main_account = Account(email=email, password=hashlib.sha256("dummy".encode()).hexdigest(), is_main=False, uuid=user_data['account_id'])
        user.accounts.append(main_account)
        db.session.commit()
        return True
    return False

def create_microsoft_account(owner_username, email, data):
    status, user_data = sync_engine_account_dispatch(owner_mail=owner_username, update=False, data=data, account_type="microsoft")

    if status:
        user = User.query.filter(User.username == owner_username).first()
        main_account = Account(email=email, password=hashlib.sha256("dummy".encode()).hexdigest(), is_main=False, uuid=user_data['account_id'])
        user.accounts.append(main_account)
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
