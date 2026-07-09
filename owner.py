"""
FoodieExpress - Restaurant Owner routes
Lets a logged-in user with role=owner register a restaurant (goes to
'pending' until admin approves) and manage its menu.
"""

from flask import Blueprint, request, jsonify, g
from extensions import db
from models import Restaurant, MenuItem, RestaurantStatus, UserRole
from auth import role_required, owns_restaurant_or_admin

owner_bp = Blueprint("owner", __name__, url_prefix="/api/owner")


# ---------- Restaurant management ----------

@owner_bp.route("/restaurants", methods=["POST"])
@role_required(UserRole.OWNER)
def create_restaurant():
    data = request.get_json() or {}
    required = ["name", "address", "city"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    restaurant = Restaurant(
        owner_id=g.current_user_id,
        name=data["name"],
        description=data.get("description"),
        cuisine_type=data.get("cuisine_type"),
        address=data["address"],
        city=data["city"],
        phone=data.get("phone"),
        image_url=data.get("image_url"),
        status=RestaurantStatus.PENDING,
    )
    db.session.add(restaurant)
    db.session.commit()
    return jsonify({"message": "Restaurant submitted for approval", "restaurant": restaurant.to_dict()}), 201


@owner_bp.route("/restaurants", methods=["GET"])
@role_required(UserRole.OWNER)
def list_my_restaurants():
    restaurants = Restaurant.query.filter_by(owner_id=g.current_user_id).all()
    return jsonify([r.to_dict() for r in restaurants]), 200


@owner_bp.route("/restaurants/<int:restaurant_id>", methods=["PUT"])
@role_required(UserRole.OWNER)
def update_restaurant(restaurant_id):
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    if not owns_restaurant_or_admin(restaurant):
        return jsonify({"error": "Not your restaurant"}), 403

    data = request.get_json() or {}
    for field in ["name", "description", "cuisine_type", "address", "city", "phone", "image_url", "is_open"]:
        if field in data:
            setattr(restaurant, field, data[field])

    # Editing details of an approved restaurant re-queues it if it changed materially.
    # Keep it simple: owners can toggle is_open freely without re-approval.
    db.session.commit()
    return jsonify({"message": "Restaurant updated", "restaurant": restaurant.to_dict()}), 200


# ---------- Menu management ----------

@owner_bp.route("/restaurants/<int:restaurant_id>/menu", methods=["POST"])
@role_required(UserRole.OWNER)
def add_menu_item(restaurant_id):
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    if not owns_restaurant_or_admin(restaurant):
        return jsonify({"error": "Not your restaurant"}), 403

    data = request.get_json() or {}
    if not data.get("name") or data.get("price") is None:
        return jsonify({"error": "name and price are required"}), 400

    item = MenuItem(
        restaurant_id=restaurant.id,
        name=data["name"],
        description=data.get("description"),
        price=data["price"],
        category=data.get("category"),
        image_url=data.get("image_url"),
        is_veg=data.get("is_veg", True),
        is_available=data.get("is_available", True),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({"message": "Menu item added", "item": item.to_dict()}), 201


@owner_bp.route("/menu/<int:item_id>", methods=["PUT"])
@role_required(UserRole.OWNER)
def update_menu_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    restaurant = item.restaurant
    if not owns_restaurant_or_admin(restaurant):
        return jsonify({"error": "Not your restaurant"}), 403

    data = request.get_json() or {}
    for field in ["name", "description", "price", "category", "image_url", "is_veg", "is_available"]:
        if field in data:
            setattr(item, field, data[field])
    db.session.commit()
    return jsonify({"message": "Menu item updated", "item": item.to_dict()}), 200


@owner_bp.route("/menu/<int:item_id>", methods=["DELETE"])
@role_required(UserRole.OWNER)
def delete_menu_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    restaurant = item.restaurant
    if not owns_restaurant_or_admin(restaurant):
        return jsonify({"error": "Not your restaurant"}), 403

    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Menu item deleted"}), 200


# ---------- Orders for owner's restaurants ----------

@owner_bp.route("/restaurants/<int:restaurant_id>/orders", methods=["GET"])
@role_required(UserRole.OWNER)
def restaurant_orders(restaurant_id):
    from models import Order  # local import: Order lives in your existing models module
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    if not owns_restaurant_or_admin(restaurant):
        return jsonify({"error": "Not your restaurant"}), 403

    orders = Order.query.filter_by(restaurant_id=restaurant_id).order_by(Order.created_at.desc()).all()
    return jsonify([o.to_dict() for o in orders]), 200


@owner_bp.route("/orders/<int:order_id>/status", methods=["PUT"])
@role_required(UserRole.OWNER)
def update_order_status(order_id):
    from models import Order
    order = Order.query.get_or_404(order_id)
    restaurant = order.restaurant
    if not owns_restaurant_or_admin(restaurant):
        return jsonify({"error": "Not your restaurant"}), 403

    data = request.get_json() or {}
    new_status = data.get("status")
    valid_statuses = {"accepted", "preparing", "out_for_delivery", "delivered", "cancelled"}
    if new_status not in valid_statuses:
        return jsonify({"error": f"status must be one of {valid_statuses}"}), 400

    order.status = new_status
    db.session.commit()
    return jsonify({"message": "Order status updated", "order": order.to_dict()}), 200
