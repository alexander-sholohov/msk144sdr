from flask import Flask

from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.wrappers import Response

import config

app = Flask(__name__)
app.config['SECRET_KEY'] = config.FLASK_SECRET_KEY
app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER

if config.APP_PREFIX:
    app.wsgi_app = DispatcherMiddleware(
        Response('Not Found', status=404),
        {config.APP_PREFIX: app.wsgi_app}
    )


from app import spots
