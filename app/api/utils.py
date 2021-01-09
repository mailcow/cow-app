from app import app, db, jwt
from app.api.models import User, Account, Settings
from app.sieve_templates.template import Template
from flask import render_template
from sievelib.managesieve import Client

import sys
import traceback
import subprocess

def get_vacation_vars(user):
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
    payload["autoReplyEmailAddresses"] = ', '.join('"{0}"'.format(w) for mail_addr in data.get('autoReplyEmailAddresses'))
    payload["conditions_enabled"] =  (payload["startDateEnabled"] or payload["endDateEnabled"] or payload["ignoreLists"])

    if payload["conditions_enabled"]:
        conditions = []
        if payload["startDateEnabled"]:
            start_date_condition = 'currentdate :value "ge" "date" "{}"'.format(payload["startDate"]) # Date format: YYYY-MM-DD
            conditions.append(start_date_condition)
        if payload["endDateEnabled"]:
            end_date_condition = 'currentdate :value "le" "date" "{}"'.format(payload["endDate"]) # Date format: YYYY-MM-DD
            conditions.append(end_date_condition)
        if payload["ignoreLists"]:
            ignore_list_conditions = 'not exists ["list-help", "list-unsubscribe", "list-subscribe", "list-owner", "list-post", "list-archive", "list-id", "Mailing-List"], not header :comparator "i;ascii-casemap" :is "Precedence" ["list", "bulk", "junk"], not header :comparator "i;ascii-casemap" :matches "To" "Multiple recipients of*"'
            conditions.append(ignore_list_conditions)
        payload["conditions"] = ','.join(conditions)
    return payload

def get_filter_vars(data):
    return ""

def get_forward_vars(data):
    pass

def create_sieve_script(username, password):
    user = User.query.filter(User.username == username).first()

    # Get user vacation Settings
    vacation_settings = (Settings.query.filter(Settings.enabled == True).filter(Settings.section == "mail").filter(Settings.setting_type == "vacation").first()) or False

    # Get user filter settings
    filter_settings = (Settings.query.filter(Settings.enabled == True).filter(Settings.section == "mail").filter(Settings.setting_type == "filter").first()) or False

    # Get user forwarding settings
    forward_settings = (Settings.query.filter(Settings.enabled == True).filter(Settings.section == "mail").filter(Settings.setting_type == "forward").first()) or False

    sieve_payload = {}

    sieve_payload["vacation_settings"] = get_vacation_vars(vacation_settings) if vacation_settings else False
    sieve_payload["filter_settings"] = get_filter_vars(filter_settings) if filter_settings else False
    sieve_payload["forward_settings"] = get_forward_vars(forward_settings) if forward_settings else False

    # connect to the managesieve host
    client = Client(app.config['IMAP_HOST'])
    client.connect(username, password, starttls=True, authmech="PLAIN")
    script = Template("cowui.sieve", sieve_payload).render()
    client.setactive("")
    client.deletescript("cowui")
    client.putscript("cowui", script)
    client.setactive("cowui")
    client.logout()
