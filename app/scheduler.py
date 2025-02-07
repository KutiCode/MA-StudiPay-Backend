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
    """
    Für jede Bank:
      - Lösche alle bestehenden Geheimzahlen.
      - Generiere 6 neue Geheimzahlen mit jeweils aktuellem Zeitstempel.
    """
    # Nutze den App-Kontext, um auf die Datenbank zuzugreifen.
    from app import create_app
    app = create_app()
    with app.app_context():
        banks = Bank.query.all()
        for bank in banks:
            # Bestehende Geheimzahlen löschen
            BankSecret.query.filter_by(bank_id=bank.id).delete()
            # 6 neue Geheimzahlen einfügen
            for _ in range(6):
                new_secret = BankSecret(
                    bank_id=bank.id,
                    secret=generate_secret_code(),
                    generated_at=get_current_timestamp()
                )
                db.session.add(new_secret)
        db.session.commit()
        print("Alle Bank-Geheimzahlen wurden neu generiert mit aktuellem Zeitstempel.")
