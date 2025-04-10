from flask import Blueprint, request, jsonify
from app.models import User  # Stelle sicher, dass dein User-Modell die neuen Felder enthält
from app.extensions import db

risk_bp = Blueprint("risk", __name__, url_prefix="/api")

@risk_bp.route("/update_risk_params", methods=["POST"])
def update_risk_params():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Benutzer anhand der Matrikelnummer identifizieren
    matriculationNumber = data.get("matriculationNumber")
    if not matriculationNumber:
        return jsonify({"error": "matriculationNumber is required"}), 400

    user = User.query.filter_by(matriculationNumber=matriculationNumber).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Neue risko‑relevante Parameter aus dem Payload übernehmen (falls vorhanden)
    if "dailyTransactionCount" in data:
        user.daily_transaction_count = data["dailyTransactionCount"]
    if "lastTransactionDate" in data:
        user.last_transaction_date = data["lastTransactionDate"]
    if "highRiskAbortedCount" in data:
        user.high_risk_aborted_count = data["highRiskAbortedCount"]
    if "lastTransaktionRiskValue" in data:
        user.last_transaction_risk_value = data["lastTransaktionRiskValue"]

    try:
        db.session.commit()
        return jsonify({
            "status": "success",
            "message": "Risk parameters updated successfully.",
            "user": user.as_dict()  # falls du eine as_dict()-Methode implementiert hast
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Database error", "details": str(e)}), 500
