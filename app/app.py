"""items-api: Flask REST API for the Item entity, backed by MySQL.

  POST   /items           create an item   -> 201 / 400
  GET    /items/{itemId}  read one item    -> 200 / 404
  PUT    /items/{itemId}  update an item   -> 200 / 400 / 404
  DELETE /items/{itemId}  delete an item   -> 204 / 404
  GET    /items           list items (?lowStock=true for low stock only) -> 200
  GET    /health          liveness check   -> 200
  GET    /                web page (static/index.html)
"""
import os
import uuid
from datetime import datetime, timezone

import pymysql
from flask import Flask, jsonify, request
from pymysql.constants import CLIENT

from validation import validate_item

app = Flask(__name__)
app.json.sort_keys = False


def db():
    # FOUND_ROWS: UPDATE reports matched rows, so an unchanged PUT is not mistaken for a missing item.
    return pymysql.connect(
        host=os.environ.get("DB_HOST", "db"),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        cursorclass=pymysql.cursors.DictCursor,
        client_flag=CLIENT.FOUND_ROWS,
        autocommit=True,
    )


def now():
    return datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None)


def to_json(row):
    return {
        "itemId": row["item_id"],
        "name": row["name"],
        "folder": row["folder"],
        "quantity": row["quantity"],
        "unit": row["unit"],
        "reorderLevel": row["reorder_level"],
        "createdAt": row["created_at"].isoformat() + "Z",
        "updatedAt": row["updated_at"].isoformat() + "Z",
    }


def fetch(cur, item_id):
    cur.execute("SELECT * FROM items WHERE item_id = %s", (item_id,))
    return cur.fetchone()


def not_found(item_id):
    return jsonify(message=f"item {item_id} not found"), 404


def body_or_400():
    data, error = validate_item(request.get_json(silent=True))
    return data, (jsonify(message=error), 400) if error else None


@app.get("/")
def index():
    return app.send_static_file("index.html")


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.post("/items")
def create_item():
    data, error = body_or_400()
    if error:
        return error
    item_id, ts = str(uuid.uuid4()), now()
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO items (item_id, name, folder, quantity, unit, reorder_level, created_at, updated_at)"
            " VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (item_id, data["name"], data["folder"], data["quantity"], data["unit"], data["reorderLevel"], ts, ts),
        )
        return jsonify(to_json(fetch(cur, item_id))), 201


@app.get("/items")
def list_items():
    # shortcut: no paging, capped at 500 rows; add paging if a business tracks more lines than that.
    sql = "SELECT * FROM items"
    if request.args.get("lowStock") == "true":
        sql += " WHERE quantity <= reorder_level"
    with db() as conn, conn.cursor() as cur:
        cur.execute(sql + " ORDER BY name LIMIT 500")
        return jsonify([to_json(row) for row in cur.fetchall()])


@app.get("/items/<item_id>")
def get_item(item_id):
    with db() as conn, conn.cursor() as cur:
        row = fetch(cur, item_id)
    return jsonify(to_json(row)) if row else not_found(item_id)


@app.put("/items/<item_id>")
def update_item(item_id):
    data, error = body_or_400()
    if error:
        return error
    with db() as conn, conn.cursor() as cur:
        matched = cur.execute(
            "UPDATE items SET name = %s, folder = %s, quantity = %s, unit = %s, reorder_level = %s, updated_at = %s"
            " WHERE item_id = %s",
            (data["name"], data["folder"], data["quantity"], data["unit"], data["reorderLevel"], now(), item_id),
        )
        if not matched:
            return not_found(item_id)
        return jsonify(to_json(fetch(cur, item_id)))


@app.delete("/items/<item_id>")
def delete_item(item_id):
    with db() as conn, conn.cursor() as cur:
        if not cur.execute("DELETE FROM items WHERE item_id = %s", (item_id,)):
            return not_found(item_id)
    return "", 204


@app.errorhandler(404)
def unknown_route(_):
    return jsonify(message="not found"), 404


@app.errorhandler(405)
def method_not_allowed(_):
    return jsonify(message=f"{request.method} {request.path} is not supported"), 405


@app.errorhandler(500)
def internal_error(_):
    return jsonify(message="internal error"), 500
