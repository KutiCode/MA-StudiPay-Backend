"""
Models module for the application.

This module defines the ORM models representing Users, Banks, and related entities.
It also provides utility functions for generating secret codes and timestamps.
"""

from datetime import datetime
import random
import string
from app.extensions import db

class User(db.Model):
    """
    Represents a user in the system, storing personal details, account information,
    transaction limits, and risk metrics.
    """
    __tablename__ = 'users'

    # Unique student matriculation number, serves as primary key
    matriculationNumber = db.Column(db.String(10), primary_key=True, unique=True, nullable=False)
    # User's family name
    lastName = db.Column(db.String(80), nullable=False)
    # User's given name
    firstName = db.Column(db.String(80), nullable=False)
    # Hashed password for authentication
    password = db.Column(db.String(256), nullable=False)
    # Unique bank account number associated with the user
    accountNumber = db.Column(db.String(20), unique=True, nullable=False)
    # Current account balance
    balance = db.Column(db.Float, default=0.0)
    # Optional secure PIN code for additional verification
    securePin = db.Column(db.String(6), nullable=True)
    # Foreign key linking to the Bank this user belongs to
    bank_code = db.Column(db.String(20), db.ForeignKey('banks.bank_code'), nullable=True)

    # New fields for transaction monitoring and risk management:
    # Count of transactions performed today
    daily_transaction_count = db.Column(db.Integer, default=0)
    # Timestamp of the last successful transaction
    last_transaction_date = db.Column(db.DateTime, nullable=True)
    # Number of transactions aborted due to high risk
    high_risk_aborted_count = db.Column(db.Integer, default=0)
    # Risk score of the last transaction attempt
    last_transaction_risk_value = db.Column(db.Integer, default=0)

    # Relationship to the Bank model for easy access
    bank = db.relationship("Bank", backref=db.backref("users", lazy=True))

    def as_dict(self):
        """
        Return a dictionary representation of the user, including related bank data.
        """
        data = {
            "matriculationNumber": self.matriculationNumber,
            "lastName": self.lastName,
            "firstName": self.firstName,
            "accountNumber": self.accountNumber,
            "balance": self.balance,
            "password": self.password,
            "securePin": self.securePin,
            "bank_code": self.bank_code,
            "dailyTransactionCount": self.daily_transaction_count,
            "lastTransactionDate": (
                self.last_transaction_date.isoformat()
                if self.last_transaction_date else None
            ),
            "highRiskAbortedCount": self.high_risk_aborted_count,
            "lastTransactionRiskValue": self.last_transaction_risk_value,
        }
        # Include nested bank data if available
        data["bank"] = self.bank.as_dict() if self.bank else None
        return data

    def __repr__(self):
        """
        Return a developer-friendly string representation of the user.
        """
        return f"<User {self.matriculationNumber} - {self.firstName} {self.lastName}>"


def generate_secret_code():
    """
    Generate a random 6-character alphanumeric secret code.
    """
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choices(characters, k=6))


def get_current_timestamp():
    """
    Return the current UTC timestamp as an ISO-formatted string.
    """
    return datetime.utcnow().isoformat()


class Bank(db.Model):
    """
    Represents a bank entity, holding its name, unique code, and associated secrets.
    """
    __tablename__ = 'banks'

    # Auto-incremented primary key
    id = db.Column(db.Integer, primary_key=True)
    # Human-readable bank name
    name = db.Column(db.String(100), nullable=False)
    # Unique bank code used to link secrets and users
    bank_code = db.Column(db.String(20), nullable=False, unique=True)
    # One-to-many relationship to BankSecret
    secrets = db.relationship(
        "BankSecret",
        backref="bank",
        cascade="all, delete-orphan",
        lazy=True
    )

    def as_dict(self):
        """
        Return a dictionary representation of the bank, including its secrets.
        """
        return {
            "id": self.id,
            "name": self.name,
            "bank_code": self.bank_code,
            "secrets": [secret.as_dict() for secret in self.secrets]
        }


class BankSecret(db.Model):
    """
    Stores a single secret code generated for a bank, with a timestamp.
    """
    __tablename__ = 'bank_secrets'

    # Auto-incremented primary key
    id = db.Column(db.Integer, primary_key=True)
    # Foreign key linking back to the Bank's code
    bank_code = db.Column(db.String(20), db.ForeignKey('banks.bank_code'), nullable=False)
    # The 6-character secret code
    secret = db.Column(db.String(6), nullable=False)
    # ISO-formatted timestamp when this code was generated
    generated_at = db.Column(db.String(30), nullable=False)

    def as_dict(self):
        """
        Return a dictionary representation of the bank secret.
        """
        return {
            "secret": self.secret,
            "generated_at": self.generated_at
        }


class ResetInfo(db.Model):
    """
    Tracks when system-wide reset operations were last performed.
    """
    __tablename__ = "reset_info"

    # Auto-incremented primary key
    id = db.Column(db.Integer, primary_key=True)
    # Timestamp of the last reset operation
    last_reset = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    def __repr__(self):
        """
        Return a developer-friendly string representation of the reset info.
        """
        return f"<ResetInfo last_reset={self.last_reset.isoformat()}>"
