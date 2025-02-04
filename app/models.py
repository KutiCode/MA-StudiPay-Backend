from app.extensions import db

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
            "balance": self.balance
        }

    def __repr__(self):
        return f"<User {self.matrikelnumber} - {self.firstName} {self.lastName}>"
