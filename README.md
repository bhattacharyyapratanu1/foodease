# FoodEase 🍽️

A local food ordering platform connecting customers with local restaurants.

> First-year college project — built with Python / Flask, Jinja2, HTML, CSS, and JavaScript.

---

## Project Structure

```
FoodEase/
├── app.py               # Flask application and route definitions
├── database.py          # SQLite layer: schema, seed data, query helpers
├── foodease.db          # SQLite database file (auto-created on first run)
├── requirements.txt     # Python dependencies
├── README.md            # This file
│
├── templates/           # Jinja2 HTML templates
│   ├── base.html        # Shared layout (navbar + footer)
│   └── index.html       # Home page
│
└── static/              # Static assets served directly by Flask
    ├── css/
    │   └── style.css    # Main stylesheet
    └── js/
        └── main.js      # Vanilla JavaScript helpers
```

## Setup & Running

### 1. Create a virtual environment
```bash
python -m venv venv
```

### 2. Activate it
- **Windows:** `venv\Scripts\activate`
- **Mac / Linux:** `source venv/bin/activate`

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the development server
```bash
python app.py
```

Open your browser at **http://127.0.0.1:5000**

The database (`foodease.db`) is created and seeded automatically on first run.

---

## Roadmap

- [x] Basic project structure
- [x] Working home page (hero, categories, restaurant cards, how-it-works)
- [x] SQLite database integration (6 tables, 4 restaurants, 24 food items)
- [ ] Restaurant listing / detail page with menu
- [ ] User registration & login
- [ ] Shopping cart
- [ ] Order placement & history
