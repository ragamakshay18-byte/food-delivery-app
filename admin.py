"""
FoodieExpress - Admin routes
Admin can: approve/reject/suspend restaurants, view all users,
deactivate accounts, and see all orders platform-wide.
"""

from flask import Blueprint, request, jsonify
from extensions import db
from models import Restaurant, RestaurantStatus, User, UserRole
from auth import role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


# ---------- Restaurant approval workflow ----------

@admin_bp.route("/restaurants", methods=["GET"])
@role_required(UserRole.ADMIN)
def list_all_restaurants():
    status_filter = request.args.get("status")  # ?status=pending
    query = Restaurant.query
    if status_filter:
        try:
            query = query.filter_by(status=RestaurantStatus(status_filter))
        except ValueError:
            return jsonify({"error": "Invalid status filter"}), 400
    restaurants = query.order_by(Restaurant.created_at.desc()).all()
    return jsonify([r.to_dict() for r in restaurants]), 200


@admin_bp.route("/restaurants/<int:restaurant_id>/approve", methods=["POST"])
@role_required(UserRole.ADMIN)
def approve_restaurant(restaurant_id):
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    restaurant.status = RestaurantStatus.APPROVED
    restaurant.rejection_reason = None
    db.session.commit()
    return jsonify({"message": "Restaurant approved", "restaurant": restaurant.to_dict()}), 200


@admin_bp.route("/restaurants/<int:restaurant_id>/reject", methods=["POST"])
@role_required(UserRole.ADMIN)
def reject_restaurant(restaurant_id):
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    data = request.get_json() or {}
    restaurant.status = RestaurantStatus.REJECTED
    restaurant.rejection_reason = data.get("reason", "Did not meet platform guidelines")
    db.session.commit()
    return jsonify({"message": "Restaurant rejected", "restaurant": restaurant.to_dict()}), 200


@admin_bp.route("/restaurants/<int:restaurant_id>/suspend", methods=["POST"])
@role_required(UserRole.ADMIN)
def suspend_restaurant(restaurant_id):
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    restaurant.status = RestaurantStatus.SUSPENDED
    db.session.commit()
    return jsonify({"message": "Restaurant suspended", "restaurant": restaurant.to_dict()}), 200


@admin_bp.route("/restaurants/<int:restaurant_id>", methods=["DELETE"])
@role_required(UserRole.ADMIN)
def delete_restaurant(restaurant_id):
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    db.session.delete(restaurant)
    db.session.commit()
    return jsonify({"message": "Restaurant removed"}), 200


# ---------- User management ----------

@admin_bp.route("/users", methods=["GET"])
@role_required(UserRole.ADMIN)
def list_users():
    role_filter = request.args.get("role")
    query = User.query
    if role_filter:
        try:
            query = query.filter_by(role=UserRole(role_filter))
        except ValueError:
            return jsonify({"error": "Invalid role filter"}), 400
    users = query.order_by(User.created_at.desc()).all()
    return jsonify([u.to_dict() for u in users]), 200


@admin_bp.route("/users/<int:user_id>/deactivate", methods=["POST"])
@role_required(UserRole.ADMIN)
def deactivate_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = False
    db.session.commit()
    return jsonify({"message": "User deactivated", "user": user.to_dict()}), 200


@admin_bp.route("/users/<int:user_id>/reactivate", methods=["POST"])
@role_required(UserRole.ADMIN)
def reactivate_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = True
    db.session.commit()
    return jsonify({"message": "User reactivated", "user": user.to_dict()}), 200


# ---------- Orders (platform-wide) ----------

@admin_bp.route("/orders", methods=["GET"])
@role_required(UserRole.ADMIN)
def list_all_orders():
    from models import Order
    status_filter = request.args.get("status")
    query = Order.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    orders = query.order_by(Order.created_at.desc()).limit(200).all()
    return jsonify([o.to_dict() for o in orders]), 200


# ---------- Dashboard summary ----------

@admin_bp.route("/dashboard/summary", methods=["GET"])
@role_required(UserRole.ADMIN)
def dashboard_summary():
    from models import Order
    return jsonify({
        "total_restaurants": Restaurant.query.count(),
        "pending_restaurants": Restaurant.query.filter_by(status=RestaurantStatus.PENDING).count(),
        "approved_restaurants": Restaurant.query.filter_by(status=RestaurantStatus.APPROVED).count(),
        "total_users": User.query.filter_by(role=UserRole.CUSTOMER).count(),
        "total_owners": User.query.filter_by(role=UserRole.OWNER).count(),
        "total_orders": Order.query.count(),
    }), 200
