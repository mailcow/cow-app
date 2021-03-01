# *-* coding: utf-8 *-*
# Maintainers:
# Ahmet Küçük <ahmetkucuk4@gmail.com>
# Zekeriya Akgül <zkry.akgul@gmail.com>

from app import app, db
from flask import Response, Blueprint, request, jsonify, session
from app import httputils
from app.api.models import User, Account, Settings
from app.auth.utils import login_smtp, update_user_account, create_imap_account, create_gmail_account, create_microsoft_account, delete_account
from app.api.utils import create_sieve_script
from app.api.validation.validate import CowValidate
from flask_jwt_extended import jwt_required, get_jwt_identity, get_current_user
from flask_restful import Resource

import os
import requests
import traceback

REFRESH_REQUIRED_TYPES = ["email-filters", "email-vacation", "email-forward"]

API_LIST = [
    "send",
    "events",
    "calenders",
    "drafts",
    "sends",
    "folders",
    "labels",
    "messages",
    "threads",
    "contacts",
    "files"
]

class MailApi(Resource):

    name = "mail"

    @jwt_required
    def dispatch_request(self, *args, **kwargs):

        if request.method == 'OPTIONS':
            resp =  jsonify({'status': True})
            resp.status_code = 200
            return resp

        api_name = kwargs['api']

        if not api_name.split('/')[0] in API_LIST:
            resp =  jsonify({'status': False})
            resp.status_code = 404
            return resp

        account = session.get('account', False)

        if not account:
            resp =  jsonify({'status': False, 'code': 'MA-100', 'content': 'Could not verify authorization credentials'})
            resp.status_code = 500
            return resp

        URL = os.path.join(app.config['SYNC_ENGINE_API_URL'], api_name)

        requests_args = {}
        headers = dict(request.headers)

        if 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/json'

        params = request.args.copy()

        for key in list(headers.keys()):
            if key.lower() == 'content-length':
                del headers[key]

        requests_args['data'] = request.data
        requests_args['headers'] = headers
        requests_args['params'] = params
        requests_args['auth'] = requests.auth.HTTPBasicAuth(account['mail-uuid'], '')
        file = request.files.get('file')

        if file and "files" in api_name:
            del headers['Content-Type']
            requests_args['data'] = {}
            requests_args['files'] = {'file': (file.filename, file, file.mimetype)}

        response = requests.request(request.method, URL, **requests_args)

        proxy_response = Response(
            response.content,
            status=response.status_code,
            mimetype='application/json'
        )

        return proxy_response

class AccountApi(Resource):

    name = "account"

    @jwt_required
    def get(self):
        username = session.get('account')['username']
        user = User.query.filter_by(username=username).first()
        resp =  jsonify({'status': True, 'user_accounts': user.get_accounts})
        resp.status_code = 200
        return resp

    @jwt_required
    def post(self):
        if not request.is_json:
            resp = jsonify({'status': False, "content": "Missing JSON in request"})
            resp.status_code = 400
            return resp

        body = request.get_json()

        account_id = body.get("account_id", False)
        if account_id:
            try:
                username = session.get('account')['username']
                user = User.query.filter_by(username=username).first()
                account = Account.query.filter_by(id=account_id).first()
                session['account'] = {'id': account_id, 'username': username, 'mail-uuid': account.uuid}
                resp = jsonify({'status': True, 'code': 'AA-100', 'content': 'Active account changed'})
                resp.status_code = 200
                return resp
            except Exception as e:
                traceback.print_exc()
                resp = jsonify({'status': False, 'code': 'AA-105', 'content': 'Error occured while changing account.'})
                resp.status_code = 400
                return resp

        username =  session.get('account')['username'] # body.get('username', '')
        account_type = body.get('account_type', '') # generic,gmail,microsoft
        email = body.get('email', '')
        smtp_host = body.get('smtp_server_host')
        smtp_port = body.get('smtp_server_port')

        if not username or not account_type:
            resp = jsonify({'status': False, 'code': 'AA-100', 'content': 'User credentials are missing'})
            resp.status_code = 400
            return resp

        user = User.query.filter_by(username=username).first()
        if not user.has_account(email):
            try:
                if account_type == "generic":
                    password = body.get('password', '')
                    smtp_status, res_code = login_smtp(email, password, smtp_host, smtp_port)

                    if smtp_status:
                        if not create_imap_account(username, email, password, body):
                            raise Exception("Cannot create account")
                        resp = jsonify({'status': True, 'user_accounts': user.get_accounts, 'code': 'AA-101', 'content': 'New account was added'})
                        resp.status_code = 200
                    else:
                        resp = jsonify({'status': False, 'code': 'AA-100', 'content': 'User credentials are wrong'})
                        resp.status_code = 400
                    return resp
                elif account_type == "gmail":
                    if not create_gmail_account(username, email, body):
                        raise Exception("Cannot create account")
                    resp = jsonify({'status': True, 'user_accounts': user.get_accounts, 'code': 'AA-101', 'content': 'New account was added'})
                    resp.status_code = 200
                    return resp
                elif account_type == "microsoft":
                    if not create_microsoft_account(username, email, body):
                        raise Exception("Cannot create account")
                    resp = jsonify({'status': True, 'user_accounts': user.get_accounts, 'code': 'AA-101', 'content': 'New account was added'})
                    resp.status_code = 200
                    return resp
            except Exception as e:
                traceback.print_exc()
                resp = jsonify({'status': False, 'code': 'AA-102', 'content': 'Something went wrong while adding new account'})
                resp.status_code = 500
                return resp
        else:
            resp =  jsonify({'status': False, 'code': 'AA-103', 'content': 'User already have this account'})
            resp.status_code = 500
            return resp

    @jwt_required
    def put(self):
        if not request.is_json:
            resp = jsonify({'status': False, "content": "Missing JSON in request"})
            resp.status_code = 400
            return resp
        return Response({'test': 'success', 'status': True}, mimetype="application/json", status=200)

    @jwt_required
    def delete(self):
        if not request.is_json:
            resp = jsonify({'status': False, "content": "Missing JSON in request"})
            resp.status_code = 400
            return resp

        body = request.get_json()

        username = body.get('username', '')
        email = body.get('email', '')
        user = User.query.filter_by(username=username).first()

        if not user.has_account(email):
            resp = jsonify({'status': False, 'code': 'AD-100', 'content': 'User does not have this account'})
            resp.status_code = 400
            return resp

        status = delete_account(owner_username=username, email=email)

        if status:
            resp = jsonify({'status': True, 'code': 'AD-101', 'content': 'Account is successfully deleted'})
            resp.status_code = 200
            return resp
        else:
            resp = jsonify({'status': False, 'code': 'AD-102', 'content': 'Something went wrong while deleting account'})
            resp.status_code = 500
            return resp

class SettingApi(Resource, CowValidate):

    name = "settings"

    @jwt_required
    def get(self):
        username = get_jwt_identity()
        user_settings = Settings.query.join(User).filter(User.username == username).group_by(Settings.setting_type).all()

        response = {}
        for setting in user_settings:

            if not setting.section in response:
                response[setting.section] = {}

            if not setting.setting_type in response[setting.section]:
                response[setting.section][setting.setting_type] = type(setting.value)() # list or dict

            if type(setting.value) is list:
                response[setting.section][setting.setting_type] = setting.value
            else:
                response[setting.section][setting.setting_type]["accounts"] = setting.get_accounts
                response[setting.section][setting.setting_type]["enabled"] = setting.enabled
                response[setting.section][setting.setting_type] = {**response[setting.section][setting.setting_type], **setting.value}

        return httputils.response(response, 200)

    @jwt_required
    def post(self):
        if not request.is_json:
            resp = jsonify({'status': False, "content": "Missing JSON in request"})
            resp.status_code = 400
            return resp

        body = request.get_json()
        username = get_jwt_identity()
        old_password = body.get('old_password')
        new_password = body.get('new_password')

        if not old_password or not new_password:
            resp = jsonify({'status': False, "code": 100})
            resp.status_code = 400
            return resp

        smtp_status, res_code = login_smtp(username, old_password)
        if smtp_status:
            status = update_user_account(username, new_password, True)
            if status:
                return httputils.response({'status': True}, 200)
        else:
            resp = jsonify({'status': False, "code": 101})
            resp.status_code = 400
            return resp

        resp = jsonify({'status': False,  "code": 102})
        resp.status_code = 400
        return resp

    @jwt_required
    def put(self):
        if not request.is_json:
            resp = jsonify({'status': False, "content": "Missing JSON in request"})
            resp.status_code = 400
            return resp

        username = get_jwt_identity()
        user = User.query.filter(User.username == username).first()

        body = request.get_json()
        accounts = body.get('accounts') # ["user1@deneme.com", "user@gmail.com"]
        content = body.get('content') # settings json
        section = body.get('section') # mail|calender|contact|general
        need_refresh = False

        if not self.is_valid(content):
            resp = jsonify({'status': False, "content": "Json object is dirty"})
            resp.status_code = 400
            return resp

        setting_accounts = []
        for account in accounts:
            record = Account.query.filter(Account.email == account).filter(User.id == user.id).first()
            if record:
                setting_accounts.append(record)

        try:
            for setting_type, setting_value in content.items():
                user_setting = Settings.query.filter_by(section=section, setting_type=setting_type, user_id=user.id).one_or_none()

                if not user_setting:
                    resp = jsonify({'status': False, "content": "Setting not found"})
                    resp.status_code = 404
                    return resp

                user_setting.enabled = False
                user_setting.value = setting_value
                user.settings.append(user_setting)

                if 'enabled' in setting_value and type(setting_value['enabled']) is bool:
                    user_setting.enabled = setting_value['enabled']

                user_setting.accounts = []
                for setting_account in setting_accounts:
                    user_setting.accounts.append(setting_account)

                db.session.commit()

                if setting_type in REFRESH_REQUIRED_TYPES:
                    need_refresh = True

            if need_refresh:
                create_sieve_script()

            resp = jsonify({'status': True, 'code': 'ST-100', 'content': 'Successfully saved'})
            resp.status_code = 200
            return resp
        except Exception as e:
            import sys
            db.session.rollback()
            traceback.print_exc(file=sys.stderr)
            resp = jsonify({'status': False, 'code': 'ST-101', 'content': 'Something went wrong while deleting account'})
            resp.status_code = 500
            return resp

    @jwt_required
    def delete(self):
        pass

class DovecotWebhookApi(Resource):

    name = "dovecothook"

    def post(self):
        logger = logging.getLogger('werkzeug')
        a = request.form 
        logger.info(a)
