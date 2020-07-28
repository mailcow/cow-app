from datetime import datetime

from sqlalchemy.orm.exc import NoResultFound
from flask_jwt_extended import decode_token

from app import app, db, jwt
from app.auth.exceptions import TokenNotFound
from app.auth.services import sync_engine_create_account
from app.auth.models import Token

def login_smtp(username, password):
    import smtplib

    if app.config['IS_SSL']:
        server = smtplib.SMTP_SSL(app.config['SMTP_HOST'], app.config['SMTP_PORT'])
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
    response = sync_engine_create_account(username, password)

    if response.status_code == 200:
        account = response.json()

    return False

def update_user_account (username, password):
    pass

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