from flask import Flask, request, jsonify
from app.config import Config
from app.extensions import db
from app.models import Bank, BankSecret, generate_secret_code, get_current_timestamp
from app.routes import init_app as init_routes
from app.scheduler import start_secret_regeneration_scheduler
import logging

# Configure root logger to output INFO-level messages with timestamp, severity, process ID, thread name, and message
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(process)d %(threadName)s: %(message)s'
)
# Reduce verbosity of the APScheduler executors logger to WARNING
logging.getLogger('apscheduler.executors.default').setLevel(logging.WARNING)
# Keep APScheduler scheduler logs at INFO level
logging.getLogger('apscheduler.scheduler').setLevel(logging.INFO)

def create_app():
    """
    Create and configure the Flask application instance.

    This function:
    - Initializes the Flask app with settings from Config.
    - Sets up the SQLAlchemy database extension.
    - Registers API routes.
    - Creates database tables if they do not exist.
    - Populates initial bank data if the banks table is empty.
    - Starts a background scheduler to regenerate bank secrets periodically.

    Returns:
        app (Flask): The configured Flask application.
    """
    app = Flask(__name__)
    # Load configuration from Config object
    app.config.from_object(Config)

    # Initialize database extension (e.g., SQLAlchemy)
    db.init_app(app)

    # Register API routes with the application
    init_routes(app)

    # Create database tables and pre-populate data within the application context
    with app.app_context():
        db.create_all()  # Create all tables defined by SQLAlchemy models
        prepopulate_banks(app)  # Insert default banks and their secrets
        start_secret_regeneration_scheduler(app)  # Launch scheduler for secret rotation

    return app


def prepopulate_banks(app):
    """
    Insert initial bank records and their corresponding secret codes into the database.

    This function only runs when the banks table is empty. It:
    - Defines a list of default bank entries with name and bank code.
    - For each bank, creates six secret codes with timestamps.
    - Commits all records to the database.

    Args:
        app (Flask): The Flask application instance providing the database context.
    """
    with app.app_context():
        # Only run if no banks currently exist
        if Bank.query.count() == 0:
            # Default data for initial banks
            banks_data = [
                {"name": "Top Giro Bank", "bank_code": "TG12345"},
                {"name": "Sparkasse Rosenheim", "bank_code": "SR67890"},
                {"name": "K-Classic Bank", "bank_code": "KC54321"},
                {"name": "VR Bank Rosenheim-Chiemsee", "bank_code": "VR98765"},
                {"name": "TH Rosenheimbank", "bank_code": "TH11223"}
            ]
            # Loop through each bank entry and insert into the database
            for data in banks_data:
                bank = Bank(name=data["name"], bank_code=data["bank_code"])
                db.session.add(bank)
                db.session.flush()  # Ensure bank.bank_code is populated before creating secrets

                # Generate six secret codes per bank
                for _ in range(6):
                    secret_code = generate_secret_code()  # Create a random secret code
                    timestamp = get_current_timestamp()   # Get current timestamp for record
                    secret = BankSecret(
                        bank_code=bank.bank_code,
                        secret=secret_code,
                        generated_at=timestamp
                    )
                    db.session.add(secret)
            # Commit all new bank and secret records at once
            db.session.commit()
            print("Pre-Population: 5 banks with 6 secrets each have been added.")
