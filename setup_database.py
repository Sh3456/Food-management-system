"""Apply the SQL files and seed a newly created database."""
import os
from pathlib import Path
import re

from pymysql.constants import CLIENT
from werkzeug.security import generate_password_hash

from db import connect

SQL = Path(__file__).resolve().parent / "database"


def apply(cursor, sql):
    cursor.execute(sql)
    while cursor.nextset():
        pass


def seed(cursor):
    cursor.execute("SELECT COUNT(*) AS total FROM CROP")
    if cursor.fetchone()["total"]:
        return
    cursor.executemany(
        "INSERT INTO CROP (id, name, category, base_price_per_kg, shelf_life_days) VALUES (%s,%s,%s,%s,%s)",
        [(101, "Wheat", "Grain", 30, 180), (102, "Rice", "Grain", 45, 180),
         (103, "Maize", "Grain", 28, 120), (104, "Potato", "Vegetable", 24, 45),
         (105, "Tomato", "Vegetable", 36, 14)],
    )
    password = generate_password_hash("password123")
    for role in ("FARMER", "WHOLESALER", "RETAILER"):
        email = f"{role.lower()}_1@demo.com"
        cursor.execute("SELECT id FROM USER_AUTH WHERE email=%s", (email,))
        if cursor.fetchone():
            continue
        cursor.execute("INSERT INTO USER_AUTH (email, password_hash, role) VALUES (%s,%s,%s)", (email, password, role))
        cursor.execute(
            f"INSERT INTO {role} (user_id, name, city) VALUES (%s,%s,%s)",
            (cursor.lastrowid, f"Demo {role.title()}", "Patiala"),
        )
        if role == "FARMER":
            cursor.execute(
                "INSERT INTO PRODUCTION (farmer_id,crop_id,quantity_kg,remaining_quantity,harvest_date,expiry_date,price_per_kg,region) "
                "VALUES (%s,101,40,40,CURDATE(),CURDATE()+INTERVAL 25 DAY,30,'Patiala')",
                (cursor.lastrowid,),
            )


def prepare_database():
    name = os.getenv("DB_NAME", "smart_food_supply")
    if not re.fullmatch(r"[A-Za-z0-9_]{1,64}", name):
        raise ValueError("DB_NAME must use only letters, digits, and underscores.")
    with connect(database=False, client_flag=CLIENT.MULTI_STATEMENTS) as db, db.cursor() as cursor:
        cursor.execute("SELECT GET_LOCK(%s, 20) AS acquired", (f"{name}:flask-setup",))
        if cursor.fetchone()["acquired"] != 1:
            raise RuntimeError("Could not acquire the database setup lock.")
        cursor.execute("SELECT COUNT(*) AS total FROM information_schema.SCHEMATA WHERE SCHEMA_NAME=%s", (name,))
        if not cursor.fetchone()["total"]:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{name}`")
        db.select_db(name)
        cursor.execute("SHOW FULL TABLES LIKE 'v_crop_price_comparison'")
        if not cursor.fetchone():
            base = (SQL / "schema.sql").read_text(encoding="utf-8")
            apply(cursor, base.replace("smart_food_supply", f"`{name}`"))
            apply(cursor, (SQL / "schema_updates.sql").read_text(encoding="utf-8"))
            apply(cursor, (SQL / "analysis.sql").read_text(encoding="utf-8"))
        seed(cursor)
        db.commit()
