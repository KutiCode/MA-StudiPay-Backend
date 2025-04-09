# In app/scheduler.py
import os
from apscheduler.schedulers.background import BackgroundScheduler
from app.models import Bank, BankSecret, generate_secret_code, get_current_timestamp
from app.extensions import db
import logging

def regenerate_bank_secrets(app):
    pid = os.getpid()
    logging.info(f"[{pid}] Attempting to run regenerate_bank_secrets...")
    with app.app_context():
        try:
            banks = Bank.query.all()
            logging.info(f"[{pid}] Regenerating secrets for {len(banks)} banks...")
            for bank in banks:
                # Wähle eine passende Synchronisierungsstrategie
                BankSecret.query.filter_by(bank_code=bank.bank_code).delete(synchronize_session='fetch')
                # db.session.flush() # Optional, je nach Session-Verhalten

                for _ in range(6):
                    secret_code = generate_secret_code()
                    timestamp = get_current_timestamp()
                    new_secret = BankSecret(
                        bank_code=bank.bank_code,
                        secret=secret_code,
                        generated_at=timestamp
                    )
                    db.session.add(new_secret)

            db.session.commit()
            logging.info(f"[{pid}] Successfully regenerated bank secrets.")
        except Exception as e:
            db.session.rollback()
            logging.error(f"[{pid}] Error during secret regeneration: {e}", exc_info=True) # Logge den Stack Trace


def start_secret_regeneration_scheduler(app):
    pid = os.getpid()

    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        logging.info(f"[{pid}] Initializing scheduler...")

        scheduler = BackgroundScheduler(daemon=True)


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
            logging.info(f"[{pid}] Shutting down scheduler on exit signal.")
            if scheduler.running:
                 scheduler.shutdown()
        except Exception as e:
            logging.error(f"[{pid}] Failed to start scheduler: {e}", exc_info=True)
    else:
        # Wird im Reload-Prozess von Werkzeug ausgeführt
        logging.info(f"[{pid}] Skipping scheduler start in Werkzeug reload process.")