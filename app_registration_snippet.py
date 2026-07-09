# Add this to your existing app.py, alongside your other blueprint registrations:

from routes.owner import owner_bp
from routes.admin import admin_bp

app.register_blueprint(owner_bp)
app.register_blueprint(admin_bp)

# Also update your signup endpoint to accept an optional "role" field
# (default to "customer" if not provided), e.g.:
#
# role_str = data.get("role", "customer")
# if role_str not in ("customer", "owner"):
#     role_str = "customer"  # admins are created manually/seeded, never via public signup
# user = User(..., role=UserRole(role_str))
#
# To create your first admin account, run a one-off script or Flask shell:
#   from models import User, UserRole
#   admin = User.query.filter_by(email="you@example.com").first()
#   admin.role = UserRole.ADMIN
#   db.session.commit()
