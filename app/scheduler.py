"""
Scheduler module for the application.

This module configures and starts a background scheduler that periodically regenerates
secret codes for all banks. It uses APScheduler to run the regeneration job at a fixed interval.
"""

import os
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from app.models import Bank, BankSecret, generate_secret_code, get_current_timestamp
from app.extensions import db


def regenerate_bank_secrets(app):
    """
    Regenerate and store new secret codes for every bank in the database.

    This function is intended to be run inside the Flask application context. It deletes
    existing secrets for each bank and generates six new secret codes, recording the
    generation timestamp.
    """
    pid = os.getpid()
    logging.info(f"[{pid}] Attempting to run regenerate_bank_secrets...")

    # Enter the Flask application context to access the database
    with app.app_context():
        try:
            # Retrieve all banks from the database
            banks = Bank.query.all()
            logging.info(f"[{pid}] Regenerating secrets for {len(banks)} banks...")

            for bank in banks:
                # Choose an appropriate synchronization strategy before deleting old secrets
                BankSecret.query.filter_by(bank_code=bank.bank_code).delete(synchronize_session='fetch')
                # db.session.flush()  # Optional, depending on session behavior

                # Generate and store six new secret codes per bank
                for _ in range(6):
                    secret_code = generate_secret_code()
                    timestamp = get_current_timestamp()
                    new_secret = BankSecret(
                        bank_code=bank.bank_code,
                        secret=secret_code,
                        generated_at=timestamp
                    )
                    db.session.add(new_secret)

            # Commit all changes to the database
            db.session.commit()
            logging.info(f"[{pid}] Successfully regenerated bank secrets.")
        except Exception as e:
            # Roll back the transaction on error and log the full stack trace
            db.session.rollback()
            logging.error(f"[{pid}] Error during secret regeneration: {e}", exc_info=True)


def start_secret_regeneration_scheduler(app):
    """
    Initialize and start the background scheduler to periodically invoke
    the regenerate_bank_secrets function.

    This function ensures the scheduler is only started once (avoiding multiple
    schedulers during Flask's auto-reload) and sets up a job to run every 3 minutes.
    """
    pid = os.getpid()

    # Only initialize the scheduler in the main process (not during Werkzeug's reload)
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        logging.info(f"[{pid}] Initializing scheduler...")

        scheduler = BackgroundScheduler(daemon=True)

        # Schedule the secret regeneration job to run every 3 minutes
        scheduler.add_job(
            func=regenerate_bank_secrets,
            trigger='interval',
            minutes=3,
            args=[app],
            id='regenerate_bank_secrets_job',
            replace_existing=True
        )

        try:
            scheduler.start()
            logging.info(f"[{pid}] Secret-Regeneration-Scheduler started successfully.")
        except (KeyboardInterrupt, SystemExit):
            # Gracefully shut down on exit signals
            logging.info(f"[{pid}] Shutting down scheduler on exit signal.")
            if scheduler.running:
                scheduler.shutdown()
        except Exception as e:
            # Log any startup failures with stack trace
            logging.error(f"[{pid}] Failed to start scheduler: {e}", exc_info=True)
    else:
        # Executed in Werkzeug's reload process; skip starting the scheduler here
        logging.info(f"[{pid}] Skipping scheduler start in Werkzeug reload process.")
