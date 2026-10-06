from marshmallow import Schema, ValidationError as MarshmallowValidationError, fields
from werkzeug.security import check_password_hash

from app.errors import UnauthorizedError, ValidationError
from app.models.user import User
from app.persistence.user_repository import UserRepository


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)


def authenticate_user(
    data: dict,
    users: UserRepository | None = None,
) -> User:
    try:
        payload = LoginSchema().load(data)
    except MarshmallowValidationError as error:
        raise ValidationError(_format_schema_errors(error.messages)) from error

    repository = users or UserRepository()
    user = repository.get_by_email(payload["email"].strip().lower())
    if user is None or not check_password_hash(user.password_hash, payload["password"]):
        raise UnauthorizedError("Invalid email or password")
    return user


def public_user(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "roles": user.roles(),
    }


def _format_schema_errors(messages) -> str:
    if isinstance(messages, dict):
        parts = []
        for field, errors in messages.items():
            text = "; ".join(errors) if isinstance(errors, list) else str(errors)
            parts.append(f"{field}: {text}")
        return "; ".join(parts)
    return str(messages)
