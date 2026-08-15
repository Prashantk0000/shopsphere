# 🛍️ ShopSphere — Full-Stack E-Commerce Platform

A production-ready Django e-commerce platform with 15+ core features: product catalog, filtering, search, cart, wishlist, checkout, authentication, orders, payments, and admin dashboard.

**Tech Stack:** `Python` • `Django 5` • `SQLite` • `HTML5` • `CSS3 (Bootstrap 5)` • `JavaScript`

---

## ✨ Features (15+ core features)

### 🛒 Shopping Features
1. **Product Catalog** — Categories, brands, images, discounts, stock levels
2. **Advanced Filtering** — By category, brand, price range, sorting (price/newest/name)
3. **Search** — Full-text search across name, description, category, brand
4. **Session Cart** — Add / update / remove / clear items (persists across sessions)
5. **Wishlist** — Add/remove favorites (auth users)
6. **Product Reviews & Ratings** — 5-star reviews with auto-computed averages
7. **Coupons** — Percentage discount codes with validity windows
8. **Checkout** — Multi-step form with shipping address & payment method
9. **Multiple Payment Methods** — COD, Card, UPI, PayPal (mocked)
10. **Featured Products & Latest Arrivals** — Homepage sections

### 👤 User Features
11. **Authentication** — Register, login, logout with Django's auth system
12. **User Profiles** — Avatar, phone, DOB, editable profile
13. **Address Book** — Multiple shipping/billing addresses with default selection
14. **Order History** — View past orders, statuses, and details
15. **Order Cancellation** — Cancel pending/processing orders (auto restock)

### 🔒 Admin Features
16. **Role-Based Access Control** — Customer vs Admin/Staff roles
17. **Admin Dashboard** — Stats, low-stock alerts, recent orders
18. **Order Management** — Update order status, filter by status
19. **Django Admin** — Full CRUD for products, categories, brands, coupons, users
20. **Inventory Logging** — Every stock change is audit-logged

---

## 🗂️ Django Models (10+)

| Model | Purpose |
|---|---|
| `Category` | Product categorization with slugs |
| `Brand` | Product brands |
| `Product` | Core product with pricing, stock, discount |
| `ProductImage` | Additional gallery images |
| `Review` | User reviews with 5-star ratings |
| `Wishlist` | Per-user favorites (M2M with products) |
| `Coupon` | Percentage discount codes |
| `Customer` | Extended user profile + role |
| `Address` | Shipping/billing addresses |
| `Order` | Order with status workflow |
| `OrderItem` | Line items (product snapshot) |
| `Payment` | Payment method + status |
| `InventoryLog` | Stock change audit trail |

---

## 🚀 Quick Start

### 1. Clone & setup
```bash
cd shopsphere
python -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run migrations & seed sample data
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py seed_data
```

### 3. Start the server
```bash
python manage.py runserver
```

Open **http://127.0.0.1:8000/** 🎉

---

## 🔑 Default Login Credentials (from seed_data)

| Role | Username | Password |
|---|---|---|
| **Admin** | `admin` | `admin123` |
| **Customer** | `customer` | `customer123` |

### Coupons pre-seeded:
- `WELCOME10` — 10% off
- `SAVE20` — 20% off

---

## 📁 Project Structure

```
shopsphere/
├── shopsphere_project/       # Django project settings
│   ├── settings.py
│   └── urls.py
├── store/                    # Products, categories, cart, wishlist, reviews
│   ├── models.py             # Category, Brand, Product, Review, Wishlist, Coupon
│   ├── views.py
│   ├── cart.py               # Session-based Cart class
│   ├── middleware.py
│   ├── context_processors.py
│   ├── forms.py
│   ├── urls.py
│   ├── admin.py
│   └── management/commands/seed_data.py
├── accounts/                 # Auth, profile, addresses, admin dashboard
│   ├── models.py             # Customer (role-based), Address
│   ├── views.py
│   ├── forms.py
│   ├── signals.py
│   └── urls.py
├── orders/                   # Checkout, orders, payments, inventory
│   ├── models.py             # Order, OrderItem, Payment, InventoryLog
│   ├── views.py
│   ├── forms.py
│   └── urls.py
├── templates/                # Bootstrap 5 templates
│   ├── base.html
│   ├── store/
│   ├── accounts/
│   └── orders/
├── static/
│   ├── css/style.css
│   └── js/main.js
├── media/                    # Uploaded images
├── requirements.txt
└── manage.py
```

---

## 🌐 Key URLs

| URL | Purpose |
|---|---|
| `/` | Home |
| `/products/` | Product listing (with filters) |
| `/products/category/<slug>/` | Category page |
| `/product/<slug>/` | Product detail |
| `/search/?q=...` | Search |
| `/cart/` | Cart |
| `/wishlist/` | Wishlist |
| `/orders/checkout/` | Checkout |
| `/orders/` | My Orders |
| `/accounts/login/` | Login |
| `/accounts/register/` | Register |
| `/accounts/profile/` | User Profile |
| `/accounts/dashboard/` | Admin Dashboard (staff only) |
| `/orders/manage/all/` | Manage Orders (staff only) |
| `/admin/` | Django Admin |

---

## 🛠️ Django ORM — 15+ CRUD Operations

- Product: list, filter, search, sort, paginate, detail, wishlist toggle, review CRUD
- Cart: add / update / remove / clear (session-based)
- Order: create (checkout), read (list/detail), cancel (restock), admin status update
- Address: create / list / edit / delete
- Coupon: apply / validate / discount calculation
- User: register / login / logout / profile edit
- Payment: create linked to order
- InventoryLog: auto-write on sale / return

---

## 🚢 Deployment Notes

- Change `SECRET_KEY` and set `DEBUG = False` in `settings.py`
- Configure `ALLOWED_HOSTS`
- Run `python manage.py collectstatic`
- Switch to PostgreSQL for production (already ORM-compatible)
- Serve static/media via WhiteNoise or cloud storage

---

## 📄 License
MIT — free to use, modify, and distribute.

Built with ♥ using Django.
