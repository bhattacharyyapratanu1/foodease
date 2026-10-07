"""
database.py
-----------
Comprehensive SQLite database layer for FoodEase.
Features:
  - Robust schema with users, restaurants, food_items, orders, order_items, reviews
  - Rich realistic seed data (10 diverse restaurants, 65+ curated food items with HD photography, reviews, sample orders)
  - Pre-seeded demo user accounts (Customer, Restaurant Owner, Admin)
  - Query helpers for search, live cuisine/dietary filtering, sorting, cart/checkout, orders, and dashboard analytics
"""

import sqlite3
import os
import json
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

# Path to the SQLite database file
DB_PATH = os.path.join(os.path.dirname(__file__), "foodease.db")


# ---------------------------------------------------------------------------
# Connection helper
# ---------------------------------------------------------------------------

def get_connection():
    """
    Open and return a new SQLite connection with dict-like row access
    and foreign key constraints enabled.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ---------------------------------------------------------------------------
# Database Schema
# ---------------------------------------------------------------------------

_CREATE_TABLES_SQL = """
-- 1. users
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    email         TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    role          TEXT    NOT NULL DEFAULT 'customer', -- 'customer' | 'restaurant_owner' | 'admin'
    phone         TEXT,
    address       TEXT,
    avatar        TEXT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. restaurants
CREATE TABLE IF NOT EXISTS restaurants (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    cuisine       TEXT    NOT NULL,
    description   TEXT,
    address       TEXT,
    phone         TEXT,
    rating        REAL    NOT NULL DEFAULT 4.5,
    review_count  INTEGER NOT NULL DEFAULT 120,
    delivery_time TEXT    NOT NULL DEFAULT '25-35 min',
    delivery_fee  REAL    NOT NULL DEFAULT 40.0,
    min_order     REAL    NOT NULL DEFAULT 150.0,
    price_level   TEXT    NOT NULL DEFAULT '$$',
    image         TEXT    NOT NULL,
    banner_image  TEXT,
    is_featured   INTEGER NOT NULL DEFAULT 1,
    is_active     INTEGER NOT NULL DEFAULT 1,
    tags          TEXT,
    opening_hours TEXT    DEFAULT '10:00 AM - 11:00 PM',
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. food_items
CREATE TABLE IF NOT EXISTS food_items (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant_id  INTEGER NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    name           TEXT    NOT NULL,
    description    TEXT,
    price          REAL    NOT NULL,
    discount_price REAL,
    category       TEXT    NOT NULL,
    is_veg         INTEGER NOT NULL DEFAULT 1, -- 1 for veg, 0 for non-veg
    is_available   INTEGER NOT NULL DEFAULT 1,
    image          TEXT,
    badge          TEXT, -- 'Bestseller', 'Chef Special', 'Must Try', etc.
    calories       INTEGER,
    rating         REAL    DEFAULT 4.8,
    order_count    INTEGER DEFAULT 50,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. orders
CREATE TABLE IF NOT EXISTS orders (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number         TEXT    NOT NULL UNIQUE,
    user_id              INTEGER REFERENCES users(id) ON DELETE SET NULL,
    restaurant_id        INTEGER NOT NULL REFERENCES restaurants(id),
    total_amount         REAL    NOT NULL,
    subtotal             REAL    NOT NULL,
    delivery_fee         REAL    NOT NULL DEFAULT 0.0,
    tax                  REAL    NOT NULL DEFAULT 0.0,
    discount             REAL    NOT NULL DEFAULT 0.0,
    status               TEXT    NOT NULL DEFAULT 'pending', -- 'pending','confirmed','preparing','out_for_delivery','delivered','cancelled'
    payment_method       TEXT    NOT NULL DEFAULT 'Credit Card',
    delivery_address     TEXT,
    special_instructions TEXT,
    created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. order_items
CREATE TABLE IF NOT EXISTS order_items (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id       INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    food_item_id   INTEGER REFERENCES food_items(id) ON DELETE SET NULL,
    food_item_name TEXT    NOT NULL,
    quantity       INTEGER NOT NULL DEFAULT 1,
    unit_price     REAL    NOT NULL,
    total_price    REAL    NOT NULL
);

-- 6. reviews
CREATE TABLE IF NOT EXISTS reviews (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER REFERENCES users(id) ON DELETE SET NULL,
    restaurant_id INTEGER NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    user_name     TEXT    NOT NULL,
    rating        INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
    comment       TEXT    NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


# ---------------------------------------------------------------------------
# Seed Data: Users, Restaurants, Food Items, Reviews & Orders
# ---------------------------------------------------------------------------

_DEFAULT_USERS = [
    {
        "name": "Aarav Patel",
        "email": "customer@foodease.com",
        "password": "password123",
        "role": "customer",
        "phone": "+91 98765 00001",
        "address": "402, Sunshine Heights, Indiranagar, Bengaluru",
        "avatar": "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=150&q=80",
    },
    {
        "name": "Chef Marco Bellini",
        "email": "owner@foodease.com",
        "password": "password123",
        "role": "restaurant_owner",
        "phone": "+91 98765 00002",
        "address": "Kitchen 1, Pizza Roma HQ, Lavelle Road, Bengaluru",
        "avatar": "https://images.unsplash.com/photo-1577219491135-ce391730fb2c?auto=format&fit=crop&w=150&q=80",
    },
    {
        "name": "FoodEase Admin",
        "email": "admin@foodease.com",
        "password": "password123",
        "role": "admin",
        "phone": "+91 98765 00003",
        "address": "FoodEase Headquarters, Koramangala Tech Park, Bengaluru",
        "avatar": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?auto=format&fit=crop&w=150&q=80",
    },
]

_RESTAURANTS_SEED = [
    {
        "name": "Spice Garden",
        "cuisine": "Indian",
        "description": "Authentic North Indian culinary heritage with hand-ground spices, clay-tandoor delicacies, and slow-simmered royal curries.",
        "address": "12 MG Road, Indiranagar, Bengaluru",
        "phone": "+91 98765 11111",
        "rating": 4.8,
        "review_count": 348,
        "delivery_time": "30-40 min",
        "delivery_fee": 35.0,
        "min_order": 200.0,
        "price_level": "$$",
        "image": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?auto=format&fit=crop&w=800&q=80",
        "banner_image": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1200&q=80",
        "is_featured": 1,
        "tags": "Curry, Tandoori, Biryani, Mughlai, North Indian",
        "opening_hours": "11:00 AM - 11:30 PM",
    },
    {
        "name": "Pizza Roma",
        "cuisine": "Italian",
        "description": "Artisanal wood-fired sourdough pizzas crafted with authentic San Marzano tomatoes, fior di latte mozzarella, and hand-rolled pasta.",
        "address": "7 Lavelle Road, Shanthala Nagar, Bengaluru",
        "phone": "+91 98765 22222",
        "rating": 4.9,
        "review_count": 512,
        "delivery_time": "25-35 min",
        "delivery_fee": 40.0,
        "min_order": 250.0,
        "price_level": "$$$",
        "image": "https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=800&q=80",
        "banner_image": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=1200&q=80",
        "is_featured": 1,
        "tags": "Wood-Fired, Pizza, Gourmet Pasta, Tiramisu, Italian",
        "opening_hours": "12:00 PM - 11:00 PM",
    },
    {
        "name": "The Burger Beast",
        "cuisine": "American",
        "description": "Award-winning smash burgers made with prime aged patties, melted artisanal cheeses, brioche buns, and house-made truffle dipping sauces.",
        "address": "34 Brigade Road, Ashok Nagar, Bengaluru",
        "phone": "+91 98765 33333",
        "rating": 4.7,
        "review_count": 420,
        "delivery_time": "20-30 min",
        "delivery_fee": 30.0,
        "min_order": 150.0,
        "price_level": "$$",
        "image": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=800&q=80",
        "banner_image": "https://images.unsplash.com/photo-1550547660-d9450f859349?auto=format&fit=crop&w=1200&q=80",
        "is_featured": 1,
        "tags": "Smash Burgers, Truffle Fries, Shakes, Crispy Chicken",
        "opening_hours": "11:30 AM - 1:00 AM",
    },
    {
        "name": "Sakura Sushi & Ramen",
        "cuisine": "Japanese",
        "description": "Authentic Japanese dining featuring sashimi-grade Norwegian salmon, hand-crafted nigiri, crunchy tempura, and 18-hour rich tonkotsu ramen broth.",
        "address": "88 100 Feet Road, Indiranagar, Bengaluru",
        "phone": "+91 98765 44444",
        "rating": 4.9,
        "review_count": 290,
        "delivery_time": "30-45 min",
        "delivery_fee": 45.0,
        "min_order": 300.0,
        "price_level": "$$$",
        "image": "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?auto=format&fit=crop&w=800&q=80",
        "banner_image": "https://images.unsplash.com/photo-1617196034796-73dfa7b1fd56?auto=format&fit=crop&w=1200&q=80",
        "is_featured": 1,
        "tags": "Sushi, Tonkotsu Ramen, Sashimi, Gyoza, Japanese",
        "opening_hours": "12:30 PM - 10:30 PM",
    },
    {
        "name": "Golden Dragon Wok",
        "cuisine": "Chinese",
        "description": "High-flame wok-tossed Cantonese and Szechuan specialities, crispy honey glazed poultry, and freshly steamed dim sum baskets.",
        "address": "5 Koramangala 5th Block, Bengaluru",
        "phone": "+91 98765 55555",
        "rating": 4.6,
        "review_count": 380,
        "delivery_time": "25-35 min",
        "delivery_fee": 30.0,
        "min_order": 180.0,
        "price_level": "$$",
        "image": "https://images.unsplash.com/photo-1585032226651-759b368d7246?auto=format&fit=crop&w=800&q=80",
        "banner_image": "https://images.unsplash.com/photo-1563245372-f21724e3856d?auto=format&fit=crop&w=1200&q=80",
        "is_featured": 1,
        "tags": "Dim Sum, Hakka Noodles, Manchurian, Szechuan, Wok",
        "opening_hours": "12:00 PM - 11:30 PM",
    },
    {
        "name": "Taco Fuego",
        "cuisine": "Mexican",
        "description": "Bold Mexican street food featuring slow-cooked barbacoa, crispy carnitas, handmade corn tortillas, fresh guacamole, and loaded churros.",
        "address": "19 Church Street, Central Bengaluru",
        "phone": "+91 98765 66666",
        "rating": 4.7,
        "review_count": 275,
        "delivery_time": "20-30 min",
        "delivery_fee": 30.0,
        "min_order": 160.0,
        "price_level": "$$",
        "image": "https://images.unsplash.com/photo-1565299585323-38d6b0865b47?auto=format&fit=crop&w=800&q=80",
        "banner_image": "https://images.unsplash.com/photo-1626700051175-6818013e1d4f?auto=format&fit=crop&w=1200&q=80",
        "is_featured": 1,
        "tags": "Tacos, Burritos, Quesadillas, Nachos, Guacamole",
        "opening_hours": "11:00 AM - 11:00 PM",
    },
    {
        "name": "Green Bowl Co.",
        "cuisine": "Healthy",
        "description": "Vibrant superfood bowls, cold-pressed elixirs, organic avocado toast, and protein-packed Mediterranean salad creations.",
        "address": "45 Richmond Road, Bengaluru",
        "phone": "+91 98765 77777",
        "rating": 4.8,
        "review_count": 310,
        "delivery_time": "20-30 min",
        "delivery_fee": 25.0,
        "min_order": 180.0,
        "price_level": "$$",
        "image": "https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=800&q=80",
        "banner_image": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=1200&q=80",
        "is_featured": 1,
        "tags": "Salads, Keto, Vegan, Smoothie Bowls, Organic, Healthy",
        "opening_hours": "8:30 AM - 10:00 PM",
    },
    {
        "name": "Cafe Lumière & Bakery",
        "cuisine": "Bakery",
        "description": "French artisanal patisserie showcasing flaky buttery croissants, sourdough tartines, single-origin espresso, and delicate macaron boxes.",
        "address": "15 Cunningham Road, Vasanth Nagar, Bengaluru",
        "phone": "+91 98765 88888",
        "rating": 4.9,
        "review_count": 460,
        "delivery_time": "15-25 min",
        "delivery_fee": 25.0,
        "min_order": 140.0,
        "price_level": "$$",
        "image": "https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&w=800&q=80",
        "banner_image": "https://images.unsplash.com/photo-1555507036-ab1f4038808a?auto=format&fit=crop&w=1200&q=80",
        "is_featured": 1,
        "tags": "Croissant, Macarons, Specialty Coffee, Desserts, French",
        "opening_hours": "8:00 AM - 9:30 PM",
    },
    {
        "name": "Dakshin Rasoi",
        "cuisine": "South Indian",
        "description": "Crispy golden ghee roast dosas, fluffy steamed idlis, spicy Chettinad curries, and aromatic Kumbakonam degree filter coffee.",
        "address": "22 Malleshwaram 7th Cross, Bengaluru",
        "phone": "+91 98765 99999",
        "rating": 4.8,
        "review_count": 620,
        "delivery_time": "20-30 min",
        "delivery_fee": 20.0,
        "min_order": 120.0,
        "price_level": "$",
        "image": "https://images.unsplash.com/photo-1668236543090-82eba5ee5976?auto=format&fit=crop&w=800&q=80",
        "banner_image": "https://images.unsplash.com/photo-1610192244261-3f33de3f55e4?auto=format&fit=crop&w=1200&q=80",
        "is_featured": 1,
        "tags": "Ghee Dosa, Filter Coffee, Vada, Chettinad, Pure Veg",
        "opening_hours": "7:00 AM - 10:30 PM",
    },
    {
        "name": "Beirut Mezze & Grill",
        "cuisine": "Middle Eastern",
        "description": "Smoky charcoal grilled shish kebabs, velvet hummus with warm za'atar pita, crispy falafel, and refreshing pomegranate fattoush.",
        "address": "62 Residency Road, Shanthala Nagar, Bengaluru",
        "phone": "+91 98765 12345",
        "rating": 4.7,
        "review_count": 315,
        "delivery_time": "25-35 min",
        "delivery_fee": 35.0,
        "min_order": 220.0,
        "price_level": "$$$",
        "image": "https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=800&q=80",
        "banner_image": "https://images.unsplash.com/photo-1529006557810-274b9b2fc783?auto=format&fit=crop&w=1200&q=80",
        "is_featured": 1,
        "tags": "Shawarma, Hummus, Kebab, Falafel, Lebanese, Mezze",
        "opening_hours": "12:00 PM - 11:30 PM",
    },
]

# Detailed food items per restaurant
_FOOD_ITEMS_SEED = {
    "Spice Garden": [
        ("Royal Butter Chicken", "Tender boneless chicken roasted in tandoor and simmered in velvety makhani gravy.", 349.0, 299.0, "Main Course", 0, "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?auto=format&fit=crop&w=600&q=80", "Bestseller", 520, 4.9, 180),
        ("Dal Bukhara Makhani", "Black lentils slow-cooked for 18 hours with churned butter and cream.", 249.0, None, "Main Course", 1, "https://images.unsplash.com/photo-1546833999-b9f581a1996d?auto=format&fit=crop&w=600&q=80", "Chef Special", 380, 4.8, 140),
        ("Hyderabadi Dum Biryani", "Aromatic aged basmati rice layered with marinated chicken, saffron, and mint.", 369.0, 329.0, "Biryani", 0, "https://images.unsplash.com/photo-1589302168068-964664d93dc0?auto=format&fit=crop&w=600&q=80", "Must Try", 680, 4.9, 230),
        ("Paneer Tikka Angara", "Marinated cottage cheese cubes chargrilled with bell peppers and roasted spices.", 289.0, None, "Starters", 1, "https://images.unsplash.com/photo-1565557623262-b51c2513a641?auto=format&fit=crop&w=600&q=80", "Popular", 420, 4.7, 110),
        ("Garlic Butter Naan", "Hand-stretched leavened flatbread topped with minced garlic and melted ghee.", 69.0, None, "Breads", 1, "https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=600&q=80", None, 210, 4.8, 310),
        ("Kesari Rasmalai", "Soft cottage cheese patties soaked in saffron and cardamom scented milk.", 129.0, None, "Desserts", 1, "https://images.unsplash.com/photo-1589119908995-c6837fa14d48?auto=format&fit=crop&w=600&q=80", None, 260, 4.9, 95),
        ("Alphonso Mango Lassi", "Thick chilled yoghurt drink churned with pure Ratnagiri Alphonso mango pulp.", 99.0, None, "Beverages", 1, "https://images.unsplash.com/photo-1546173159-315724a31696?auto=format&fit=crop&w=600&q=80", "Trending", 190, 4.8, 150),
    ],
    "Pizza Roma": [
        ("Margherita Di Bufala", "San Marzano D.O.P. tomatoes, fresh buffalo mozzarella, fresh basil, and extra virgin olive oil.", 399.0, 349.0, "Pizzas", 1, "https://images.unsplash.com/photo-1604382354936-07c5d9983bd3?auto=format&fit=crop&w=600&q=80", "Bestseller", 650, 4.9, 210),
        ("Diavola Pepperoni", "Spicy artisan pepperoni, smoked provolone, fresh mozzarella, and chili honey drizzle.", 479.0, 429.0, "Pizzas", 0, "https://images.unsplash.com/photo-1628840042765-356cda07504e?auto=format&fit=crop&w=600&q=80", "Must Try", 780, 4.9, 260),
        ("Truffle Wild Mushroom", "Creamy fontina base, sauteed porcini and cremini mushrooms, white truffle oil.", 459.0, None, "Pizzas", 1, "https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=600&q=80", "Chef Special", 710, 4.8, 130),
        ("Handmade Fettuccine Alfredo", "Handmade egg pasta ribbons tossed in Parmesan Reggiano butter sauce with roasted garlic.", 349.0, None, "Pasta", 1, "https://images.unsplash.com/photo-1645112411341-6c4fd023714a?auto=format&fit=crop&w=600&q=80", None, 580, 4.7, 120),
        ("Cheesy Garlic Dough Knots", "Sourdough knots baked with garlic herb butter, parsley, and marinara dip.", 189.0, None, "Sides", 1, "https://images.unsplash.com/photo-1541592106381-b31e9677c0e5?auto=format&fit=crop&w=600&q=80", "Popular", 320, 4.8, 190),
        ("Classic Venetian Tiramisu", "Savoiardi ladyfingers soaked in espresso and Marsala, layered with mascarpone cream.", 219.0, None, "Desserts", 1, "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?auto=format&fit=crop&w=600&q=80", "Bestseller", 390, 5.0, 240),
    ],
    "The Burger Beast": [
        ("The Double Beast Smash", "Twin 100% aged beef patties, double American cheddar, caramelized onions, Beast secret sauce.", 329.0, 289.0, "Burgers", 0, "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=600&q=80", "Bestseller", 720, 4.9, 320),
        ("Crispy Nashville Hot Chicken", "Golden battered spicy chicken thigh, sweet pickles, spicy slaw, honey butter glaze.", 299.0, None, "Burgers", 0, "https://images.unsplash.com/photo-1625813506062-0aeb1d7a094b?auto=format&fit=crop&w=600&q=80", "Must Try", 690, 4.8, 280),
        ("Truffle Portobello Veggie Burger", "Panko-crusted whole portobello mushroom stuffed with mozzarella, garlic aioli.", 279.0, None, "Burgers", 1, "https://images.unsplash.com/photo-1550547660-d9450f859349?auto=format&fit=crop&w=600&q=80", "Chef Special", 540, 4.7, 160),
        ("Parmesan Truffle Fries", "Crispy crinkle fries tossed in black truffle oil, rosemary sea salt, and grated Parmesan.", 169.0, None, "Sides", 1, "https://images.unsplash.com/photo-1576107232684-1279f3908594?auto=format&fit=crop&w=600&q=80", "Popular", 410, 4.9, 290),
        ("Spicy Buffalo Wings (8 pcs)", "Crisp fried wings tossed in Frank's red hot sauce with blue cheese dip and celery.", 269.0, 239.0, "Sides", 0, "https://images.unsplash.com/photo-1567620832903-9fc6debc209f?auto=format&fit=crop&w=600&q=80", None, 580, 4.7, 190),
        ("Belgian Dark Chocolate Thickshake", "Whole milk churned with 70% dark Belgian chocolate ganache and chocolate curls.", 179.0, None, "Beverages", 1, "https://images.unsplash.com/photo-1572490122747-3968b75cc699?auto=format&fit=crop&w=600&q=80", "Trending", 480, 4.8, 175),
    ],
    "Sakura Sushi & Ramen": [
        ("Dragon Roll (8 pcs)", "Tempura prawn and cucumber wrapped with fresh avocado, unagi eel sauce, and tobiko.", 489.0, 449.0, "Sushi", 0, "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?auto=format&fit=crop&w=600&q=80", "Bestseller", 380, 4.9, 195),
        ("Salmon Nigiri & Sashimi Set", "Fresh Norwegian salmon slices served with pickled ginger, fresh wasabi, and nikiri soy.", 549.0, None, "Sushi", 0, "https://images.unsplash.com/photo-1617196034796-73dfa7b1fd56?auto=format&fit=crop&w=600&q=80", "Chef Special", 320, 5.0, 160),
        ("Rich Tonkotsu Chashu Ramen", "18-hour broth, handmade ramen noodles, slow-braised pork chashu, ajitsuke tamago, nori.", 429.0, 389.0, "Ramen", 0, "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=600&q=80", "Must Try", 640, 4.9, 240),
        ("Spicy Miso Tofu Ramen", "Silky vegetable broth infused with red miso, roasted tofu, sweet corn, bamboo shoots, chili oil.", 369.0, None, "Ramen", 1, "https://images.unsplash.com/photo-1591814468924-caf88d1232e1?auto=format&fit=crop&w=600&q=80", "Veg Choice", 510, 4.7, 120),
        ("Pan-Fried Gyoza (6 pcs)", "Crispy bottom Japanese chicken and scallion dumplings served with sesame ponzu.", 249.0, None, "Starters", 0, "https://images.unsplash.com/photo-1496116218417-1a781b1c416c?auto=format&fit=crop&w=600&q=80", "Popular", 280, 4.8, 170),
        ("Matcha Green Tea Tiramisu", "Ceremonial grade Uji matcha layered with mascarpone cream and white chocolate shavings.", 219.0, None, "Desserts", 1, "https://images.unsplash.com/photo-1536256263959-770b48d82b0a?auto=format&fit=crop&w=600&q=80", None, 290, 4.8, 110),
    ],
    "Golden Dragon Wok": [
        ("Cantonese Chicken Dim Sum", "Translucent crystal dumplings stuffed with juicy minced chicken and water chestnuts.", 269.0, 229.0, "Dim Sum", 0, "https://images.unsplash.com/photo-1563245372-f21724e3856d?auto=format&fit=crop&w=600&q=80", "Bestseller", 240, 4.8, 180),
        ("Szechuan Chilli Garlic Noodles", "Wok-tossed hand-pulled noodles with charred garlic, red chillies, and scallions.", 229.0, None, "Noodles", 1, "https://images.unsplash.com/photo-1585032226651-759b368d7246?auto=format&fit=crop&w=600&q=80", "Must Try", 460, 4.7, 210),
        ("Crispy Kung Pao Chicken", "Golden chicken tossed with dry red chillies, Szechuan peppercorns, roasted peanuts, and spring onions.", 319.0, 279.0, "Main Course", 0, "https://images.unsplash.com/photo-1525755662778-989d0524087e?auto=format&fit=crop&w=600&q=80", "Chef Special", 520, 4.8, 175),
        ("Yangzhou Special Fried Rice", "Wok-fried jasmine rice with scrambled egg, tender prawns, chicken, and sweet green peas.", 329.0, None, "Rice", 0, "https://images.unsplash.com/photo-1603133872878-684f208fb84b?auto=format&fit=crop&w=600&q=80", "Popular", 550, 4.8, 150),
        ("Vegetable Spring Rolls (4 pcs)", "Golden fried crispy wrappers loaded with julienned veggies and sweet plum sauce.", 169.0, None, "Starters", 1, "https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=600&q=80", None, 280, 4.6, 130),
        ("Hot & Sour Soup", "Authentic cloudy broth with black wood-ear mushrooms, bamboo shoots, tofu, and chili vinegar.", 159.0, None, "Soups", 1, "https://images.unsplash.com/photo-1547592166-23ac45744acd?auto=format&fit=crop&w=600&q=80", None, 180, 4.7, 140),
    ],
    "Taco Fuego": [
        ("Slow-Cooked Barbacoa Tacos (3 pcs)", "Tender spiced braised beef on warm corn tortillas with salsa verde, diced white onion, and cilantro.", 329.0, 289.0, "Tacos", 0, "https://images.unsplash.com/photo-1565299585323-38d6b0865b47?auto=format&fit=crop&w=600&q=80", "Bestseller", 490, 4.9, 210),
        ("Crispy Fish Baja Tacos (3 pcs)", "Beer-battered fish fillets, purple chipotle slaw, avocado pico de gallo, fresh lime.", 349.0, None, "Tacos", 0, "https://images.unsplash.com/photo-1551504734-5ee1c4a1479b?auto=format&fit=crop&w=600&q=80", "Chef Special", 440, 4.8, 160),
        ("Grande California Burrito", "Flour tortilla rolled with carne asada, crispy fries, guacamole, jack cheese, sour cream.", 369.0, 319.0, "Burritos", 0, "https://images.unsplash.com/photo-1626700051175-6818013e1d4f?auto=format&fit=crop&w=600&q=80", "Must Try", 750, 4.8, 230),
        ("Loaded Queso Nachos", "Corn tortilla chips layered with molten queso blanco, black beans, jalapenos, and pico de gallo.", 249.0, None, "Sides", 1, "https://images.unsplash.com/photo-1513456852971-30c0b8199d4d?auto=format&fit=crop&w=600&q=80", "Popular", 520, 4.7, 190),
        ("Cinnamon Sugar Churros", "Golden fried Mexican pastry sticks dusted in cinnamon sugar with warm dulce de leche dip.", 179.0, None, "Desserts", 1, "https://images.unsplash.com/photo-1624371414361-e670edf4898d?auto=format&fit=crop&w=600&q=80", "Sweet Tooth", 380, 4.9, 220),
    ],
    "Green Bowl Co.": [
        ("Mediterranean Falafel Power Bowl", "Crispy spiced falafel, beetroot hummus, quinoa, kalamata olives, cucumber, tahini dressing.", 299.0, 259.0, "Bowls", 1, "https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=600&q=80", "Bestseller", 460, 4.9, 190),
        ("Avocado & Burrata Sourdough", "Toasted artisanal sourdough, Hass avocado mash, creamy burrata ball, chili flakes, balsamic glaze.", 349.0, None, "Toast", 1, "https://images.unsplash.com/photo-1525351484163-7529414344d8?auto=format&fit=crop&w=600&q=80", "Must Try", 420, 4.8, 140),
        ("Berry Acai Antioxidant Bowl", "Frozen organic acai puree blended with blueberries, topped with granola, chia seeds, and kiwi.", 289.0, None, "Bowls", 1, "https://images.unsplash.com/photo-1590301157890-4810ed352733?auto=format&fit=crop&w=600&q=80", "Popular", 310, 4.9, 160),
        ("Grilled Teriyaki Tofu Salad", "Organic tofu glazed in low-sodium teriyaki, edamame, baby spinach, sesame ginger dressing.", 279.0, None, "Salads", 1, "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=600&q=80", "Keto Friendly", 340, 4.7, 115),
        ("Cold Pressed Green Detox Juice", "Celery, green apple, cucumber, kale, ginger, and Meyer lemon.", 149.0, None, "Beverages", 1, "https://images.unsplash.com/photo-1613478223719-2ab802602423?auto=format&fit=crop&w=600&q=80", "Healthy", 95, 4.8, 205),
    ],
    "Cafe Lumière & Bakery": [
        ("Butter Almond Croissant", "Twice-baked flaky French croissant loaded with almond frangipane cream and toasted sliced almonds.", 169.0, 149.0, "Viennoiserie", 1, "https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&w=600&q=80", "Bestseller", 360, 4.9, 290),
        ("Pain au Chocolat", "Laminated buttery pastry filled with dual batons of Valrhona 64% dark chocolate.", 159.0, None, "Viennoiserie", 1, "https://images.unsplash.com/photo-1608198093002-ad4e005484ec?auto=format&fit=crop&w=600&q=80", "Popular", 340, 4.9, 240),
        ("French Macaron Box (6 pcs)", "Assorted Parisian macarons: Salted Caramel, Pistachio, Raspberry, Dark Chocolate, Vanilla.", 329.0, 289.0, "Pastries", 1, "https://images.unsplash.com/photo-1569864358642-9d1684040f43?auto=format&fit=crop&w=600&q=80", "Chef Special", 290, 4.8, 170),
        ("Spanish Iced Cortado", "Double shot of Colombian espresso shaken with condensed milk and whole milk over rock ice.", 159.0, None, "Coffee", 1, "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?auto=format&fit=crop&w=600&q=80", "Signature", 140, 4.9, 260),
        ("Belgian Dark Chocolate Opera Cake", "Delicate almond sponge cake soaked in coffee syrup, layered with ganache and coffee buttercream.", 239.0, None, "Pastries", 1, "https://images.unsplash.com/photo-1578985545062-69928b1d9587?auto=format&fit=crop&w=600&q=80", "Must Try", 410, 5.0, 185),
    ],
    "Dakshin Rasoi": [
        ("Mysore Masala Ghee Dosa", "Crispy golden fermented crepe smeared with spicy red garlic chutney and stuffed with spiced potato mash.", 149.0, 129.0, "Tiffins", 1, "https://images.unsplash.com/photo-1668236543090-82eba5ee5976?auto=format&fit=crop&w=600&q=80", "Bestseller", 390, 4.9, 380),
        ("Ghee Podi Idli (4 pcs)", "Mini button idlis tossed generously in aromatic gun-powder spice and hot melted desi ghee.", 129.0, None, "Tiffins", 1, "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?auto=format&fit=crop&w=600&q=80", "Must Try", 290, 4.8, 290),
        ("Crispy Medu Vada (2 pcs)", "Golden fried lentil donuts with a crunchy crust and fluffy center, served with coconut chutney and sambar.", 89.0, None, "Tiffins", 1, "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?auto=format&fit=crop&w=600&q=80", "Popular", 240, 4.8, 220),
        ("Chettinad Paneer Curry", "Cottage cheese simmered in spicy freshly pounded black pepper, star anise, and coconut gravy.", 239.0, None, "Curries", 1, "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?auto=format&fit=crop&w=600&q=80", "Chef Special", 370, 4.7, 130),
        ("Authentic Filter Coffee", "Freshly brewed chicory blend decoction frothed with boiled full-cream milk in a traditional dabarah.", 49.0, None, "Beverages", 1, "https://images.unsplash.com/photo-1517256064527-09c73fc73e38?auto=format&fit=crop&w=600&q=80", "Signature", 110, 5.0, 450),
    ],
    "Beirut Mezze & Grill": [
        ("Signature Chicken Shawarma Plate", "Marinated sliced chicken off the vertical spit, served with garlic toum, pickles, fries, and flatbread.", 329.0, 289.0, "Platters", 0, "https://images.unsplash.com/photo-1529006557810-274b9b2fc783?auto=format&fit=crop&w=600&q=80", "Bestseller", 620, 4.9, 260),
        ("Creamy Hummus with Spiced Lamb", "Velvety chickpea puree with tahini, olive oil, topped with spiced minced lamb and pine nuts.", 279.0, None, "Mezze", 0, "https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=600&q=80", "Chef Special", 440, 4.9, 180),
        ("Crispy Falafel Platter (6 pcs)", "Herbaceous chickpea fritters served with pickled turnips, diced sumac salad, and tahini drizzle.", 219.0, None, "Mezze", 1, "https://images.unsplash.com/photo-1593001874117-c99c800e3eb7?auto=format&fit=crop&w=600&q=80", "Veg Favourite", 360, 4.8, 195),
        ("Shish Tawook Skewers (2 pcs)", "Chicken breast cubes marinated in garlic, lemon, paprika, yogurt, chargrilled over live coals.", 349.0, 309.0, "Grills", 0, "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?auto=format&fit=crop&w=600&q=80", "Must Try", 510, 4.8, 170),
        ("Pomegranate Mint Lemonade", "Freshly squeezed lemon juice, muddled garden mint, sparkling water, and organic pomegranate reduction.", 119.0, None, "Beverages", 1, "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?auto=format&fit=crop&w=600&q=80", "Refreshing", 90, 4.7, 140),
    ],
}

_REVIEWS_SEED = [
    ("Aarav Patel", 1, 5, "Best butter chicken in town! The garlic naan was super soft and the delivery arrived in just 25 minutes hot and fresh."),
    ("Priya Sharma", 1, 5, "Authentic taste. The Dal Bukhara is rich, creamy, and reminds me of top Mughlai restaurants in Delhi."),
    ("Vikram Singh", 2, 5, "The sourdough crust on the Diavola pizza is perfection. Crispy, airy, and the hot honey takes it to another level!"),
    ("Sneha Nair", 2, 4, "Loved the Tiramisu and handmade pasta. Packaging kept everything intact and warm."),
    ("Rohan Deshmukh", 3, 5, "Insane smash burgers! The Double Beast was juicy, bursting with flavor, and the truffle fries are addictive."),
    ("Kavya Rao", 4, 5, "Sakura Sushi never disappoints. Fresh salmon sashimi, perfectly seasoned sushi rice, and prompt delivery!"),
    ("Ananya Roy", 5, 4, "Loved the dim sums and noodles. Tangy, spicy, and generous portion size."),
    ("Deepak Verma", 6, 5, "The barbacoa tacos taste like authentic Mexican street tacos. The salsa verde is truly top tier."),
    ("Divya Iyer", 7, 5, "Finally a place that makes healthy food actually taste incredible! The Falafel power bowl is my daily lunch now."),
    ("Meera Nambiar", 8, 5, "The almond croissant was super flaky and buttery! You can taste the quality French butter."),
    ("Karthik Hegde", 9, 5, "Crispy Ghee roast dosa with piping hot filter coffee. Unbeatable comfort food delivered swiftly."),
    ("Farhan Akhtar", 10, 5, "The Shawarma platter and garlic toum are top quality. Truly authentic Beirut taste!"),
]


# ---------------------------------------------------------------------------
# Database Initialization & Seeding
# ---------------------------------------------------------------------------

def init_db(force_reseed=False):
    """
    Initialise the database tables and seed comprehensive data.
    If force_reseed is True or if the schema is fresh, inserts the rich datasets.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # If force_reseed is True, drop old tables so new schema is applied completely
    if force_reseed:
        cursor.execute("PRAGMA foreign_keys = OFF")
        for tbl in ["order_items", "orders", "reviews", "food_items", "restaurants", "users"]:
            cursor.execute(f"DROP TABLE IF EXISTS {tbl}")
        cursor.execute("PRAGMA foreign_keys = ON")
        conn.commit()

    # Create tables
    conn.executescript(_CREATE_TABLES_SQL)
    conn.commit()

    # Check if restaurants already exist
    existing_count = cursor.execute("SELECT COUNT(*) FROM restaurants").fetchone()[0]

    # If force_reseed or empty, seed rich data
    if force_reseed or existing_count < 8:
        print("[DB] Populating database with rich seed data...")
        # Clear out existing demo data to avoid duplicates
        cursor.execute("DELETE FROM order_items")
        cursor.execute("DELETE FROM orders")
        cursor.execute("DELETE FROM reviews")
        cursor.execute("DELETE FROM food_items")
        cursor.execute("DELETE FROM restaurants")

        # 1. Seed demo users
        for u in _DEFAULT_USERS:
            cursor.execute(
                """
                INSERT INTO users (name, email, password_hash, role, phone, address, avatar)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(email) DO UPDATE SET
                    name = excluded.name,
                    role = excluded.role,
                    phone = excluded.phone,
                    address = excluded.address,
                    avatar = excluded.avatar
                """,
                (
                    u["name"],
                    u["email"],
                    generate_password_hash(u["password"]),
                    u["role"],
                    u["phone"],
                    u["address"],
                    u["avatar"],
                ),
            )

        # 2. Seed restaurants
        restaurant_ids = {}
        for r in _RESTAURANTS_SEED:
            cursor.execute(
                """
                INSERT INTO restaurants (
                    name, cuisine, description, address, phone, rating,
                    review_count, delivery_time, delivery_fee, min_order, price_level,
                    image, banner_image, is_featured, is_active, tags, opening_hours
                )
                VALUES (
                    :name, :cuisine, :description, :address, :phone, :rating,
                    :review_count, :delivery_time, :delivery_fee, :min_order, :price_level,
                    :image, :banner_image, :is_featured, 1, :tags, :opening_hours
                )
                """,
                r,
            )
            restaurant_ids[r["name"]] = cursor.lastrowid

        # 3. Seed food items
        seeded_food_item_ids = {}
        for rest_name, items in _FOOD_ITEMS_SEED.items():
            rid = restaurant_ids.get(rest_name)
            if not rid:
                continue
            for item in items:
                (name, desc, price, disc_price, cat, is_veg, img, badge, cal, rating, ocount) = item
                cursor.execute(
                    """
                    INSERT INTO food_items (
                        restaurant_id, name, description, price, discount_price,
                        category, is_veg, is_available, image, badge, calories, rating, order_count
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?)
                    """,
                    (rid, name, desc, price, disc_price, cat, is_veg, img, badge, cal, rating, ocount),
                )
                seeded_food_item_ids[f"{rid}_{name}"] = cursor.lastrowid

        # 4. Seed reviews
        for user_name, r_idx, rating, comment in _REVIEWS_SEED:
            # Map index to actual restaurant id
            all_r_ids = list(restaurant_ids.values())
            rid = all_r_ids[(r_idx - 1) % len(all_r_ids)]
            cursor.execute(
                """
                INSERT INTO reviews (user_id, restaurant_id, user_name, rating, comment)
                VALUES (1, ?, ?, ?, ?)
                """,
                (rid, user_name, rating, comment),
            )

        # 5. Seed sample orders so customer and dashboards have rich initial state
        sample_orders = [
            {
                "order_number": "ORD-FE-8291",
                "restaurant_name": "Spice Garden",
                "subtotal": 678.0,
                "delivery_fee": 35.0,
                "tax": 33.9,
                "total_amount": 746.9,
                "status": "delivered",
                "payment_method": "UPI",
                "items": [
                    ("Royal Butter Chicken", 1, 299.0),
                    ("Dal Bukhara Makhani", 1, 249.0),
                    ("Garlic Butter Naan", 2, 65.0),
                ],
                "created_at": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
            },
            {
                "order_number": "ORD-FE-9042",
                "restaurant_name": "Pizza Roma",
                "subtotal": 778.0,
                "delivery_fee": 0.0,
                "tax": 38.9,
                "total_amount": 816.9,
                "status": "out_for_delivery",
                "payment_method": "Credit Card",
                "items": [
                    ("Diavola Pepperoni", 1, 429.0),
                    ("Margherita Di Bufala", 1, 349.0),
                ],
                "created_at": (datetime.now() - timedelta(minutes=25)).strftime("%Y-%m-%d %H:%M:%S"),
            },
            {
                "order_number": "ORD-FE-9125",
                "restaurant_name": "The Burger Beast",
                "subtotal": 458.0,
                "delivery_fee": 30.0,
                "tax": 22.9,
                "total_amount": 510.9,
                "status": "preparing",
                "payment_method": "Cash on Delivery",
                "items": [
                    ("The Double Beast Smash", 1, 289.0),
                    ("Parmesan Truffle Fries", 1, 169.0),
                ],
                "created_at": (datetime.now() - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S"),
            },
        ]

        for so in sample_orders:
            rid = restaurant_ids[so["restaurant_name"]]
            cursor.execute(
                """
                INSERT INTO orders (
                    order_number, user_id, restaurant_id, total_amount, subtotal,
                    delivery_fee, tax, status, payment_method, delivery_address, created_at
                )
                VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    so["order_number"],
                    rid,
                    so["total_amount"],
                    so["subtotal"],
                    so["delivery_fee"],
                    so["tax"],
                    so["status"],
                    so["payment_method"],
                    "402, Sunshine Heights, Indiranagar, Bengaluru",
                    so["created_at"],
                ),
            )
            oid = cursor.lastrowid
            for iname, qty, uprice in so["items"]:
                cursor.execute(
                    """
                    INSERT INTO order_items (order_id, food_item_name, quantity, unit_price, total_price)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (oid, iname, qty, uprice, qty * uprice),
                )

        conn.commit()
        print("[DB] Rich database seeding completed successfully.")

    conn.close()
    print(f"[DB] Database verified and active at: {DB_PATH}")


# ---------------------------------------------------------------------------
# Restaurant Queries & Filtering
# ---------------------------------------------------------------------------

def get_all_restaurants(cuisine=None, query=None, sort_by=None, veg_only=False):
    """
    Fetch restaurants with flexible filtering and sorting.
    """
    conn = get_connection()
    sql = "SELECT * FROM restaurants WHERE is_active = 1"
    params = []

    if cuisine and cuisine.lower() != "all":
        sql += " AND LOWER(cuisine) = LOWER(?)"
        params.append(cuisine)

    if query and query.strip():
        term = f"%{query.strip()}%"
        sql += " AND (name LIKE ? OR cuisine LIKE ? OR description LIKE ? OR tags LIKE ?)"
        params.extend([term, term, term, term])

    if veg_only:
        # Only restaurants that have veg specialities or tags containing veg
        sql += " AND (tags LIKE '%Veg%' OR cuisine IN ('Healthy', 'South Indian'))"

    # Sorting
    if sort_by == "rating":
        sql += " ORDER BY rating DESC"
    elif sort_by == "fastest":
        sql += " ORDER BY delivery_time ASC"
    elif sort_by == "delivery_fee":
        sql += " ORDER BY delivery_fee ASC"
    elif sort_by == "min_order":
        sql += " ORDER BY min_order ASC"
    else:
        sql += " ORDER BY is_featured DESC, rating DESC"

    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return rows


def get_restaurant_by_id(restaurant_id):
    """Return a single restaurant row with all attributes."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM restaurants WHERE id = ?", (restaurant_id,)).fetchone()
    conn.close()
    return row


def get_all_cuisines():
    """Return distinct cuisine types available in the platform."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT cuisine FROM restaurants WHERE is_active = 1 ORDER BY cuisine"
    ).fetchall()
    conn.close()
    return [r["cuisine"] for r in rows]


def get_food_items_by_restaurant(restaurant_id, category=None, veg_only=False):
    """Return food items for a restaurant, optionally filtered by category or veg flag."""
    conn = get_connection()
    sql = "SELECT * FROM food_items WHERE restaurant_id = ? AND is_available = 1"
    params = [restaurant_id]

    if category and category.lower() != "all":
        sql += " AND LOWER(category) = LOWER(?)"
        params.append(category)

    if veg_only:
        sql += " AND is_veg = 1"

    sql += " ORDER BY category, rating DESC"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return rows


def get_restaurant_categories(restaurant_id):
    """Return distinct categories available in a restaurant's menu."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT category FROM food_items WHERE restaurant_id = ? ORDER BY category",
        (restaurant_id,),
    ).fetchall()
    conn.close()
    return [r["category"] for r in rows]


def get_food_item_by_id(food_item_id):
    """Return a single food item row."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM food_items WHERE id = ?", (food_item_id,)).fetchone()
    conn.close()
    return row


# ---------------------------------------------------------------------------
# Reviews Queries
# ---------------------------------------------------------------------------

def get_reviews_by_restaurant(restaurant_id):
    """Return all reviews for a restaurant ordered by latest."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM reviews WHERE restaurant_id = ? ORDER BY created_at DESC",
        (restaurant_id,),
    ).fetchall()
    conn.close()
    return rows


def add_review(user_id, restaurant_id, user_name, rating, comment):
    """Add a customer review and update restaurant average rating."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO reviews (user_id, restaurant_id, user_name, rating, comment)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, restaurant_id, user_name, rating, comment),
    )
    # Recalculate average rating
    stats = cursor.execute(
        "SELECT AVG(rating), COUNT(*) FROM reviews WHERE restaurant_id = ?",
        (restaurant_id,),
    ).fetchone()
    if stats and stats[0]:
        new_rating = round(float(stats[0]), 1)
        new_count = stats[1]
        cursor.execute(
            "UPDATE restaurants SET rating = ?, review_count = ? WHERE id = ?",
            (new_rating, new_count, restaurant_id),
        )
    conn.commit()
    conn.close()
    return True


# ---------------------------------------------------------------------------
# Orders & Checkout Queries
# ---------------------------------------------------------------------------

def create_order(user_id, restaurant_id, cart_items, delivery_address, payment_method, special_instructions=""):
    """
    Create a new order and line items from cart items.
    cart_items: list of dicts [{'food_item': Row/dict, 'quantity': int}]
    """
    conn = get_connection()
    cursor = conn.cursor()

    subtotal = 0.0
    for item in cart_items:
        price = item["food_item"]["discount_price"] if item["food_item"]["discount_price"] else item["food_item"]["price"]
        subtotal += price * item["quantity"]

    rest = cursor.execute("SELECT * FROM restaurants WHERE id = ?", (restaurant_id,)).fetchone()
    delivery_fee = 0.0 if subtotal >= 500 else (rest["delivery_fee"] if rest else 35.0)
    tax = round(subtotal * 0.05, 2)  # 5% GST
    total_amount = round(subtotal + delivery_fee + tax, 2)

    order_num = f"FE-{datetime.now().strftime('%m%d')}-{os.urandom(2).hex().upper()}"

    cursor.execute(
        """
        INSERT INTO orders (
            order_number, user_id, restaurant_id, total_amount, subtotal,
            delivery_fee, tax, status, payment_method, delivery_address, special_instructions
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, 'confirmed', ?, ?, ?)
        """,
        (
            order_num,
            user_id,
            restaurant_id,
            total_amount,
            subtotal,
            delivery_fee,
            tax,
            payment_method,
            delivery_address,
            special_instructions,
        ),
    )
    order_id = cursor.lastrowid

    # Insert items
    for item in cart_items:
        fi = item["food_item"]
        price = fi["discount_price"] if fi["discount_price"] else fi["price"]
        total_p = round(price * item["quantity"], 2)
        cursor.execute(
            """
            INSERT INTO order_items (order_id, food_item_id, food_item_name, quantity, unit_price, total_price)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (order_id, fi["id"], fi["name"], item["quantity"], price, total_p),
        )

    conn.commit()
    conn.close()
    return order_id, order_num


def get_order_by_id(order_id):
    """Return order details along with restaurant details and line items."""
    conn = get_connection()
    order = conn.execute(
        """
        SELECT o.*, r.name as restaurant_name, r.image as restaurant_image, r.phone as restaurant_phone
        FROM orders o
        JOIN restaurants r ON o.restaurant_id = r.id
        WHERE o.id = ?
        """,
        (order_id,),
    ).fetchone()

    if not order:
        conn.close()
        return None, []

    items = conn.execute(
        "SELECT * FROM order_items WHERE order_id = ?", (order_id,)
    ).fetchall()
    conn.close()
    return order, items


def get_orders_by_user(user_id):
    """Return all orders for a specific user ordered by newest first."""
    conn = get_connection()
    orders = conn.execute(
        """
        SELECT o.*, r.name as restaurant_name, r.image as restaurant_image,
               COUNT(oi.id) as item_count
        FROM orders o
        JOIN restaurants r ON o.restaurant_id = r.id
        LEFT JOIN order_items oi ON o.id = oi.order_id
        WHERE o.user_id = ?
        GROUP BY o.id
        ORDER BY o.created_at DESC
        """,
        (user_id,),
    ).fetchall()
    conn.close()
    return orders


def get_orders_by_restaurant(restaurant_id):
    """Return all orders received by a specific restaurant."""
    conn = get_connection()
    orders = conn.execute(
        """
        SELECT o.*, u.name as customer_name, u.phone as customer_phone
        FROM orders o
        LEFT JOIN users u ON o.user_id = u.id
        WHERE o.restaurant_id = ?
        ORDER BY o.created_at DESC
        """,
        (restaurant_id,),
    ).fetchall()
    conn.close()
    return orders


def get_all_orders():
    """Return all platform orders for Admin dashboard."""
    conn = get_connection()
    orders = conn.execute(
        """
        SELECT o.*, r.name as restaurant_name, u.name as customer_name
        FROM orders o
        JOIN restaurants r ON o.restaurant_id = r.id
        LEFT JOIN users u ON o.user_id = u.id
        ORDER BY o.created_at DESC
        """
    ).fetchall()
    conn.close()
    return orders


def update_order_status(order_id, new_status):
    """Update order status (e.g., preparing, out_for_delivery, delivered)."""
    conn = get_connection()
    conn.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
    conn.commit()
    conn.close()
    return True


# ---------------------------------------------------------------------------
# Dashboard Analytics Helpers
# ---------------------------------------------------------------------------

def get_admin_stats():
    """Calculate platform-wide operational statistics."""
    conn = get_connection()
    cursor = conn.cursor()

    total_restaurants = cursor.execute("SELECT COUNT(*) FROM restaurants WHERE is_active = 1").fetchone()[0]
    total_orders = cursor.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    total_revenue = cursor.execute("SELECT COALESCE(SUM(total_amount), 0) FROM orders").fetchone()[0]
    total_users = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]

    recent_orders = conn.execute(
        """
        SELECT o.*, r.name as restaurant_name, u.name as customer_name
        FROM orders o
        JOIN restaurants r ON o.restaurant_id = r.id
        LEFT JOIN users u ON o.user_id = u.id
        ORDER BY o.created_at DESC LIMIT 8
        """
    ).fetchall()

    top_restaurants = conn.execute(
        """
        SELECT r.name, r.cuisine, r.rating, r.image, COUNT(o.id) as order_count,
               COALESCE(SUM(o.total_amount), 0) as total_sales
        FROM restaurants r
        LEFT JOIN orders o ON r.id = o.restaurant_id
        GROUP BY r.id
        ORDER BY total_sales DESC LIMIT 5
        """
    ).fetchall()

    conn.close()
    return {
        "total_restaurants": total_restaurants,
        "total_orders": total_orders,
        "total_revenue": round(total_revenue, 2),
        "total_users": total_users,
        "recent_orders": recent_orders,
        "top_restaurants": top_restaurants,
    }


def get_owner_stats(restaurant_id=1):
    """Calculate restaurant-specific analytics for the owner dashboard."""
    conn = get_connection()
    cursor = conn.cursor()

    restaurant = cursor.execute("SELECT * FROM restaurants WHERE id = ?", (restaurant_id,)).fetchone()
    total_orders = cursor.execute("SELECT COUNT(*) FROM orders WHERE restaurant_id = ?", (restaurant_id,)).fetchone()[0]
    total_revenue = cursor.execute("SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE restaurant_id = ?", (restaurant_id,)).fetchone()[0]
    active_orders = cursor.execute(
        "SELECT COUNT(*) FROM orders WHERE restaurant_id = ? AND status IN ('pending', 'confirmed', 'preparing', 'out_for_delivery')",
        (restaurant_id,),
    ).fetchone()[0]
    menu_count = cursor.execute("SELECT COUNT(*) FROM food_items WHERE restaurant_id = ?", (restaurant_id,)).fetchone()[0]

    orders = conn.execute(
        """
        SELECT o.*, u.name as customer_name, u.phone as customer_phone
        FROM orders o
        LEFT JOIN users u ON o.user_id = u.id
        WHERE o.restaurant_id = ?
        ORDER BY o.created_at DESC LIMIT 10
        """,
        (restaurant_id,),
    ).fetchall()

    menu_items = conn.execute(
        "SELECT * FROM food_items WHERE restaurant_id = ? ORDER BY order_count DESC",
        (restaurant_id,),
    ).fetchall()

    conn.close()
    return {
        "restaurant": restaurant,
        "total_orders": total_orders,
        "total_revenue": round(total_revenue, 2),
        "active_orders": active_orders,
        "menu_count": menu_count,
        "orders": orders,
        "menu_items": menu_items,
    }


# ---------------------------------------------------------------------------
# User Authentication Helpers
# ---------------------------------------------------------------------------

def create_user(name, email, password_hash, role="customer", phone="", address=""):
    """Insert a new user row."""
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO users (name, email, password_hash, role, phone, address)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, email, password_hash, role, phone, address),
        )
        conn.commit()
        return True, None
    except Exception as exc:
        if "UNIQUE" in str(exc).upper():
            return False, "An account with this email already exists."
        return False, "Registration failed. Please try again."
    finally:
        conn.close()


def get_user_by_email(email):
    """Return user by email."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email,)).fetchone()
    conn.close()
    return row


def get_user_by_id(user_id):
    """Return user by ID."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return row
