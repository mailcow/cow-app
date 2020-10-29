from app.api.views import MailApi, AccountApi

def api_routes(api):
    api.add_resource(MailApi, '/api/email/<path:api>', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    api.add_resource(AccountApi, '/api/account')
