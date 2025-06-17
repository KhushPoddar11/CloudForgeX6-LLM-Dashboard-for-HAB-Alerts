from flask import Flask
from routes.api_routes import api_routes
import logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

app.register_blueprint(api_routes)

if __name__ == '__main__':
    app.run(debug=True)
