from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.commands.update_volunteer_availability import UpdateVolunteerAvailability
from app.commands.update_volunteer_categories import UpdateVolunteerCategories
from app.queries.get_volunteer_availability import GetVolunteerAvailability
from app.queries.get_volunteer_categories import GetVolunteerCategories
from app.queries.search_volunteers import SearchVolunteers

volunteers_bp = Blueprint("volunteers", __name__, url_prefix="/api/volunteers")


@volunteers_bp.route("", methods=["GET"], strict_slashes=False)
@jwt_required()
def search_volunteers():
    return jsonify(
        SearchVolunteers().execute(
            int(get_jwt_identity()),
            {
                "category": request.args.get("category"),
                "date": request.args.get("date"),
                "start_time": request.args.get("start_time"),
                "location": request.args.get("location"),
            },
        )
    ), 200


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


@volunteers_bp.get("/me/availability")
@jwt_required()
def get_my_availability():
    return jsonify(GetVolunteerAvailability().execute(int(get_jwt_identity()))), 200


@volunteers_bp.put("/me/availability")
@jwt_required()
def update_my_availability():
    return jsonify(
        UpdateVolunteerAvailability().execute(
            int(get_jwt_identity()),
            request.get_json(silent=True) or {},
        )
    ), 200
