from flask import Flask, request, jsonify
from app.config import Config
from app.extensions import db
from app.models import Bank, BankSecret, generate_secret_code, get_current_timestamp
from app.routes import init_app as init_routes
from app.scheduler import start_secret_regeneration_scheduler
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(process)d %(threadName)s: %(message)s'
)

logging.getLogger('apscheduler.executors.default').setLevel(logging.WARNING)
logging.getLogger('apscheduler.scheduler').setLevel(logging.INFO)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Erweiterungen initialisieren (z. B. SQLAlchemy)
    db.init_app(app)

    # API-Routen registrieren
    init_routes(app)


    with app.app_context():
        db.create_all()  # Erstelle alle Tabellen, falls nicht vorhanden
        prepopulate_banks(app)
        start_secret_regeneration_scheduler(app)  # Starte den Scheduler

    return app


def prepopulate_banks(app):
    with app.app_context():
        if Bank.query.count() == 0:
            banks_data = [
                {"name": "Top Giro Bank", "bank_code": "TG12345"},
                {"name": "Sparkasse Rosenheim", "bank_code": "SR67890"},
                {"name": "K-Classic Bank", "bank_code": "KC54321"},
                {"name": "VR Bank Rosenheim-Chiemsee", "bank_code": "VR98765"},
                {"name": "TH Rosenheimbank", "bank_code": "TH11223"}
            ]
            for data in banks_data:
                # Verwende data["bank_code"] statt data["bankCode"]
                bank = Bank(name=data["name"], bank_code=data["bank_code"])
                db.session.add(bank)
                db.session.flush()  # Damit bank.bank_code verfügbar ist
                for _ in range(6):
                    secret_code = generate_secret_code()
                    timestamp = get_current_timestamp()
                    # Hier ebenfalls: bank.bank_code verwenden
                    secret = BankSecret(bank_code=bank.bank_code, secret=secret_code, generated_at=timestamp)
                    db.session.add(secret)
            db.session.commit()
            print("Pre-Population: 5 Banken mit je 6 Geheimzahlen wurden eingefügt.")

