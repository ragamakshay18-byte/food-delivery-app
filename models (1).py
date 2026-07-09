"""
FoodieExpress - Extended Models
Adds role-based users, Restaurant, MenuItem, and restaurant approval workflow
on top of your existing SQLAlchemy setup.

Assumes: db = SQLAlchemy() is created in app.py / extensions.py and imported here.
"""

from datetime import datetime
from extensions import db
import enum


class UserRole(enum.Enum):
    CUSTOMER = "customer"
    OWNER = "owner"
    ADMIN = "admin"


class RestaurantStatus(enum.Enum):
    PENDING = "pending"      # submitted by owner, awaiting admin approval
    APPROVED = "approved"    # live on the platform
    REJECTED = "rejected"
    SUSPENDED = "suspended"  # admin can suspend an already-approved restaurant


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.Enum(UserRole), default=UserRole.CUSTOMER, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    restaurants = db.relationship("Restaurant", backref="owner", lazy=True)
    orders = db.relationship("Order", backref="customer", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "role": self.role.value,
            "is_active": self.is_active,
        }


class Restaurant(db.Model):
    __tablename__ = "restaurants"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    cuisine_type = db.Column(db.String(100))
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    image_url = db.Column(db.String(255))
    status = db.Column(db.Enum(RestaurantStatus), default=RestaurantStatus.PENDING, nullable=False)
    rejection_reason = db.Column(db.String(255))
    rating = db.Column(db.Float, default=0.0)
    is_open = db.Column(db.Boolean, default=True)  # owner toggles open/closed for orders
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    menu_items = db.relationship("MenuItem", backref="restaurant", lazy=True, cascade="all, delete-orphan")
    orders = db.relationship("Order", backref="restaurant", lazy=True)

    def to_dict(self, include_menu=False):
        data = {
            "id": self.id,
            "owner_id": self.owner_id,
            "name": self.name,
            "description": self.description,
            "cuisine_type": self.cuisine_type,
            "address": self.address,
            "city": self.city,
            "phone": self.phone,
            "image_url": self.image_url,
            "status": self.status.value,
            "rejection_reason": self.rejection_reason,
            "rating": self.rating,
            "is_open": self.is_open,
        }
        if include_menu:
            data["menu_items"] = [m.to_dict() for m in self.menu_items]
        return data


class MenuItem(db.Model):
    __tablename__ = "menu_items"

    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    category = db.Column(db.String(100))  # starters, main course, dessert...
    image_url = db.Column(db.String(255))
    is_veg = db.Column(db.Boolean, default=True)
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "restaurant_id": self.restaurant_id,
            "name": self.name,
            "description": self.description,
            "price": float(self.price),
            "category": self.category,
            "image_url": self.image_url,
            "is_veg": self.is_veg,
            "is_available": self.is_available,
        }


# NOTE: Order model assumed to already exist in your codebase with a
# restaurant_id FK. If not, add one so admin/owner can filter orders per
# restaurant, e.g.:
#
# class Order(db.Model):
#     __tablename__ = "orders"
#     id = db.Column(db.Integer, primary_key=True)
#     customer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
#     restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"), nullable=False)
#     status = db.Column(db.String(30), default="placed")  # placed, accepted, preparing,
#                                                            # out_for_delivery, delivered, cancelled
#     total_amount = db.Column(db.Numeric(10, 2), nullable=False)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
