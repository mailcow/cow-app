# *-* coding: utf-8 *-*
# Ahmet Küçük <ahmetkucuk4@gmail.com>
# Zekeriya Akgül <zkry.akgul@gmail.com>
import os

from flask import Flask
from flask_restful import Api
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from app.api.exceptions import exceptions

# Define aplication
APP_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PATH = os.path.join(APP_PATH, 'app/sieve_templates/')
app = Flask(__name__, template_folder=TEMPLATE_PATH)
app.config.from_object('config')

# Define CORS
cors = CORS(app, resources={r"/api/*": {"origins": "*", "supports_credentials": True}})

# Define the database
db = SQLAlchemy(app)

# Define RESTFul
jwt = JWTManager(app)
api = Api(app, errors=exceptions)

from app.api.routes import api_routes
from app.auth.routes import auth_routes

api_routes(api)
auth_routes(api)

# Build the database:
db.create_all()