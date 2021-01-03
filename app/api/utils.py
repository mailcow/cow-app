from app import app, db, jwt
from app.api.models import User, Account, Settings
from app.sieve_templates import Template
from flask import render_template
from sievelib.managesieve import Client

import sys
import traceback
import subprocess

def build_vacation_sieve(data):
    """
    Example data['content']
    Vacation:{
          "startDateEnabled": True,
          "startDate":1609621200, # Timestamp
          "endDateEnabled": True,
          "endDate":1609707600, # Timestamp
          "enabled":True,
          "customSubjectEnabled": True,
          "ignoreLists": False,
          "alwaysSend": True,
          "customSubject": "DENEME subject",
          "autoReplyText": "Bu bir otomatik dönüttür.",
          "discardMails": False,
          "autoReplyEmailAddresses":[
             "user1@deneme.com"
          ],
          "daysBetweenResponse":7
    }
    """
    action = data.get('action') # enable|disable
    accounts = data.get('accounts')
    content = data.get('content')

    if action == 'enable':
        payload = {}
        payload["enabled"] = data.get('enabled', True)
        # Date Settings
        payload["daysBetweenResponse"] = data.get('daysBetweenResponse', 7)
        payload["startDateEnabled"] = data.get('startDateEnabled', False)
        payload["startDate"] = data.get('startDate')
        payload["endDateEnabled"] = data.get('endDateEnabled', False)
        payload["endDate"] = data.get('endDate')
        # Sending/Recieving options
        payload["ignoreLists"] = data.get('ignoreLists', False)
        payload["alwaysSend"] = data.get('alwaysSend', True)
        payload["discardMails"] = data.get('discardMails')
        #  Content options
        payload["customSubjectEnabled"] = data.get('customSubjectEnabled', False)
        payload["customSubject"] = data.get('customSubject', False)
        payload["autoReplyText"] = data.get('autoReplyText')
        payload["autoReplyEmailAddresses"] = accounts

        try:
            return Template("vocation.sieve", payload).render()
        except Exception as e:
            log.error("Error was occured while building sieve script")
            return False
    else:
        return ""

def build_filter_sieve(data):
    return ""

def build_forward_sieve(data):
    pass

def create_sieve_script(username):
    user = User.query.filter(User.username == username).first()
    for setting in user.settings:
        pass
    # connect to the managesieve host
    username = None
    password = None
    client = Client(app.config['IMAP_HOST'])
    client.connect(username, password, starttls=True, authmech="PLAIN")
    script = Template("vocation.sieve", payload).render()
    client.setactive("")
    client.deletescript("cowui")
    client.putscript("cowui", script)
    client.setactive("cowui")
    client.logout()
