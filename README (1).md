# FoodieExpress — Admin & Restaurant Owner Module

Extends your existing FoodieExpress backend/frontend with role-based auth,
restaurant owner onboarding, and admin management.

## What's included

**Backend (Flask + SQLAlchemy)**
- `backend/models.py` — `UserRole` enum, `RestaurantStatus` enum, `Restaurant`, `MenuItem` models
- `backend/auth.py` — `role_required()` decorator for JWT-based role access control
- `backend/routes/owner.py` — restaurant registration, menu CRUD, order status updates
- `backend/routes/admin.py` — approve/reject/suspend restaurants, manage users, view all orders
- `backend/app_registration_snippet.py` — how to wire the new blueprints into your existing `app.py`

**Frontend**
- `frontend/owner/` — owner dashboard: register restaurant, manage menu, update order status
- `frontend/admin/` — admin dashboard: overview stats, restaurant approval queue, user management, orders

## Integration steps

1. Merge `models.py` into your existing models file (or import from it) — you already have `User`
   and `Order`; add the `role` column to `User` and a `restaurant_id` FK to `Order` if not present.
2. Copy `auth.py`'s `role_required` decorator alongside your existing JWT logic, or merge if you
   already generate tokens elsewhere — just make sure the JWT payload includes a `role` claim.
3. Register the two new blueprints per `app_registration_snippet.py`.
4. Run a migration (Flask-Migrate / `db.create_all()`) to add the new tables/columns.
5. Seed one admin user manually (see snippet) — admin accounts should never be created through
   public signup.
6. Drop the `frontend/owner` and `frontend/admin` folders into your static/templates directory and
   link to them after login based on the user's role (redirect owners to `/owner/owner-dashboard.html`,
   admins to `/admin/admin-dashboard.html`, customers to your existing home page).
7. Restyle the CSS to match your existing FoodieExpress design system (I used your brand orange
   `#fc8019` as a starting point, but your custom design tokens should take priority).

## Flow

- Owner signs up/logs in with role=owner → registers restaurant → status starts as `pending`
- Admin reviews pending restaurants in the Restaurants tab → approves or rejects with a reason
- Once approved, restaurant appears live; owner manages menu items and incoming orders
- Admin can suspend a misbehaving restaurant or deactivate a user account at any time
