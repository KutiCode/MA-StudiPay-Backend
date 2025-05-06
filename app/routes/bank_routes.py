from flask import Blueprint, jsonify, request
from app.models import Bank, User
from app.extensions import db

# Create a Blueprint for bank-related API endpoints under the '/api' prefix
bank_bp = Blueprint("bank", __name__, url_prefix="/api")

@bank_bp.route("/all_secrets", methods=["GET"])
def get_all_bank_secrets():
    """
    Retrieve all banks along with their secret codes.

    Returns a JSON object containing a list of banks, each with:
      - bank_name: Name of the bank
      - bank_code: Unique identifier for the bank
      - secrets: List of secret code records, each with:
          - code: The secret code string
          - generated_at: Timestamp when the code was generated
    """
    # Query all Bank records from the database
    banks = Bank.query.all()
    result = []

    # Build the response list
    for bank in banks:
        result.append({
            "bank_name": bank.name,
            "bank_code": bank.bank_code,
            "secrets": [
                {
                    "code": secret.secret,
                    "generated_at": secret.generated_at
                }
                for secret in bank.secrets  # Access related BankSecret entries
            ]
        })

    # Return the compiled list of banks and their secrets
    return jsonify({"banks": result}), 200

@bank_bp.route("/add_balance", methods=["POST"])
def add_balance():
    """
    Increase a user's account balance.

    Expects JSON payload with:
      - matriculationNumber: User's unique matriculation ID (required)
      - amount: Amount to add to the balance (required, numeric)

    Returns the updated user record and new balance.
    """
    data = request.get_json()

    # Validate required input fields
    if not data or "matriculationNumber" not in data or "amount" not in data:
        return jsonify({"error": "matriculationNumber and amount are required"}), 400

    matriculationNumber = data["matriculationNumber"]
    amount = data["amount"]

    # Look up the user by matriculation number
    user = User.query.filter_by(matriculationNumber=matriculationNumber).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    try:
        # Add the specified amount to the user's balance
        user.balance += float(amount)
        db.session.commit()

        # Return success response with updated balance
        return jsonify({
            "message": "Balance updated successfully",
            "new_balance": user.balance,
            "user": user.as_dict()
        }), 200
    except Exception as e:
        # Roll back on error and return details
        db.session.rollback()
        return jsonify({"error": "Error updating balance", "details": str(e)}), 500

@bank_bp.route("/deduct_balance", methods=["POST"])
def deduct_balance():
    """
    Decrease a user's account balance.

    Expects JSON payload with:
      - matriculationNumber: User's unique matriculation ID (required)
      - amount: Amount to deduct from the balance (required, numeric)

    Checks that the user has sufficient funds before deduction.
    Returns the updated user record and new balance.
    """
    data = request.get_json()

    # Validate required input fields
    if not data or "matriculationNumber" not in data or "amount" not in data:
        return jsonify({"error": "matriculationNumber and amount are required"}), 400

    matriculationNumber = data["matriculationNumber"]
    amount = float(data["amount"])

    # Look up the user by matriculation number
    user = User.query.filter_by(matriculationNumber=matriculationNumber).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Ensure the user has enough balance to cover the deduction
    if user.balance < amount:
        return jsonify({"error": "Insufficient balance", "current_balance": user.balance}), 400

    try:
        # Subtract the specified amount from the user's balance
        user.balance -= amount
        db.session.commit()

        # Return success response with updated balance
        return jsonify({
            "message": "Amount deducted successfully",
            "new_balance": user.balance,
            "user": user.as_dict()
        }), 200
    except Exception as e:
        # Roll back on error and return details
        db.session.rollback()
        return jsonify({"error": "Error updating balance", "details": str(e)}), 500
