import hmac
import os
import secrets
from datetime import date
from decimal import Decimal, InvalidOperation

import bcrypt
import pymysql
from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from db import close_connection, connection, procedure, rows

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)
app.teardown_appcontext(close_connection)

ROLE_TABLES = {"FARMER": "FARMER", "WHOLESALER": "WHOLESALER", "RETAILER": "RETAILER"}


@app.before_request
def identify_user():
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(32)
    if request.method == "POST" and not hmac.compare_digest(
        session["csrf"], request.form.get("csrf", "")
    ):
        abort(400, "Invalid form. Reload the page and try again.")
    g.user = session.get("user")


def verify_password(password, encoded):
    if encoded == "password_hash":
        return hmac.compare_digest(password, "password123")
    if encoded.startswith(("$2a$", "$2b$", "$2y$")):
        return len(password.encode()) <= 72 and bcrypt.checkpw(password.encode(), encoded.encode())
    return check_password_hash(encoded, password)


@app.get("/")
def home():
    return redirect(url_for("dashboard" if g.user else "login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        matches = rows("SELECT id, email, password_hash, role FROM USER_AUTH WHERE email=%s", (email,))
        if matches and verify_password(request.form.get("password", ""), matches[0]["password_hash"]):
            account = matches[0]
            table = ROLE_TABLES.get(account["role"])
            profile = rows(f"SELECT id, name FROM {table} WHERE user_id=%s", (account["id"],)) if table else []
            if table and not profile:
                flash("This account has no supply chain profile.")
            else:
                session.clear()
                session["user"] = {
                    "role": account["role"],
                    "name": profile[0]["name"] if profile else account["email"],
                    "entity_id": profile[0]["id"] if profile else None,
                }
                return redirect(url_for("dashboard"))
        else:
            flash("Email or password is incorrect.")
    return render_template("auth.html", signup=False)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        name = request.form.get("name", "").strip()
        role = request.form.get("role", "")
        password = request.form.get("password", "")
        if not (0 < len(email) <= 255 and "@" in email and 0 < len(name) <= 255
                and 8 <= len(password) <= 128 and role in ROLE_TABLES):
            flash("Enter a valid email, name, role, and a password of 8–128 characters.")
        else:
            db = connection()
            try:
                with db.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO USER_AUTH (email, password_hash, role) VALUES (%s, %s, %s)",
                        (email, generate_password_hash(password), role),
                    )
                    user_id = cursor.lastrowid
                    cursor.execute(
                        f"INSERT INTO {ROLE_TABLES[role]} (user_id, name, city, state, contact) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        (user_id, name, request.form.get("city", "").strip()[:100],
                         request.form.get("state", "").strip()[:100],
                         request.form.get("contact", "").strip()[:20]),
                    )
                db.commit()
            except pymysql.err.IntegrityError as error:
                db.rollback()
                if error.args[0] != 1062:
                    raise
                flash("This email already has an account.")
            else:
                flash("Account created. You can now sign in.")
                return redirect(url_for("login"))
    return render_template("auth.html", signup=True)


@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.get("/inventory")
def dashboard():
    if not g.user:
        return redirect(url_for("login"))
    role = g.user["role"]
    entity_id = g.user["entity_id"]
    if role == "ADMIN":
        return redirect(url_for("analysis"))
    city = request.args.get("city", "").strip() if role == "RETAILER" else ""
    market = []
    crops = []
    if role == "FARMER":
        inventory = rows(
            "SELECT * FROM v_production_pricing WHERE farmer_id=%s AND quantity_kg>0 ORDER BY expiry_date",
            (entity_id,),
        )
        crops = rows("SELECT id, name FROM CROP ORDER BY name")
    else:
        if role == "WHOLESALER":
            view, owner_col = "v_wholesaler_stock_pricing", "wholesaler_id"

        else:
            view, owner_col = "v_retail_stock_status", "retailer_id"

        inventory = rows(f"SELECT * FROM {view} WHERE {owner_col}=%s AND quantity_kg>0 ORDER BY expiry_date", (entity_id,))
        if role == "WHOLESALER":
            market = rows("""
                SELECT crop_id, crop_name, COUNT(*) AS batches, SUM(quantity_kg) AS quantity_kg,
                       MIN(expiry_date) AS expiry_date, MIN(discounted_price) AS discounted_price
                FROM v_production_pricing
                WHERE quantity_kg>0 AND expiry_date>=CURDATE()
                GROUP BY crop_id, crop_name ORDER BY crop_name
            """)
        else:
            sql = "SELECT * FROM v_wholesaler_stock_pricing WHERE quantity_kg>0 AND expiry_date>=CURDATE()"
            market = rows(sql + (" AND city=%s" if city else "") + " ORDER BY expiry_date, id", (city,) if city else ())
    alerts = rows(
        "SELECT message, created_at FROM SYSTEM_ALERTS WHERE user_id=%s AND role=%s ORDER BY created_at DESC LIMIT 10",
        (entity_id, role),
    )
    return render_template("inventory.html", inventory=inventory, market=market, crops=crops, city=city, alerts=alerts)


def positive_decimal(field):
    try:
        value = Decimal(request.form.get(field, ""))
        if value.is_finite() and 0 < value <= Decimal("99999999.99") and value == value.quantize(Decimal("0.01")):
            return value
    except InvalidOperation:
        pass
    raise ValueError("Enter positive quantities and prices with up to two decimal places.")


def positive_id(field):
    value = int(request.form.get(field, "0"))
    if not 0 < value <= 2147483647:
        raise ValueError("Choose a valid crop or stock batch.")
    return value


@app.post("/inventory")
def change_inventory():
    if not g.user:
        return redirect(url_for("login"))
    role, entity_id = g.user["role"], g.user["entity_id"]
    if role not in ROLE_TABLES:
        abort(403)
    try:
        quantity, price = positive_decimal("quantity"), positive_decimal("price")
        if role == "FARMER":
            harvest = date.fromisoformat(request.form.get("harvest", ""))
            expiry = date.fromisoformat(request.form.get("expiry", ""))
            if expiry < harvest or expiry < date.today():
                raise ValueError("Expiry must be today or later and on or after harvest.")
            region = rows("SELECT city FROM FARMER WHERE id=%s", (entity_id,))[0]["city"]
            procedure("add_production", (entity_id, positive_id("crop_id"), quantity, harvest, expiry, price, region))
        elif role == "WHOLESALER":
            procedure("buy_crop", (entity_id, positive_id("crop_id"), quantity, price))
        else:
            procedure("sell_stock", (positive_id("stock_id"), entity_id, quantity, price))
    except ValueError as error:
        flash(str(error))
    except pymysql.MySQLError as error:
        if error.args[0] == 1644:
            flash(error.args[1])
        else:
            app.logger.exception("Inventory update failed")
            flash("The database could not complete this update.")
    else:
        flash("Crop batch saved." if role == "FARMER" else "Purchase completed.")
    return redirect(url_for("dashboard"))


@app.get("/analysis")
def analysis():
    if not g.user:
        return redirect(url_for("login"))
    comparisons = rows("SELECT * FROM v_crop_price_comparison ORDER BY crop_name")
    expiry = rows("""
        SELECT crop_name, farmer_name, quantity_kg, expiry_date, days_to_expiry, status
        FROM v_production_pricing
        WHERE quantity_kg>0 AND days_to_expiry<=30
        ORDER BY expiry_date LIMIT 50
    """)
    transactions = rows("""
        SELECT t.transaction_timestamp, c.name AS crop, f.name AS farmer, w.name AS wholesaler,
               t.quantity, t.price, t.quantity*t.price AS total
        FROM TRANSACTIONS t
        JOIN CROP c ON c.id=t.crop_id
        JOIN FARMER f ON f.id=t.farmer_id
        JOIN WHOLESALER w ON w.id=t.wholesaler_id
        ORDER BY t.transaction_timestamp DESC, t.transaction_id DESC LIMIT 20
    """)
    return render_template("analysis.html", comparisons=comparisons, expiry=expiry, transactions=transactions)
