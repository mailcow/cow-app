class TokenNotFound(Exception):
    pass

exceptions = {
     "TokenNotFound": {
         "message": "Token could not be found in the database",
         "status": 401
     }
}
