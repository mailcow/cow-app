from app import app
from requests.auth import HTTPBasicAuth

import requests
import json

URL = app.config['SYNC_ENGINE_API_URL']

HEADERS = {
    'Content-Type': "application/json",
    'Cache-Control': "no-cache"
}

def _get_genric_data (email, password, imp_host = None, imp_port = None, smtp_host = None, smtp_port = None, ac_type = "generic"):
    # Get connection security options
    SMTP_SEC_CONN = app.config['SMTP_SEC_CONN']
    IMAP_SEC_CONN = app.config['IMAP_SEC_CONN']

    # Get host settings
    imp_host = (imp_host or app.config['IMAP_HOST'])
    smtp_host = (smtp_host or app.config['SMTP_HOST'])

    # Set SMTP port for given connection security options
    if SMTP_SEC_CONN:
        smtp_port = (smtp_port or app.config['SMTPS_PORT'])
    else:
        smtp_port = (smtp_port or app.config['SMTP_PORT'])

    # Set IMAP port for given connection security options
    if IMAP_SEC_CONN:     
        imp_port = (imp_port or app.config['IMAPS_PORT'])
    else:
        imp_port = (imp_port or app.config['IMAP_PORT'])
        

    # Type: generic | gmail | microsoft

    data = {
        "type": ac_type,
        "email_address": email,
        "sync_email": True,
        "sync_calendar": True,
        "imap_server_host": imp_host,
        "imap_server_port": imp_port,
        "imap_username": email,
        "imap_password": password,
        "smtp_server_host": smtp_host,
        "smtp_server_port": smtp_port,
        "smtp_username": email,
        "smtp_password": password
    }

    return json.dumps(data)

def _get_user_by_email (email):
    response = requests.get(URL + '/accounts?email_address=' + email)
    if response.status_code == 200:
        data = response.json()
        if len(data) > 0:
            return response.json()[0]

    return False

def sync_engine_update_account (user_id, data):
    response = requests.put(URL + '/accounts/' + user_id, data=data, headers=HEADERS)

    if response.status_code == 200:
        user_data = response.json()
        active_status = activate_user_sync(user_data['account_id'])
        return active_status, user_data
    else:
        return False, None

def sync_engine_create_account(data):
    response = requests.post(URL + '/accounts', data=data, headers=HEADERS)

    if response.status_code == 200:
        user_data = response.json()
        active_status = activate_user_sync(user_data['account_id'])
        return active_status, user_data
    else:
        return False, None

def sync_engine_account_dispatch (email, password, update = False):

    payload = _get_genric_data (email, password)
    user = _get_user_by_email(email)

    if user:
        if update:
            # Update user for changed password
            return sync_engine_update_account(user['account_id'], payload)

        # Make sure account sync is active?
        status = activate_user_sync(user['account_id'])
        return status, user
    else:
        # Initial creation of user account
        return sync_engine_create_account(payload)

def activate_user_sync (user_id):
    status_payload = json.dumps({'sync_should_run': True})
    active_sync_status = requests.put(URL + '/status', data=status_payload, headers=HEADERS, auth=HTTPBasicAuth(user_id, ''))
    return active_sync_status.status_code == 200
