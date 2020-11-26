from app import app
from config import HOST, HOST_PORT

app.run(host=HOST, port=HOST_PORT, debug=True)
