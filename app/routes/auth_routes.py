from flask import Blueprint, jsonify, request
from app.models import User
from app.extensions import db
from datetime import datetime
import dateutil.parser

# Create a Blueprint for authentication and transaction verification endpoints
auth_bp = Blueprint("auth", __name__, url_prefix="/api")


@auth_bp.route("/verify_transaction", methods=["POST"])
def verify_transaction_endpoint():
    """
    Endpoint to authorize or reject a transaction request.

    Expects JSON payload with:
      - matriculationNumber: User's unique ID (required)
      - amount: Transaction amount to verify (required)

    Returns JSON indicating 'success' or 'failure' with a message.
    HTTP status codes:
      - 200 on successful authorization
      - 400 on transaction failure
      - 401 if no data provided
      - 402 if required fields missing
      - 404 if user not found
    """
    data = request.get_json()

    # Check that JSON data was sent
    if not data:
        return jsonify({"error": "No data provided"}), 401

    # Extract required fields from the payload
    matriculationNumber = data.get("matriculationNumber")
    amount = data.get("amount")
    if not matriculationNumber or amount is None:
        return jsonify({"error": "matriculationNumber and amount must be provided"}), 402

    # Look up user by matriculation number
    user = User.query.filter_by(matriculationNumber=matriculationNumber).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Delegate the core logic to verify_transaction()
    is_authorized, message = verify_transaction(user, float(amount))
    if is_authorized:
        return jsonify({"status": "success", "message": message}), 200
    else:
        return jsonify({"status": "failure", "message": message}), 400


def verify_transaction(user, amount):
    """
    Core logic to decide if a transaction should be allowed.

    Steps:
      1. Check user's balance is sufficient.
      2. If daily transaction count < 5, auto-approve.
      3. If last transaction risk value > 80 and there was a prior high-risk abort, reject.
      4. If daily count >= 5, enforce stricter checks:
         a. Parse last_transaction_date and compare with today.
         b. If a transaction occurred today, reject if too many high-risk aborts.
         c. Otherwise, allow since it's a new day or no prior date.

    Returns a tuple (is_authorized: bool, message: str).
    """
    # 1. Sufficient balance check
    if user.balance < amount:
        return False, "Insufficient funds"

    # 2. Quick path for users with fewer than 5 transactions today
    if user.daily_transaction_count < 5:
        return True, "Transaction authorized"

    # Additional risk check for heavy usage
    if user.last_transaction_risk_value > 80:
        if user.high_risk_aborted_count > 0:
            return False, "Risk too high!"

    # 3. Time-based daily enforcement
    today = datetime.utcnow().date()
    if user.last_transaction_date:
        try:
            # Attempt to parse stored date (ISO format)
            last_date = dateutil.parser.isoparse(user.last_transaction_date).date()
        except Exception:
            return False, "Invalid date format for last transaction"

        # If the last transaction was today, enforce high-risk abort limits
        if last_date == today:
            # Reject if >= 2 high-risk aborts occurred today
            if user.high_risk_aborted_count >= 2:
                return False, "Too many high-risk aborts today"
            else:
                return True, "Transaction authorized despite daily limit"
        else:
            # Reset enforcement for a new day
            return True, "Transaction authorized (new day)"
    else:
        # No previous transaction date recorded, allow transaction
        return True, "Transaction authorized (no prior transaction date)"
