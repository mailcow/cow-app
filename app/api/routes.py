from app.api.views import MailApi, AccountApi, SettingApi, DovecotWebhookApi

def api_routes(api):
    api.add_resource(MailApi, '/api/email/<path:api>', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    api.add_resource(AccountApi, '/api/account/')
    api.add_resource(DovecotWebhookApi, '/api/dovecothook/')
    api.add_resource(SettingApi, '/api/settings/')
    api.add_resource(SettingApi, '/api/settings/password/', endpoint="password")
