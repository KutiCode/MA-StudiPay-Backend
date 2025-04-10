from flask import Blueprint, jsonify, request
from app.models import User
from app.extensions import db
from datetime import datetime
import dateutil.parser

auth_bp = Blueprint("auth", __name__, url_prefix="/api")

@auth_bp.route("/verify_transaction", methods=["POST"])
def verify_transaction_endpoint():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Keine Daten gesendet"}), 400

    matriculationNumber = data.get("matriculationNumber")
    amount = data.get("amount")
    if not matriculationNumber or amount is None:
        return jsonify({"error": "matriculationNumber und amount müssen angegeben werden"}), 400

    user = User.query.filter_by(matriculationNumber=matriculationNumber).first()
    if not user:
        return jsonify({"error": "Benutzer nicht gefunden"}), 400

    is_authorized, message = verify_transaction(user, float(amount))
    if is_authorized:
        return jsonify({"status": "success", "message": message}), 200
    else:
        return jsonify({"status": "failure", "message": message}), 400





def verify_transaction(user, amount):
    # 1. Überprüfe, ob der Nutzer genügend Guthaben hat
    if user.balance < amount:
        return False, "Nicht genügend Guthaben"

    # 2. Falls der tägliche Transaktionszähler unter 5 liegt, ist keine zusätzliche Prüfung nötig
    if user.daily_transaction_count < 5:
        return True, "Transaktion autorisiert"

    if user.last_transaction_risk_value > 80:
        if user.high_risk_aborted_count > 0:
            return False

    # 3. Wenn der Zähler 5 oder mehr beträgt, überprüfe den letzten Transaktionstag
    today = datetime.utcnow().date()
    if user.last_transaction_date:
        try:
            last_date = dateutil.parser.isoparse(user.last_transaction_date).date()
        except Exception as e:
            return False, "Ungültiges Datumsformat im letzten Transaktionsdatum"

        # Falls die letzte Transaktion heute stattfand, prüfen wir den high-risk Abbruchzähler
        if last_date == today:
            # Beispiel: Wenn mehr als 2 Transaktionen heute aufgrund hohen Risikos abgebrochen wurden, lehne ab
            if user.high_risk_aborted_count >= 2:
                return False, "Zu viele risikoreiche Abbrüche heute"
            else:
                return True, "Transaktion autorisiert, obwohl Maximalanzahl erreicht wurde"
        else:
            # Wenn heute noch keine Transaktion durchgeführt wurde, gibt es keine zusätzlichen Konsequenzen
            return True, "Transaktion autorisiert (neuer Tag)"
    else:
        # Falls kein Datum gespeichert ist, erlauben wir die Transaktion
        return True, "Transaktion autorisiert (kein vorheriger Transaktionstag vorhanden)"
