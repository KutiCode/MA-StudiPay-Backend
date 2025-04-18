from datetime import timedelta, datetime

from flask import Blueprint, request, jsonify, current_app

from app.models import User, ResetInfo
from app.extensions import db

user_bp = Blueprint("user", __name__, url_prefix="/api")

@user_bp.route("/register", methods=["POST"])
def register_user():
    """Registriert einen neuen Benutzer"""
    data = request.get_json()

    # Prüfen, ob alle Felder vorhanden sind
    required_fields = ["matriculationNumber", "lastName", "firstName", "password", "accountNumber", "securePin"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Fehlende Daten"}), 404

    # Prüfen, ob die Matrikelnummer bereits existiert
    if User.query.filter_by(matriculationNumber=data["matriculationNumber"]).first():
        return jsonify({"message": "Matrikelnummer existiert bereits"}), 400

    # Benutzer erstellen
    new_user = User(
        matriculationNumber=data["matriculationNumber"],
        lastName=data["lastName"],
        firstName=data["firstName"],
        password=data["password"],
        accountNumber=data["accountNumber"],
        balance=0.0,
        securePin=data["securePin"]
    )

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "Benutzer erfolgreich registriert"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Fehler beim Speichern der Daten", "details": str(e)}), 500

@user_bp.route("/user", methods=["GET"])
def get_user():
    """Abrufen eines Benutzers anhand der Matrikelnummer"""
    matriculationNumber = request.args.get("matriculationNumber")

    if not matriculationNumber:
        return jsonify({"error": "Matrikelnummer muss angegeben werden"}), 400

    user = User.query.filter_by(matriculationNumber=matriculationNumber).first()

    if user:
        return jsonify({
            "exists": True,
            "user": user.as_dict()
        }), 200
    else:
        return jsonify({"exists": False, "message": "Benutzer nicht gefunden"}), 404


@user_bp.route("/users", methods=["GET"])
def get_all_users():
    """Gibt alle Benutzer in der Datenbank zurück"""

    # --- Reset‑Logik ---
    reset = ResetInfo.query.get(1)
    now = datetime.utcnow()

    # Falls noch kein Eintrag existiert, legen wir ihn an
    if not reset:
        reset = ResetInfo(id=1, last_reset=now)
        db.session.add(reset)
        db.session.commit()
    # Wenn seit der letzten Rücksetzung 24h rum sind, Counter zurücksetzen
    elif now - reset.last_reset >= timedelta(hours=24):
        # Massen‑Update aller Nutzer
        User.query.update({User.daily_transaction_count: 0})
        # Reset‑Zeit auf jetzt setzen
        reset.last_reset = now
        db.session.commit()

    users = User.query.all()  # Alle Benutzer abrufen
    user_list = [user.as_dict() for user in users]  # Benutzer in JSON umwandeln

    return jsonify({"users": user_list}), 200


@user_bp.route("/update_secure_pin", methods=["POST"])
def update_secure_pin():
    """
    Aktualisiert den securePin eines Benutzers.
    Erwartet JSON-Daten mit den Feldern:
    - matriculationNumber: Eindeutige Identifikation des Benutzers
    - newSecurePin: Der neue Secure Pin (idealerweise vor dem Speichern schon gehasht, falls gewünscht)
    """
    data = request.get_json()

    # Überprüfen, ob beide benötigten Felder vorhanden sind
    if not data or "matriculationNumber" not in data or "newSecurePin" not in data:
        return jsonify({"error": "Matrikelnummer und newSecurePin müssen angegeben werden"}), 400

    matriculationNumber = data["matriculationNumber"]
    new_secure_pin = data["newSecurePin"]

    # Benutzer anhand der Matrikelnummer suchen
    user = User.query.filter_by(matriculationNumber=matriculationNumber).first()
    if not user:
        return jsonify({"error": "Benutzer nicht gefunden"}), 404

    # Secure Pin aktualisieren
    user.securePin = new_secure_pin  # Optional: hier kannst du den Pin auch vor dem Speichern hashen

    try:
        db.session.commit()
        return jsonify({
            "message": "Secure Pin erfolgreich aktualisiert",
            "user": user.as_dict()  # Hier erhältst du den aktualisierten Datensatz
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Fehler beim Aktualisieren des Secure Pin",
            "details": str(e)
        }), 500

@user_bp.route("/update_user", methods=["PUT"])
def update_user():
    data = request.get_json()
    current_app.logger.info(f"Update User Payload: {data}")
    if not data or "matriculationNumber" not in data:
        return jsonify({"error": "Matrikelnummer muss angegeben werden"}), 400

    # Nutzer anhand der Matrikelnummer suchen
    user = User.query.filter_by(matriculationNumber=data["matriculationNumber"]).first()
    if not user:
        return jsonify({"error": "Benutzer nicht gefunden"}), 404

    # Aktualisiere nur die Felder, die im Request vorhanden sind
    if "lastName" in data:
        user.lastName = data["lastName"]
    if "firstName" in data:
        user.firstName = data["firstName"]
    if "password" in data:
        user.password = data["password"]
    if "accountNumber" in data:
        user.accountNumber = data["accountNumber"]
    if "balance" in data:
        user.balance = data["balance"]
    if "securePin" in data:
        user.securePin = data["securePin"]
    if "bank_code" in data:
        user.bank_code = data["bank_code"]

    try:
        db.session.commit()
        # Optional: Lade den Nutzer neu, um sicherzugehen, dass alle Änderungen übernommen wurden
        db.session.refresh(user)
        current_app.logger.info(f"Benutzer aktualisiert: {user.as_dict()}")
        return jsonify({
            "message": "Benutzer erfolgreich aktualisiert",
            "user": user.as_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error("Fehler beim Aktualisieren des Benutzers", exc_info=e)
        return jsonify({
            "error": "Fehler beim Aktualisieren des Benutzers",
            "details": str(e)
        }), 500


