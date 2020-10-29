from app.auth.views import LoginApi, LogoutApi, RefreshTokenApi

def auth_routes(api):
    api.add_resource(LoginApi, '/api/auth/login/')
    api.add_resource(RefreshTokenApi, '/api/auth/refresh/')
    api.add_resource(LogoutApi, '/api/auth/logout/')
