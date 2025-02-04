from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
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

    # Hashing von Passwort und PIN
    hashed_password = generate_password_hash(data["password"])
    hashed_pin = generate_password_hash(data["securePin"])

    # Benutzer erstellen
    new_user = User(
        matrikelnumber=data["matrikelnumber"],
        lastName=data["lastName"],
        firstName=data["firstName"],
        password=hashed_password,
        accountNumber=data["accountNumber"],
        balance=0.0,
        securePin=hashed_pin
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
