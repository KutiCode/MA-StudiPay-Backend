from flask import Flask
from app.config import Config
from app.extensions import db
from app.routes import init_app as init_routes


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Erweiterungen initialisieren (z. B. SQLAlchemy)
    db.init_app(app)

    # API-Routen registrieren
    init_routes(app)

    return app
