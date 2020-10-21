# *-* coding: utf-8 *-*
# Ahmet Küçük <ahmetkucuk4@gmail.com>
# Zekeriya Akgül <zkry.akgul@gmail.com>

from flask import Response, Blueprint, request, jsonify, session
from app.api.models import User
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource
from app import app

import os
import requests

class MailApi(Resource):

    API_LIST = [
        "events",
        "calenders",
        "drafts",
        "sends",
        "folders",
        "labels",
        "messages",
        "threads",
        "contacts"
    ]
    
    @jwt_required
    def dispatch_request(self, *args, **kwargs):

        api_name = kwargs['api']

        if not api_name.split('/')[0] in self.API_LIST:
            resp =  jsonify({'status': False})
            resp.status_code = 404
            return resp

        account_id = session.get('account_id', False)

        if not account_id:
            resp =  jsonify({'status': False, 'code': 'PX-100', 'content': 'Could not verify authorization credentials'})
            resp.status_code = 500
            return resp

        URL = os.path.join(app.config['SYNC_ENGINE_API_URL'], api_name)

        requests_args = {}
        headers = dict(request.headers)
        params = request.args.copy()

        for key in list(headers.keys()):
            if key.lower() == 'content-length':
                del headers[key]

        requests_args['data'] = request.data
        requests_args['headers'] = headers
        requests_args['params'] = params
        requests_args['auth'] = requests.auth.HTTPBasicAuth(account_id, '')

        response = requests.request(request.method, URL, **requests_args)

        proxy_response = Response(
            response.content,
            status=response.status_code,
            mimetype='application/json'
        )

        return proxy_response

class AccountApi(Resource):

    @jwt_required
    def get(self, api):
        return Response({'test': 'success', 'status': True}, mimetype="application/json", status=200)
