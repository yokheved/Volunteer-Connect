from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.commands.create_volunteer_request import CreateVolunteerRequest

requests_bp = Blueprint("requests", __name__, url_prefix="/api/requests")


@requests_bp.route("", methods=["POST"], strict_slashes=False)
@jwt_required()
def create_request():
    return jsonify(
        CreateVolunteerRequest().execute(
            int(get_jwt_identity()),
            request.get_json(silent=True) or {},
        )
    ), 201
