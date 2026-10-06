from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt, jwt_required

from app.commands.register_user import RegisterUser
from app.extensions import jwt_blocklist
from app.services.auth_service import authenticate_user, public_user

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/register")
def register():
    user = RegisterUser().execute(request.get_json(silent=True) or {})
    return jsonify(public_user(user)), 201


@auth_bp.post("/login")
def login():
    user = authenticate_user(request.get_json(silent=True) or {})
    access_token = create_access_token(identity=str(user.id))
    return jsonify({"access_token": access_token, "user": public_user(user)}), 200


@auth_bp.post("/logout")
@jwt_required()
def logout():
    jwt_blocklist.add(get_jwt()["jti"])
    return jsonify({"message": "Logged out"}), 200
