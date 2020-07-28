# *-* coding: utf-8 *-*
# Ahmet Küçük <ahmetkucuk4@gmail.com>
# Zekeriya Akgül <zkry.akgul@gmail.com>

from flask import Response, Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token

from app.api.models import User
from app.auth.utils import login_smtp, create_user_account, update_user_account, add_token_to_database, revoke_token_status
from flask_jwt_extended import jwt_required, jwt_refresh_token_required, get_jwt_identity, unset_jwt_cookies, set_access_cookies, set_refresh_cookies, get_raw_jwt
from flask_restful import Resource
import datetime

class LoginApi(Resource):

    def post(self):

        body = request.get_json()
        email = body.get('email')
        password = body.get('password')

        user = User.query.filter_by(email=email).first()
        smtp_status, res_code = login_smtp(email, password)

        if smtp_status:

            if user:
                check_password = user.check_password(password)

                # Changed email password
                if not check_password and res_code == -1:
                    updated = update_user_account(email, password)

                    if not updated:
                        resp =  jsonify({'status': False, 'code': 'MC-100', 'content': 'Something went be wrong, please try again later'})
                        return resp, 400

            else:
                created = create_user_account(email, password)

                if not created:
                    resp =  jsonify({'status': False, 'code': 'MC-101', 'content': 'Something went be wrong, please try again later'})
                    return resp, 400

        else:
            resp =  jsonify({'status': False, 'code': 'MC-102', 'content': 'User credentials wrong or Imap server unreacheable'})
            return resp, 401

        expires = datetime.timedelta(days=7)
        access_token = create_access_token(identity=email, expires_delta=expires)
        refresh_token = create_refresh_token(identity=email)

        # Store the tokens in our store with a status of not currently revoked.
        add_token_to_database(access_token)
        add_token_to_database(refresh_token)

        resp =  jsonify({'status': True, 'access_token': access_token, 'refresh_token': refresh_token})
        set_access_cookies(resp, access_token)
        set_refresh_cookies(resp, refresh_token)
        resp.status_code = 201
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
