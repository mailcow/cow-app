from app.api.views import MailApi, AccountApi

def api_routes(api):
    api.add_resource(MailApi, '/api/email/<string:api>')
    api.add_resource(AccountApi, '/api/account')
