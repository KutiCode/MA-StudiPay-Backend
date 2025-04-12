from flask import Blueprint, jsonify,request
from app.models import Bank
from app.models import User
from app.extensions import db
bank_bp = Blueprint("bank", __name__, url_prefix="/api")

@bank_bp.route("/all_secrets", methods=["GET"])
def get_all_bank_secrets():
    banks = Bank.query.all()
    result = []
    for bank in banks:
        result.append({
            "bank_name": bank.name,
            "bank_code": bank.bank_code,  # Korrekte Attributreferenz
            "secrets": [
                {
                    "code": secret.secret,
                    "generated_at": secret.generated_at
                }
                for secret in bank.secrets
            ]
        })
    return jsonify({"banks": result}), 200

@bank_bp.route("/add_balance", methods=["POST"])
def add_balance():
    """Erhöht das Guthaben eines Nutzers und gibt die neuen Daten zurück"""
    data = request.get_json()

    # Prüfen, ob alle benötigten Felder vorhanden sind
    if not data or "matriculationNumber" not in data or "amount" not in data:
        return jsonify({"error": "Matrikelnummer und Betrag müssen angegeben werden"}), 400

    matriculationNumber = data["matriculationNumber"]
    amount = data["amount"]

    # Prüfen, ob der Benutzer existiert
    user = User.query.filter_by(matriculationNumber=matriculationNumber).first()
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


@bank_bp.route("/deduct_balance", methods=["POST"])
def deduct_balance():
    """Reduziert das Guthaben eines Nutzers und gibt die neuen Daten zurück"""
    data = request.get_json()

    # Prüfen, ob alle benötigten Felder vorhanden sind
    if not data or "matriculationNumber" not in data or "amount" not in data:
        return jsonify({"error": "Matrikelnummer und Betrag müssen angegeben werden"}), 400

    matriculationNumber = data["matriculationNumber"]
    amount = float(data["amount"])

    # Prüfen, ob der Benutzer existiert
    user = User.query.filter_by(matriculationNumber=matriculationNumber).first()
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