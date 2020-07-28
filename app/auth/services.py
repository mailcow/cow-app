from app.api.models import User
from app import app
import requests


def sync_engine_create_account(email, password, imp_host = None, imp_port = None, smtp_host = None, smtp_port = None, provider = "custom"):

    url = app.config['SYNC_ENGINE_API_URL']

    IS_SSL = app.config['IS_SSL']

    if IS_SSL:
        imp_host = (imp_host or app.config['IMAPS_HOST'])
        imp_port = (imp_host or app.config['IMAPS_HOST'])
        smtp_host = (smtp_host or app.config['SMTPS_HOST'])
        smtp_port = (smtp_port or app.config['SMTPS_PORT'])
    else:
        imp_host = (imp_host or app.config['IMAP_HOST'])
        imp_port = (imp_host or app.config['IMAP_HOST'])
        smtp_host = (smtp_host or app.config['SMTP_HOST'])
        smtp_port = (smtp_port or app.config['SMTP_PORT'])

    data = {
        "provider": provider,
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

    response = requests.post(url + '/accounts/', data)

    return response
