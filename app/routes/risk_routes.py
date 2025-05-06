from flask import Blueprint, request, jsonify
from app.models import User  # Ensure that your User model includes the new risk-related fields
from app.extensions import db
from datetime import datetime

# Create a Blueprint for risk management endpoints under the '/api' prefix
risk_bp = Blueprint("risk", __name__, url_prefix="/api")

@risk_bp.route("/update_risk_params", methods=["POST"])
def update_risk_params():
    """
    Update risk-related parameters for a user.

    Expects JSON payload with:
      - matriculationNumber (str): Unique identifier for the user (required)
      - dailyTransactionCount (int): Number of transactions the user has made today (optional)
      - lastTransactionDate (ISO8601 str): Timestamp of the user's last transaction (optional)
      - highRiskAbortedCount (int): Count of aborted high-risk transactions (optional)
      - lastTransactionRiskValue (float): Risk score of the last transaction (optional)

    Returns a JSON response indicating success or error details.
    """
    data = request.get_json()
    # Validate that some data was provided
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Extract and validate matriculation number
    matriculationNumber = data.get("matriculationNumber")
    if not matriculationNumber:
        return jsonify({"error": "matriculationNumber is required"}), 400

    # Look up the user by matriculation number
    user = User.query.filter_by(matriculationNumber=matriculationNumber).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Update risk parameters if present in the payload
    if "dailyTransactionCount" in data:
        user.daily_transaction_count = data["dailyTransactionCount"]

    if "lastTransactionDate" in data:
        try:
            # Parse ISO8601-formatted date string into a datetime object
            user.last_transaction_date = datetime.fromisoformat(data["lastTransactionDate"])
        except ValueError:
            return jsonify({
                "error": "Invalid date format for lastTransactionDate",
                "details": f"Expected ISO format, got {data['lastTransactionDate']!r}"
            }), 400

    if "highRiskAbortedCount" in data:
        user.high_risk_aborted_count = data["highRiskAbortedCount"]

    if "lastTransactionRiskValue" in data:
        user.last_transaction_risk_value = data["lastTransactionRiskValue"]

    try:
        # Commit all changes to the database
        db.session.commit()
        return jsonify({
            "status": "success",
            "message": "Risk parameters updated successfully.",
            "user": user.as_dict()  # Requires an as_dict() method on the User model
        }), 200
    except Exception as e:
        # Roll back if any database error occurs
        db.session.rollback()
        return jsonify({"error": "Database error", "details": str(e)}), 500
