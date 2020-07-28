from app.api.views import MailApi

def api_routes(api):
    api.add_resource(MailApi, '/api/email/<string:api>')