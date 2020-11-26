# Cow App

The backend app of Mailcow's CowUI web interface

### Installation

```
# Create virtualenvironment and source it
virtualenv -p python3 venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuring for your setings

Just go in the **config.py** and edit the variables for your dependencies. 

### Runing the development environment
```
export FLASK_ENV=development
export HOST=<ip or fqdn>
export PORT=<port>
python server.py
```

Go to browser and open the url http://HOST:PORT/
