from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.commands.change_request_status import (
    ApproveVolunteerRequest,
    RejectVolunteerRequest,
)
from app.commands.create_volunteer_request import CreateVolunteerRequest
from app.queries.list_my_requests import ListMyRequests

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


@requests_bp.route("", methods=["GET"], strict_slashes=False)
@jwt_required()
def list_my_requests():
    return jsonify(
        ListMyRequests().execute(int(get_jwt_identity()), request.args.get("status"))
    )


@requests_bp.post("/<int:request_id>/approve")
@jwt_required()
def approve_request(request_id: int):
    return jsonify(ApproveVolunteerRequest().execute(int(get_jwt_identity()), request_id))


@requests_bp.post("/<int:request_id>/reject")
@jwt_required()
def reject_request(request_id: int):
    return jsonify(RejectVolunteerRequest().execute(int(get_jwt_identity()), request_id))
