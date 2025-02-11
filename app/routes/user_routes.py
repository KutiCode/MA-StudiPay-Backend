from flask import Blueprint, request, jsonify, current_app

from app.models import User
from app.extensions import db

user_bp = Blueprint("user", __name__, url_prefix="/api")

@user_bp.route("/register", methods=["POST"])
def register_user():
    """Registriert einen neuen Benutzer"""
    data = request.get_json()

    # Prüfen, ob alle Felder vorhanden sind
    required_fields = ["matrikelnumber", "lastName", "firstName", "password", "accountNumber", "securePin"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Fehlende Daten"}), 400

    # Prüfen, ob die Matrikelnummer bereits existiert
    if User.query.filter_by(matrikelnumber=data["matrikelnumber"]).first():
        return jsonify({"message": "Matrikelnummer existiert bereits"}), 400

    # Benutzer erstellen
    new_user = User(
        matrikelnumber=data["matrikelnumber"],
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
        return jsonify({"message": "Benutzer erfolgreich registriert"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Fehler beim Speichern der Daten", "details": str(e)}), 500

@user_bp.route("/user", methods=["GET"])
def get_user():
    """Abrufen eines Benutzers anhand der Matrikelnummer"""
    matrikelnumber = request.args.get("matrikelnumber")

    if not matrikelnumber:
        return jsonify({"error": "Matrikelnummer muss angegeben werden"}), 400

    user = User.query.filter_by(matrikelnumber=matrikelnumber).first()

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
    users = User.query.all()  # Alle Benutzer abrufen
    user_list = [user.as_dict() for user in users]  # Benutzer in JSON umwandeln

    return jsonify({"users": user_list}), 200


@user_bp.route("/add_balance", methods=["POST"])
def add_balance():
    """Erhöht das Guthaben eines Nutzers und gibt die neuen Daten zurück"""
    data = request.get_json()

    # Prüfen, ob alle benötigten Felder vorhanden sind
    if not data or "matrikelnumber" not in data or "amount" not in data:
        return jsonify({"error": "Matrikelnummer und Betrag müssen angegeben werden"}), 400

    matrikelnumber = data["matrikelnumber"]
    amount = data["amount"]

    # Prüfen, ob der Benutzer existiert
    user = User.query.filter_by(matrikelnumber=matrikelnumber).first()
    if not user:
        return jsonify({"error": "Benutzer nicht gefunden"}), 404

    # Guthaben aktualisieren
    try:
        user.balance += float(amount)
        db.session.commit()
        return jsonify({
            "message": "Guthaben erfolgreich aktualisiert",
            "new_balance": user.balance,
            "user": user.as_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Fehler beim Aktualisieren des Guthabens", "details": str(e)}), 500


@user_bp.route("/deduct_balance", methods=["POST"])
def deduct_balance():
    """Reduziert das Guthaben eines Nutzers und gibt die neuen Daten zurück"""
    data = request.get_json()

    # Prüfen, ob alle benötigten Felder vorhanden sind
    if not data or "matrikelnumber" not in data or "amount" not in data:
        return jsonify({"error": "Matrikelnummer und Betrag müssen angegeben werden"}), 400

    matrikelnumber = data["matrikelnumber"]
    amount = float(data["amount"])

    # Prüfen, ob der Benutzer existiert
    user = User.query.filter_by(matrikelnumber=matrikelnumber).first()
    if not user:
        return jsonify({"error": "Benutzer nicht gefunden"}), 404

    # Prüfen, ob genügend Guthaben vorhanden ist
    if user.balance < amount:
        return jsonify({"error": "Nicht genug Guthaben vorhanden", "current_balance": user.balance}), 400

    # Guthaben reduzieren
    try:
        user.balance -= amount
        db.session.commit()
        return jsonify({
            "message": "Betrag erfolgreich abgebucht",
            "new_balance": user.balance,
            "user": user.as_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Fehler beim Aktualisieren des Guthabens", "details": str(e)}), 500

@user_bp.route("/update_secure_pin", methods=["POST"])
def update_secure_pin():
    """
    Aktualisiert den securePin eines Benutzers.
    Erwartet JSON-Daten mit den Feldern:
    - matrikelnumber: Eindeutige Identifikation des Benutzers
    - newSecurePin: Der neue Secure Pin (idealerweise vor dem Speichern schon gehasht, falls gewünscht)
    """
    data = request.get_json()

    # Überprüfen, ob beide benötigten Felder vorhanden sind
    if not data or "matrikelnumber" not in data or "newSecurePin" not in data:
        return jsonify({"error": "Matrikelnummer und newSecurePin müssen angegeben werden"}), 400

    matrikelnumber = data["matrikelnumber"]
    new_secure_pin = data["newSecurePin"]

    # Benutzer anhand der Matrikelnummer suchen
    user = User.query.filter_by(matrikelnumber=matrikelnumber).first()
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

    if not data or "matrikelnumber" not in data:
        return jsonify({"error": "Matrikelnummer muss angegeben werden"}), 400

    # Nutzer anhand der Matrikelnummer suchen
    user = User.query.filter_by(matrikelnumber=data["matrikelnumber"]).first()
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
    if "bankCode" in data:
        user.bankCode = data["bankCode"]

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


