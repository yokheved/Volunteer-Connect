from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.queries.get_user_profile import GetUserProfile

users_bp = Blueprint("users", __name__, url_prefix="/api/users")


@users_bp.get("/me")
@jwt_required()
def me():
    profile = GetUserProfile().execute(int(get_jwt_identity()))
    return jsonify(profile), 200
