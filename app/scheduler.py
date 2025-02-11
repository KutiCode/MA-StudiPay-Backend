from apscheduler.schedulers.background import BackgroundScheduler


def start_secret_regeneration_scheduler():
    scheduler = BackgroundScheduler()
    # Füge einen Job hinzu, der alle 30 Minuten die Geheimzahlen regeneriert
    scheduler.add_job(func=regenerate_bank_secrets, trigger='interval', minutes=30)
    scheduler.start()
    print("Secret-Regeneration-Scheduler gestartet.")
from app.models import Bank, BankSecret, generate_secret_code, get_current_timestamp
from app.extensions import db

def regenerate_bank_secrets():
    from app import create_app  # Hole dir deine Flask-App
    app = create_app()
    with app.app_context():
        banks = Bank.query.all()
        for bank in banks:
            # Statt BankSecret.query.filter_by(bank_id=bank.id) nutzen wir bankCode:
            BankSecret.query.filter_by(bank_code=bank.bankCode).delete()
            for _ in range(6):
                secret_code = generate_secret_code()
                timestamp = get_current_timestamp()
                # Hier wird bankCode verwendet, nicht bank_id
                new_secret = BankSecret(
                    bank_code=bank.bankCode,
                    secret=secret_code,
                    generated_at=timestamp
                )
                db.session.add(new_secret)
        db.session.commit()
        print("Alle Bank-Geheimzahlen wurden neu generiert.")
