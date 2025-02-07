from app.extensions import db
import random
import string
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'

    matrikelnumber = db.Column(db.String(10), primary_key=True, unique=True, nullable=False)
    lastName = db.Column(db.String(80), nullable=False)
    firstName = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(256), nullable=False)  # Passwort-Hash (nicht im Klartext speichern!)
    accountNumber = db.Column(db.String(20), unique=True, nullable=False)
    balance = db.Column(db.Float, default=0.0)  # Standardmäßig 0.0
    securePin = db.Column(db.String(6), nullable=False)  # 6-stelliger Pin (verschlüsselt speichern)

    def as_dict(self):
        """Hilfsfunktion zur Umwandlung eines Objekts in ein Dictionary (z. B. für JSON-Responses)"""
        return {
            "matrikelnumber": self.matrikelnumber,
            "lastName": self.lastName,
            "firstName": self.firstName,
            "accountNumber": self.accountNumber,
            "balance": self.balance,
            "password": self.password,
            "securePin": self.securePin
        }

    def __repr__(self):
        return f"<User {self.matrikelnumber} - {self.firstName} {self.lastName}>"



def generate_secret_code():
    """Generiert einen zufälligen alphanumerischen Code der Länge 6."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def get_current_timestamp():
    """Gibt den aktuellen UTC-Zeitstempel im ISO-Format als String zurück."""
    return datetime.utcnow().isoformat()

class Bank(db.Model):
    __tablename__ = 'banks'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    bank_code = db.Column(db.String(20), nullable=False)
    # Beziehung zu den Geheimzahlen
    secrets = db.relationship("BankSecret", backref="bank", cascade="all, delete-orphan", lazy=True)

    def as_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "bank_code": self.bank_code,
            "secrets": [secret.as_dict() for secret in self.secrets]
        }

class BankSecret(db.Model):
    __tablename__ = 'bank_secrets'
    id = db.Column(db.Integer, primary_key=True)
    bank_id = db.Column(db.Integer, db.ForeignKey('banks.id'), nullable=False)
    secret = db.Column(db.String(6), nullable=False)
    generated_at = db.Column(db.String(30), nullable=False)  # Zeitstempel als String

    def as_dict(self):
        return {
            "secret": self.secret,
            "generated_at": self.generated_at
        }