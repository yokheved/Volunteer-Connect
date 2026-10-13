from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.commands.update_volunteer_categories import UpdateVolunteerCategories
from app.queries.get_volunteer_categories import GetVolunteerCategories

volunteers_bp = Blueprint("volunteers", __name__, url_prefix="/api/volunteers")


@volunteers_bp.get("/me/categories")
@jwt_required()
def get_my_categories():
    return jsonify(GetVolunteerCategories().execute(int(get_jwt_identity()))), 200


@volunteers_bp.put("/me/categories")
@jwt_required()
def update_my_categories():
    return jsonify(
        UpdateVolunteerCategories().execute(
            int(get_jwt_identity()),
            request.get_json(silent=True) or {},
        )
    ), 200
