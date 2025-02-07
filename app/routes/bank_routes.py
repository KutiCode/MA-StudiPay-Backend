from flask import Blueprint, jsonify
from app.models import Bank

bank_bp = Blueprint("bank", __name__, url_prefix="/api")

@bank_bp.route("/all_secrets", methods=["GET"])
def get_all_bank_secrets():
    banks = Bank.query.all()
    result = []
    for bank in banks:
        result.append({
            "bank_name": bank.name,
            "bank_code": bank.bank_code,
            "secrets": [
                {
                    "code": secret.secret,
                    "generated_at": secret.generated_at
                }
                for secret in bank.secrets
            ]
        })
    return jsonify({"banks": result}), 200

