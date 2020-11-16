from app import app, db
from requests.auth import HTTPBasicAuth
from app.api.models import Account

import time
import requests
import json
import logging 


URL = app.config['SYNC_ENGINE_API_URL']

HEADERS = {
    'Content-Type': "application/json",
    'Cache-Control': "no-cache"
}

def _get_account_data_for_generic_account (data):
    # Get basic account information
    email = data.get('email', False)
    password = data.get('password', False)

    # Get connection security options
    SMTP_SEC_CONN = (data.get('smtp_secure', False) or app.config['SMTP_SEC_CONN'])
    IMAP_SEC_CONN = (data.get('imap_secure', False) or app.config['IMAP_SEC_CONN'])

    # Get host settings
    imp_host = (data.get("imap_server_host") or app.config['IMAP_HOST'])
    smtp_host = (data.get("smtp_server_host") or app.config['SMTP_HOST'])

    # Set SMTP port for given connection security options
    if SMTP_SEC_CONN:
        smtp_port = (data.get("smtp_server_port") or app.config['SMTPS_PORT'])
    else:
        smtp_port = (data.get("smtp_server_port") or app.config['SMTP_PORT'])

    # Set IMAP port for given connection security options
    if IMAP_SEC_CONN:     
        imp_port = (data.get("imap_server_port") or app.config['IMAPS_PORT'])
    else:
        imp_port = (data.get("imap_server_port") or app.config['IMAP_PORT'])
        
    return json.dumps({
        "type": "generic",
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
    })

def _get_account_data_for_google_account(data):
    email_address = data.get("email")
    scopes = data.get("scopes", "")
    client_id = data.get("client_id")

    sync_email = data.get("sync_email", True)
    sync_calendar = data.get("sync_calendar", False)
    sync_contacts = data.get("sync_contacts", False)

    refresh_token = data.get("refresh_token")
    authalligator = data.get("authalligator")

    return json.dumps({
        "email_address": email_address,
        "secret_type": secret_type,
        "secret_value": secret_value,
        "client_id": client_id,
        "scopes": scopes,
        "sync_email": sync_email,
        "sync_events": sync_calendar,
        "sync_contacts": sync_contacts,
    })

def _get_account_data_for_microsoft_account(data):
    email_address = data.get("email")
    scopes = data.get("scopes")
    client_id = data.get("client_id")

    refresh_token = data.get("refresh_token")
    authalligator = data.get("authalligator")

    sync_email = data.get("sync_email", True)

    return json.dumps({
        "email_address": email_address,
        "secret_type": secret_type,
        "secret_value": secret_value,
        "client_id": client_id,
        "scopes": scopes,
        "sync_email": sync_email
    })

def get_sync_status(email):
    db.session.commit()
    records = db.session.execute('SELECT sync_state,_sync_status from inbox.account WHERE _raw_address="{}";'.format(email)).fetchall()
    return records

def _get_user_by_email (email):
    # records = db.session.execute('SELECT sync_state,_sync_status from inbox.account WHERE _raw_address="{}";'.format(email)).fetchall()
    records = get_sync_status(email)
    if not records:
        return False
    else:
        ret = False
        for record in records:
            if record[0] == "running":
                return True
            else:
                rec_status = json.loads(record[1])
                if "sync_disabled_reason" not in rec_status.keys() or rec_status['sync_disabled_reason'] == "account deleted":
                    ret = False
    return ret

def sync_engine_update_account (user_id, data):
    response = requests.put(URL + '/accounts/' + user_id, data=data, headers=HEADERS)

    if response.status_code == 200:
        user_data = response.json()
        active_status = activate_user_sync(user_data['account_id'])
        return active_status, user_data
    else:
        return False, None

def sync_engine_create_account(data):
    max_tries = 5
    active_status = False
    user_data = None
    email = json.loads(data)['email_address']

    while max_tries > 0:
        max_tries -= 1
        response = requests.post(URL + '/accounts', data=data, headers=HEADERS)
        if response and response.status_code == 200:
            user_data = response.json()
            break

    db.session.flush()
    max_tries = 5
    while max_tries > 0:
        max_tries -= 1
        active_status = activate_user_sync(user_data['account_id'])
        if sync_engine_check_account_health(email) == 0:
            break
        else:
            active_status = False
    sync_engine_purge_faulty_account(email)
    return active_status, user_data

def sync_engine_purge_faulty_account(email):
    db.session.execute('DELETE from inbox.account WHERE _raw_address="{}" and sync_state is NULL;'.format(email))

def sync_engine_check_account_health(email):
    records = get_sync_status(email)
    print_to_stdout(str(records))
    if not records:
        # Account does not exist in db
        return -1 
    else:
        ret = False
        for record in records:
            if record[0] == "running":
                # Account healthy and running
                return 0
            else:
                rec_status = json.loads(record[1])
                if len(rec_status.keys()) == 0:
                    # Sync engine cant fully create account. _sync_status object is empty
                    ret = 1
    print_to_stdout("HEALTH RET:::: " + str(ret))
    return ret

def sync_engine_delete_account(account_id):
    response = requests.delete(URL + '/accounts/' + account_id, headers=HEADERS)
    if response.status_code == 200:
        return True
    else:
        return False

def sync_engine_account_dispatch (owner_mail, account_type, data, update = False):
    if account_type == "generic":
        payload = _get_account_data_for_generic_account (data)
    elif account_type == "gmail":
        payload = _get_account_data_for_google_account (data)
    elif account_type == "microsoft":
        payload = _get_account_data_for_microsoft_account (data)

    email = json.loads(payload)["email_address"]
    account = _get_user_by_email(email)

    if account:
        account_uuid = Account.query.filter(Account.email == email).first().uuid
        if update:
            # Update account for changed password
            return sync_engine_update_account(account_uuid, payload)

        # Make sure account sync is active?
        status = activate_user_sync(account_uuid)
        user_data = {'account_id': account_uuid}
        return status, user_data
    else:
        # Initial creation of account account
        return sync_engine_create_account(payload)

def activate_user_sync (user_id):
    status_payload = json.dumps({'sync_should_run': True})
    active_sync_status = requests.put(URL + '/status', data=status_payload, headers=HEADERS, auth=HTTPBasicAuth(user_id, ''))
    return active_sync_status.status_code == 200

def print_to_stdout(a): 
  
    logger = logging.getLogger('werkzeug')
    logger.info(a)