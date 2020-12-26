# *-* coding: utf-8 *-*
# Maintainers:
# Ahmet Küçük <ahmetkucuk4@gmail.com>
# Zekeriya Akgül <zkry.akgul@gmail.com>

from flask import Response, Blueprint, request, jsonify, session
from flask_jwt_extended import create_access_token, create_refresh_token

from app import db
from app.api.models import User
from app.auth.utils import login_smtp, create_user_account, update_user_account, add_token_to_database, revoke_token_status, check_database_status
from flask_jwt_extended import jwt_required, jwt_refresh_token_required, get_jwt_identity, unset_jwt_cookies, set_access_cookies, set_refresh_cookies, get_raw_jwt
from flask_restful import Resource
import datetime
import traceback

class LoginApi(Resource):

    def post(self):
        try:
            if not request.is_json:
                resp = jsonify({'status': False, "content": "Missing JSON in request"})
                resp.status_code = 400
                return resp

            body = request.get_json()

            email = body.get('email', '')
            password = body.get('password', '')

            if not email or not password:
                resp = jsonify({'status': False, 'code': 'MC-100', 'content': 'User credentials wrong'})
                resp.status_code = 400
                return resp

            db_status = check_database_status()
            if not db_status:
                resp = jsonify({'status': False, 'code': 'DB-100', 'content': 'DB does not ready yet!'})
                resp.status_code = 400
                return resp

            user = User.query.filter_by(username=email).first()
            smtp_status, res_code = login_smtp(email, password)
            is_first_login = False

            if smtp_status:

                if user:
                    check_password = user.main_account.check_password(password)

                    # Changed email password & update sync-engine password
                    if not check_password and res_code == -1:
                        updated = update_user_account(email, password)

                        if not updated:
                            resp =  jsonify({'status': False, 'code': 'MC-101', 'content': 'Something went be wrong, please try again later'})
                            resp.status_code = 400
                            return resp

                else:
                    is_first_login = True
                    # Create sync-engine account
                    created = create_user_account(email, password)

                    if not created:
                        resp =  jsonify({'status': False, 'code': 'MC-102', 'content': 'Something went be wrong, please try again later'})
                        resp.status_code = 400
                        return resp

            else:
                resp =  jsonify({'status': False, 'code': 'MC-103', 'content': 'User credentials wrong or Imap server unreacheable'})
                resp.status_code = 401
                return resp

            user = User.query.filter_by(username=email).first()
            expires = datetime.timedelta(days=7)
            access_token = create_access_token(identity=email, expires_delta=expires)
            refresh_token = create_refresh_token(identity=email)
            expires_date = datetime.datetime.now() + expires
            session['account'] = {'id': user.main_account.id, 'username': email, 'mail-uuid': user.main_account.uuid}

            # Store the tokens in our store with a status of not currently revoked.
            add_token_to_database(access_token)
            add_token_to_database(refresh_token)
            resp =  jsonify({'status': True, 'access_token': access_token, 'refresh_token': refresh_token, 'expires': str(expires_date),
                             'user_accounts': user.get_accounts, 'first_login': is_first_login})

            set_access_cookies(resp, access_token)
            set_refresh_cookies(resp, refresh_token)
            resp.status_code = 201
            return resp
        except Exception as e:
            traceback.print_exc()
            db.session.rollback()
            resp =  jsonify({'status': False, 'code': 'MC-104', 'content': 'Something went be wrong, please try again later'})
            resp.status_code = 500
            return resp
            
class RefreshTokenApi(Resource):

    @jwt_refresh_token_required
    def post(self):
        # Create the new access token
        current_user = get_jwt_identity()
        expires = datetime.timedelta(days=7)
        access_token = create_access_token(identity=current_user, expires_delta=expires)
        refresh_token = create_refresh_token(identity=email)

        # Store the tokens in our store with a status of not currently revoked.
        add_token_to_database(access_token)
        add_token_to_database(refresh_token)

        # Set the access JWT and CSRF double submit protection cookies
        # in this response

        resp =  jsonify({'status': True, 'access_token': access_token, 'refresh_token': refresh_token})
        set_access_cookies(resp, access_token)
        set_refresh_cookies(resp, refresh_token)
        resp.status_code = 201
        return resp

class LogoutApi(Resource):

    # Because the JWTs are stored in an httponly cookie now, we cannot
    # log the user out by simply deleting the cookie in the frontend.
    # We need the backend to send us a response to delete the cookies
    # in order to logout. unset_jwt_cookies is a helper function to
    # do just that.

    @jwt_required
    def post(self):
        user_identity = get_jwt_identity()
        revoke_token_status(get_raw_jwt(), user_identity, True)
        resp = Response({'logout': 'success', 'status': True}, mimetype="application/json", status=200)
        unset_jwt_cookies(resp)
        return resp

