# *-* coding: utf-8 *-*
# Ahmet Küçük <ahmetkucuk4@gmail.com>
# Zekeriya Akgül <zkry.akgul@gmail.com>

from flask import Response, Blueprint, request
from app.api.models import User
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource

class MailApi(Resource):

    @jwt_required
    def get(self, api):
        return Response({'test': 'success', 'status': True}, mimetype="application/json", status=200)

class AccountApi(Response):

    @jwt_required
    def get(self, api):
        return Response({'test': 'success', 'status': True}, mimetype="application/json", status=200)
