from datetime import timedelta, datetime

from flask import Blueprint, request, jsonify, current_app

from app.models import User, ResetInfo
from app.extensions import db

# Create a Blueprint for user-related API endpoints under the '/api' prefix
user_bp = Blueprint("user", __name__, url_prefix="/api")

@user_bp.route("/register", methods=["POST"])
def register_user():
    """
    Register a new user with the provided details.

    Expects JSON with:
      - matriculationNumber: user's unique matriculation ID
      - lastName: user's last name
      - firstName: user's first name
      - password: user's password (should be hashed in a real app)
      - accountNumber: user's bank account number

    Returns a success message or error details.
    """
    data = request.get_json()

    # Ensure all required fields are present
    required_fields = ["matriculationNumber", "lastName", "firstName", "password", "accountNumber"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required data"}), 400

    # Check for duplicate matriculation numbers
    if User.query.filter_by(matriculationNumber=data["matriculationNumber"]).first():
        return jsonify({"message": "Matriculation number already exists"}), 400

    # Create new user record with initial balance 0.0
    new_user = User(
        matriculationNumber=data["matriculationNumber"],
        lastName=data["lastName"],
        firstName=data["firstName"],
        password=data["password"],
        accountNumber=data["accountNumber"],
        balance=0.0
    )

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "User successfully registered"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error saving data", "details": str(e)}), 500

@user_bp.route("/user", methods=["GET"])
def get_user():
    """
    Retrieve a user by their matriculation number.

    Query parameter:
      - matriculationNumber: user's matriculation ID

    Returns the user data if found.
    """
    matriculationNumber = request.args.get("matriculationNumber")

    if not matriculationNumber:
        return jsonify({"error": "Matriculation number must be provided"}), 400

    user = User.query.filter_by(matriculationNumber=matriculationNumber).first()
    if user:
        return jsonify({"exists": True, "user": user.as_dict()}), 200
    else:
        return jsonify({"exists": False, "message": "User not found"}), 404

@user_bp.route("/users", methods=["GET"])
def get_all_users():
    """
    Retrieve all users and reset daily transaction counters every 24 hours.

    Uses a singleton ResetInfo record (ID=1) to track the last reset time.
    If more than 24 hours have passed since last reset, zero out all users' daily transaction counts.

    Returns a list of all user records.
    """
    now = datetime.utcnow()

    # Fetch or create the global reset tracker
    existing = ResetInfo.query.get(1)
    if existing is None:
        # Initialize reset info on first call
        existing = ResetInfo(id=1, last_reset=now)
        db.session.add(existing)
    elif now - existing.last_reset >= timedelta(hours=24):
        # Zero out daily counters if 24 hours have elapsed
        User.query.update(
            {User.daily_transaction_count: 0},
            synchronize_session='fetch'
        )
        existing.last_reset = now

    db.session.commit()

    # Return all users as a JSON list
    users = User.query.all()
    return jsonify({"users": [u.as_dict() for u in users]}), 200

@user_bp.route("/update_secure_pin", methods=["POST"])
def update_secure_pin():
    """
    Update a user's secure PIN.

    Expects JSON with:
      - matriculationNumber: user's ID
      - newSecurePin: the updated secure PIN value

    Returns the updated user record.
    """
    data = request.get_json()

    # Validate input data
    if not data or "matriculationNumber" not in data or "newSecurePin" not in data:
        return jsonify({"error": "Matriculation number and newSecurePin are required"}), 400

    # Look up the user
    user = User.query.filter_by(matriculationNumber=data["matriculationNumber"]).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Set new secure PIN (consider hashing in production)
    user.securePin = data["newSecurePin"]

    try:
        db.session.commit()
        return jsonify({"message": "Secure PIN updated successfully", "user": user.as_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error updating secure PIN", "details": str(e)}), 500

@user_bp.route("/update_user", methods=["PUT"])
def update_user():
    """
    Update arbitrary fields on an existing user record.

    Expects JSON with:
      - matriculationNumber: user's ID (required)
      - Any other User model fields to update (e.g., lastName, firstName, password, accountNumber, balance, securePin, bank_code)

    Only provided fields will be changed.
    Returns the updated user record.
    """
    data = request.get_json()
    current_app.logger.info(f"Update User Payload: {data}")

    if not data or "matriculationNumber" not in data:
        return jsonify({"error": "Matriculation number must be provided"}), 400

    # Find the user by matriculation number
    user = User.query.filter_by(matriculationNumber=data["matriculationNumber"]).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Update only the fields present in the request
    for field in ["lastName", "firstName", "password", "accountNumber", "balance", "securePin", "bank_code"]:
        if field in data:
            setattr(user, field, data[field])

    try:
        db.session.commit()
        db.session.refresh(user)  # Refresh to ensure all changes are loaded
        current_app.logger.info(f"User updated: {user.as_dict()}")
        return jsonify({"message": "User updated successfully", "user": user.as_dict()}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error("Error updating user", exc_info=e)
        return jsonify({"error": "Error updating user", "details": str(e)}), 500
