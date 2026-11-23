import os

import pymysql
from flask import g


def connect(database=True, client_flag=0):
    return pymysql.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3307")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "smart_food_supply") if database else None,
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=5,
        client_flag=client_flag,
    )


def connection():
    if "db" not in g:
        g.db = connect()
    return g.db


def close_connection(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def rows(sql, params=()):
    with connection().cursor() as cursor:
        cursor.execute(sql, params)
        return cursor.fetchall()


def procedure(name, params):
    db = connection()
    try:
        with db.cursor() as cursor:
            cursor.callproc(name, params)
            while cursor.nextset():
                pass
        db.commit()
    except pymysql.MySQLError:
        db.rollback()
        raise
