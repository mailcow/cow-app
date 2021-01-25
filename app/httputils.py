# *-* coding: utf-8 *-*
# Ahmet Küçük <ahmetkucuk4@gmail.com>
# Zekeriya Akgül <zkry.akgul@gmail.com>

from flask import jsonify

OK = jsonify({"status": True}, status_code = 200)
NOT_FOUND = jsonify({"status": False}, status_code = 404)
AUTHORIZATION_ERROR = jsonify({"status": False, "code": "MA-100", "content": "Could not verify authorization credentials"}, status_code = 500)
MISSING_REQUEST = jsonify({"status": False, "content": "Missing JSON in request"}, status_code = 400)
CREDENTIALS_MISSING = jsonify({"status": False, "code": "AA-100", "content": "User credentials are missing"}, status_code = 400)
