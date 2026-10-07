"""
app.py
------
Main Flask application for FoodEase.
Features:
  - Dynamic home page with real-time cuisine filtering, search, sorting, and dietary filters
  - Restaurant detail & interactive menu page with category navigation & reviews
  - Session-backed shopping cart with AJAX endpoints and real-time badge updates
  - Checkout with delivery address, payment method selection, and order placement
  - Live order tracking timeline and customer order history
  - Auth system with 1-click Demo quick-fill accounts (Customer, Restaurant Owner, Admin)
  - Interactive Restaurant Owner and Admin analytics dashboards with status management
"""

import os
from functools import wraps
from flask import (
    Flask, render_template, redirect, url_for,
    request, session, flash, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash

import database as db

# ---------------------------------------------------------------------------
# App configuration
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "foodease-super-secret-key-2026")

# Initialise database on startup
with app.app_context():
    db.init_db()


# ---------------------------------------------------------------------------
# Context Processors (Injected into all Jinja2 templates)
# ---------------------------------------------------------------------------

@app.context_processor
def inject_global_data():
    """Make cart items count and current user info easily accessible anywhere."""
    cart = session.get("cart", {})
    cart_count = sum(item.get("quantity", 0) for item in cart.values())
    return {
        "cart_count": cart_count,
        "cuisines_list": ["All", "Indian", "Italian", "American", "Japanese", "Chinese", "Mexican", "Healthy", "Bakery", "South Indian", "Middle Eastern"]
    }


# ---------------------------------------------------------------------------
# Auth helpers / decorators
# ---------------------------------------------------------------------------

def login_required(f):
    """Redirect to login if the user is not in session."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated


def redirect_after_login():
    """Return the correct redirect response based on the user's role."""
    role = session.get("user_role")
    next_url = request.args.get("next")
    if next_url and next_url.startswith("/"):
        return redirect(next_url)

    if role == "restaurant_owner":
        return redirect(url_for("owner_dashboard"))
    if role == "admin":
        return redirect(url_for("admin_dashboard"))
    return redirect(url_for("index"))


# ---------------------------------------------------------------------------
# Public routes: Home, Search, Restaurant Detail & Menu
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """
    Home page – displays featured restaurants, cuisine filter pills,
    live search query, and sorting options.
    """
    cuisine = request.args.get("cuisine", "All")
    query = request.args.get("q", "").strip()
    sort_by = request.args.get("sort", "rating")
    veg_only = request.args.get("veg") == "1"

    restaurants = db.get_all_restaurants(
        cuisine=cuisine,
        query=query,
        sort_by=sort_by,
        veg_only=veg_only
    )

    all_cuisines = db.get_all_cuisines()

    return render_template(
        "index.html",
        restaurants=restaurants,
        cuisines=all_cuisines,
        active_cuisine=cuisine,
        search_query=query,
        active_sort=sort_by,
        veg_only=veg_only,
        total_count=len(restaurants)
    )


@app.route("/restaurant/<int:restaurant_id>", methods=["GET", "POST"])
def restaurant_detail(restaurant_id):
    """
    Restaurant detail page with category menu, dietary toggles,
    reviews list, and review submission form.
    """
    restaurant = db.get_restaurant_by_id(restaurant_id)
    if not restaurant:
        flash("Restaurant not found.", "danger")
        return redirect(url_for("index"))

    category = request.args.get("category", "All")
    veg_only = request.args.get("veg") == "1"

    # Handle customer review submission
    if request.method == "POST":
        if "user_id" not in session:
            flash("You must be logged in to leave a review.", "warning")
            return redirect(url_for("login", next=request.path))

        rating = int(request.form.get("rating", 5))
        comment = request.form.get("comment", "").strip()
        if comment:
            db.add_review(
                user_id=session["user_id"],
                restaurant_id=restaurant_id,
                user_name=session.get("user_name", "Anonymous"),
                rating=rating,
                comment=comment
            )
            flash("Thank you! Your review has been submitted.", "success")
            return redirect(url_for("restaurant_detail", restaurant_id=restaurant_id))

    menu_items = db.get_food_items_by_restaurant(restaurant_id, category=category, veg_only=veg_only)
    categories = db.get_restaurant_categories(restaurant_id)
    reviews = db.get_reviews_by_restaurant(restaurant_id)

    # Get current quantities in cart for this restaurant
    cart = session.get("cart", {})
    cart_quantities = {int(k): v["quantity"] for k, v in cart.items()}

    return render_template(
        "restaurant_detail.html",
        restaurant=restaurant,
        menu_items=menu_items,
        categories=categories,
        active_category=category,
        veg_only=veg_only,
        reviews=reviews,
        cart_quantities=cart_quantities
    )


# ---------------------------------------------------------------------------
# Cart & Checkout Routes (AJAX + Standard)
# ---------------------------------------------------------------------------

def _get_cart_details():
    """Helper to assemble full item models and calculate subtotal/delivery."""
    cart = session.get("cart", {})
    items = []
    subtotal = 0.0
    restaurant = None

    for item_id_str, cart_entry in list(cart.items()):
        food_item = db.get_food_item_by_id(int(item_id_str))
        if food_item:
            qty = cart_entry.get("quantity", 1)
            effective_price = food_item["discount_price"] if food_item["discount_price"] else food_item["price"]
            item_total = effective_price * qty
            subtotal += item_total
            items.append({
                "food_item": food_item,
                "quantity": qty,
                "effective_price": effective_price,
                "item_total": round(item_total, 2)
            })
            if not restaurant:
                restaurant = db.get_restaurant_by_id(food_item["restaurant_id"])

    # Free delivery for orders above ₹500
    delivery_fee = 0.0 if (subtotal >= 500 or subtotal == 0) else (restaurant["delivery_fee"] if restaurant else 35.0)
    tax = round(subtotal * 0.05, 2) if subtotal > 0 else 0.0
    total = round(subtotal + delivery_fee + tax, 2)

    return {
        "items": items,
        "subtotal": round(subtotal, 2),
        "delivery_fee": round(delivery_fee, 2),
        "tax": round(tax, 2),
        "total": total,
        "restaurant": restaurant
    }


@app.route("/cart")
def view_cart():
    """Display the full cart with summary and checkout action."""
    cart_data = _get_cart_details()
    return render_template("cart.html", **cart_data)


@app.route("/api/cart/add", methods=["POST"])
def api_cart_add():
    """AJAX endpoint to add or increment an item in the session cart."""
    data = request.get_json() or {}
    item_id = str(data.get("item_id"))

    if not item_id:
        return jsonify({"success": False, "error": "Item ID required"}), 400

    food_item = db.get_food_item_by_id(int(item_id))
    if not food_item:
        return jsonify({"success": False, "error": "Item not found"}), 404

    cart = session.get("cart", {})

    # Check if cart contains items from a different restaurant
    if cart:
        first_key = next(iter(cart))
        first_item = db.get_food_item_by_id(int(first_key))
        if first_item and first_item["restaurant_id"] != food_item["restaurant_id"]:
            # Prompt or handle restaurant mismatch
            if not data.get("clear_mismatch"):
                return jsonify({
                    "success": False,
                    "mismatch": True,
                    "error": f"Your cart contains items from a different restaurant. Would you like to clear it?"
                }), 409
            cart = {}

    if item_id in cart:
        cart[item_id]["quantity"] += 1
    else:
        cart[item_id] = {
            "id": food_item["id"],
            "restaurant_id": food_item["restaurant_id"],
            "quantity": 1
        }

    session["cart"] = cart
    session.modified = True

    cart_count = sum(item["quantity"] for item in cart.values())
    return jsonify({
        "success": True,
        "item_id": int(item_id),
        "quantity": cart[item_id]["quantity"],
        "cart_count": cart_count,
        "message": f"Added {food_item['name']} to cart!"
    })


@app.route("/api/cart/update", methods=["POST"])
def api_cart_update():
    """AJAX endpoint to increase, decrease, or remove an item."""
    data = request.get_json() or {}
    item_id = str(data.get("item_id"))
    action = data.get("action")  # 'increase', 'decrease', 'remove'

    cart = session.get("cart", {})
    if item_id in cart:
        if action == "increase":
            cart[item_id]["quantity"] += 1
        elif action == "decrease":
            cart[item_id]["quantity"] -= 1
            if cart[item_id]["quantity"] <= 0:
                del cart[item_id]
        elif action == "remove":
            del cart[item_id]

    session["cart"] = cart
    session.modified = True

    cart_data = _get_cart_details()
    cart_count = sum(item["quantity"] for item in cart.values())
    curr_qty = cart.get(item_id, {}).get("quantity", 0)

    return jsonify({
        "success": True,
        "item_id": int(item_id),
        "quantity": curr_qty,
        "cart_count": cart_count,
        "subtotal": cart_data["subtotal"],
        "delivery_fee": cart_data["delivery_fee"],
        "tax": cart_data["tax"],
        "total": cart_data["total"]
    })


@app.route("/api/cart/clear", methods=["POST"])
def api_cart_clear():
    """Clear all items in cart."""
    session["cart"] = {}
    session.modified = True
    return jsonify({"success": True, "cart_count": 0})


@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    """Checkout review and order placement."""
    cart_data = _get_cart_details()
    if not cart_data["items"]:
        flash("Your cart is currently empty.", "warning")
        return redirect(url_for("index"))

    user = db.get_user_by_id(session["user_id"])

    if request.method == "POST":
        delivery_address = request.form.get("delivery_address", "").strip()
        payment_method = request.form.get("payment_method", "Credit Card")
        instructions = request.form.get("special_instructions", "").strip()

        if not delivery_address:
            flash("Please provide a delivery address.", "danger")
            return render_template("checkout.html", user=user, **cart_data)

        # Create order in database
        order_id, order_num = db.create_order(
            user_id=session["user_id"],
            restaurant_id=cart_data["restaurant"]["id"],
            cart_items=cart_data["items"],
            delivery_address=delivery_address,
            payment_method=payment_method,
            special_instructions=instructions
        )

        # Clear cart
        session["cart"] = {}
        session.modified = True

        flash(f"Order #{order_num} placed successfully! Your delicious food is being prepared.", "success")
        return redirect(url_for("order_detail", order_id=order_id))

    return render_template("checkout.html", user=user, **cart_data)


@app.route("/order/<int:order_id>")
@login_required
def order_detail(order_id):
    """Live tracking and receipt for an order."""
    order, items = db.get_order_by_id(order_id)
    if not order:
        flash("Order not found.", "danger")
        return redirect(url_for("index"))

    # Only order owner or admin/restaurant owner can view
    if session.get("user_role") == "customer" and order["user_id"] != session.get("user_id"):
        flash("Unauthorized access to that order.", "danger")
        return redirect(url_for("index"))

    return render_template("order_detail.html", order=order, items=items)


@app.route("/orders")
@login_required
def orders():
    """Customer's past orders history."""
    user_orders = db.get_orders_by_user(session["user_id"])
    return render_template("orders.html", orders=user_orders)


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    """Show the registration form (GET) or process it (POST)."""
    if "user_id" in session:
        return redirect_after_login()

    if request.method == "POST":
        name     = request.form.get("name", "").strip()
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm_password", "")
        role     = request.form.get("role", "customer")
        phone    = request.form.get("phone", "").strip()
        address  = request.form.get("address", "").strip()

        errors = []
        if not name:
            errors.append("Full name is required.")
        if not email:
            errors.append("Email address is required.")
        if not password:
            errors.append("Password is required.")
        elif len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")

        if role not in ("customer", "restaurant_owner"):
            errors.append("Invalid role selected.")

        if errors:
            for msg in errors:
                flash(msg, "danger")
            return render_template("auth/register.html",
                                   form_name=name, form_email=email,
                                   form_role=role, form_phone=phone, form_address=address)

        hashed = generate_password_hash(password)
        success, error_msg = db.create_user(name, email, hashed, role, phone, address)

        if not success:
            flash(error_msg, "danger")
            return render_template("auth/register.html",
                                   form_name=name, form_email=email,
                                   form_role=role, form_phone=phone, form_address=address)

        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("auth/register.html",
                           form_name="", form_email="", form_role="customer", form_phone="", form_address="")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Show the login form (GET) or authenticate the user (POST)."""
    if "user_id" in session:
        return redirect_after_login()

    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Email and password are required.", "danger")
            return render_template("auth/login.html", form_email=email)

        user = db.get_user_by_email(email)

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html", form_email=email)

        # Preserve existing cart items across login
        cart = session.get("cart", {})
        session.clear()
        session["user_id"]   = user["id"]
        session["user_name"] = user["name"]
        session["user_role"] = user["role"]
        session["user_email"] = user["email"]
        session["user_avatar"] = user["avatar"] or ""
        session["cart"]      = cart

        flash(f"Welcome back, {user['name']}!", "success")
        return redirect_after_login()

    return render_template("auth/login.html", form_email="")


@app.route("/logout")
def logout():
    """Clear session and redirect to home."""
    session.clear()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for("index"))


# ---------------------------------------------------------------------------
# Dashboards (Restaurant Owner & Admin)
# ---------------------------------------------------------------------------

@app.route("/dashboard/owner")
@login_required
def owner_dashboard():
    """Interactive dashboard for restaurant owners with live metrics and orders."""
    if session.get("user_role") not in ("restaurant_owner", "admin"):
        flash("Access restricted to restaurant owners.", "danger")
        return redirect(url_for("index"))

    # For demonstration, owner manages restaurant 2 (Pizza Roma) or 1 (Spice Garden)
    rest_id = 2 if session.get("user_name") == "Chef Marco Bellini" else 1
    stats = db.get_owner_stats(restaurant_id=rest_id)
    return render_template("dashboard/owner.html", **stats)


@app.route("/dashboard/owner/order/<int:order_id>/status", methods=["POST"])
@login_required
def update_owner_order_status(order_id):
    """Allows restaurant owner to progress order status."""
    if session.get("user_role") not in ("restaurant_owner", "admin"):
        flash("Unauthorized action.", "danger")
        return redirect(url_for("index"))

    new_status = request.form.get("status")
    if new_status in ("confirmed", "preparing", "out_for_delivery", "delivered", "cancelled"):
        db.update_order_status(order_id, new_status)
        flash(f"Order #{order_id} status updated to {new_status.replace('_', ' ').title()}.", "success")

    return redirect(url_for("owner_dashboard"))


@app.route("/dashboard/admin")
@login_required
def admin_dashboard():
    """Executive admin dashboard with platform KPIs, top restaurants, and orders."""
    if session.get("user_role") != "admin":
        flash("Access restricted to platform administrators.", "danger")
        return redirect(url_for("index"))

    stats = db.get_admin_stats()
    restaurants = db.get_all_restaurants()
    return render_template("dashboard/admin.html", stats=stats, restaurants=restaurants)


# ---------------------------------------------------------------------------
# Run development server
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, port=5000)
