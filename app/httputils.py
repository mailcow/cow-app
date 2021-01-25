# *-* coding: utf-8 *-*
# Ahmet Küçük <ahmetkucuk4@gmail.com>
# Zekeriya Akgül <zkry.akgul@gmail.com>

from flask import jsonify

# NOT_FOUND = jsonify({"status": False})
# AUTHORIZATION_ERROR = jsonify({"status": False, "code": "MA-100", "content": "Could not verify authorization credentials"})
# MISSING_REQUEST = jsonify({"status": False, "content": "Missing JSON in request"})
# CREDENTIALS_MISSING = jsonify({"status": False, "code": "AA-100", "content": "User credentials are missing"})

def response(content, code = 200):
    response = jsonify(content)
    response.status_code = code
    return response
