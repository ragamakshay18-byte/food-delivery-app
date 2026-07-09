"""
FoodieExpress - Role-based JWT auth
Extends your existing JWT setup with a role claim and decorators
for restricting routes to customer / owner / admin.
"""

from functools import wraps
from flask import request, jsonify, g
import jwt
import os
from datetime import datetime, timedelta
from models import User, UserRole

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "change-this-in-production")
ALGORITHM = "HS256"
TOKEN_EXPIRY_HOURS = 24


def generate_token(user: User) -> str:
    payload = {
        "user_id": user.id,
        "email": user.email,
        "role": user.role.value,
        "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str):
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def _get_token_from_header():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1]
    return None


def token_required(f):
    """Any logged-in user (customer, owner, or admin)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _get_token_from_header()
        if not token:
            return jsonify({"error": "Missing authentication token"}), 401
        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        g.current_user_id = payload["user_id"]
        g.current_user_role = payload["role"]
        return f(*args, **kwargs)
    return decorated


def role_required(*allowed_roles):
    """
    Restrict a route to one or more roles.
    Usage: @role_required(UserRole.ADMIN)
           @role_required(UserRole.ADMIN, UserRole.OWNER)
    """
    allowed_values = {r.value if isinstance(r, UserRole) else r for r in allowed_roles}

    def wrapper(f):
        @wraps(f)
        @token_required
        def decorated(*args, **kwargs):
            if g.current_user_role not in allowed_values:
                return jsonify({"error": "Forbidden: insufficient role"}), 403
            return f(*args, **kwargs)
        return decorated
    return wrapper


def owns_restaurant_or_admin(restaurant):
    """Helper: True if current user is the restaurant's owner or an admin."""
    if g.current_user_role == UserRole.ADMIN.value:
        return True
    return restaurant.owner_id == g.current_user_id
