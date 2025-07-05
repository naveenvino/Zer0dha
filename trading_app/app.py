import os
from flask import Flask, render_template, current_app
from flask_sock import Sock
from flask_login import LoginManager
from flask_cors import CORS # Import CORS
from . import db
from .api import routes as api_routes
from .services.kite_service import get_kite_instance, start_ticker_websocket, stop_ticker_websocket
from kiteconnect.logging_config import setup_logging
import logging
from .models import User # Import User from models.py

def create_app(test_config=None):
    # create and configure the app
    setup_logging()
    app = Flask(__name__, instance_relative_config=True)
    CORS(app) # Enable CORS for all routes
    app.logger.addHandler(logging.getLogger("kiteconnect_logger").handlers[0]) # Add file handler
    app.logger.addHandler(logging.getLogger("kiteconnect_logger").handlers[1]) # Add console handler
    app.logger.setLevel(logging.INFO)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'index' # Redirect to index for login

    @login_manager.user_loader
    def load_user(user_id):
        return User.get(user_id)

    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'trading_app.sqlite')
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import db
    db.init_app(app)

    app.register_blueprint(api_routes.api_bp)

    sock = Sock(app)

    @app.route('/')
    def index():
        return render_template('index.html')

    @sock.route('/ws/live_data')
    def live_data(ws):
        current_app.logger.info("WebSocket connected.")
        # Start the KiteTicker and pass the websocket object to it
        start_ticker_websocket(ws)
        # Keep the websocket open until disconnected
        while True:
            message = ws.receive()
            if message is None:
                break
            current_app.logger.info(f"Received message from client: {message}")
        current_app.logger.info("WebSocket disconnected.")
        stop_ticker_websocket()

    return app
