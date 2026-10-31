"""
Student Records - a small Flask web app that stores its data in MySQL.
Used for CSC418 Assignment 2 (Part I: Docker on EC2, Part II: Jenkins pipeline).
"""
import os
import socket
import time

import pymysql
from flask import Flask, jsonify, redirect, render_template_string, request, url_for

app = Flask(__name__)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "db"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "appuser"),
    "password": os.getenv("DB_PASSWORD", "apppass123"),
    "database": os.getenv("DB_NAME", "studentdb"),
}
APP_LABEL = os.getenv("APP_LABEL", "Student Records")


def get_conn():
    return pymysql.connect(
        **DB_CONFIG,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
        connect_timeout=5,
    )


def init_db(retries=40, delay=3):
    """Wait until MySQL is ready, then create the table if it does not exist."""
    for attempt in range(1, retries + 1):
        try:
            with get_conn() as conn, conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS students (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        roll_no VARCHAR(30) NOT NULL,
                        course VARCHAR(100) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
            print("Database is ready.", flush=True)
            return
        except pymysql.err.OperationalError as err:
            print(f"Waiting for database ({attempt}/{retries}): {err}", flush=True)
            time.sleep(delay)
    raise RuntimeError("Could not connect to the database.")


PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ label }}</title>
  <style>
    body { font-family: system-ui, Arial, sans-serif; background:#f4f6f9; margin:0; color:#1f2937; }
    .wrap { max-width: 820px; margin: 32px auto; padding: 0 16px; }
    .card { background:#fff; border-radius:10px; padding:20px 24px; box-shadow:0 1px 4px rgba(0,0,0,.08); margin-bottom:20px; }
    h1 { margin:0 0 4px; font-size:24px; }
    .meta { color:#6b7280; font-size:13px; }
    form { display:flex; gap:8px; flex-wrap:wrap; }
    input { flex:1 1 160px; padding:9px 10px; border:1px solid #d1d5db; border-radius:6px; }
    button { padding:9px 16px; border:0; border-radius:6px; background:#2563eb; color:#fff; cursor:pointer; }
    button.del { background:#dc2626; padding:5px 10px; font-size:12px; }
    table { width:100%; border-collapse:collapse; }
    th, td { text-align:left; padding:9px 6px; border-bottom:1px solid #e5e7eb; font-size:14px; }
    th { color:#6b7280; font-weight:600; }
    .ok { color:#16a34a; font-weight:600; }
  </style>
</head>
<body>
<div class="wrap">
  <div class="card">
    <h1>{{ label }}</h1>
    <div class="meta">
      Container: {{ host }} &middot; Database: {{ db_host }}/{{ db_name }}
      &middot; <span class="ok">DB connected</span> &middot; Records: {{ students|length }}
    </div>
  </div>

  <div class="card">
    <h3>Add a student</h3>
    <form method="post" action="{{ url_for('add') }}">
      <input name="name" placeholder="Full name" required>
      <input name="roll_no" placeholder="Roll no (e.g. FA23-BDS-048)" required>
      <input name="course" placeholder="Course" required>
      <button type="submit">Save</button>
    </form>
  </div>

  <div class="card">
    <h3>Saved records (stored in MySQL)</h3>
    {% if students %}
    <table>
      <tr><th>#</th><th>Name</th><th>Roll no</th><th>Course</th><th>Added</th><th></th></tr>
      {% for s in students %}
      <tr>
        <td>{{ s.id }}</td><td>{{ s.name }}</td><td>{{ s.roll_no }}</td><td>{{ s.course }}</td>
        <td>{{ s.created_at }}</td>
        <td>
          <form method="post" action="{{ url_for('delete', sid=s.id) }}">
            <button class="del" type="submit">Delete</button>
          </form>
        </td>
      </tr>
      {% endfor %}
    </table>
    {% else %}
    <p class="meta">No records yet. Add one above.</p>
    {% endif %}
  </div>
</div>
</body>
</html>
"""


@app.route("/")
def index():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM students ORDER BY id DESC")
        students = cur.fetchall()
    return render_template_string(
        PAGE,
        label=APP_LABEL,
        students=students,
        host=socket.gethostname(),
        db_host=DB_CONFIG["host"],
        db_name=DB_CONFIG["database"],
    )


@app.route("/add", methods=["POST"])
def add():
    name = request.form.get("name", "").strip()
    roll_no = request.form.get("roll_no", "").strip()
    course = request.form.get("course", "").strip()
    if name and roll_no and course:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO students (name, roll_no, course) VALUES (%s, %s, %s)",
                (name, roll_no, course),
            )
    return redirect(url_for("index"))


@app.route("/delete/<int:sid>", methods=["POST"])
def delete(sid):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM students WHERE id = %s", (sid,))
    return redirect(url_for("index"))


@app.route("/health")
def health():
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM students")
            count = cur.fetchone()["n"]
        return jsonify(status="ok", database="connected", records=count, label=APP_LABEL)
    except Exception as err:  # noqa: BLE001
        return jsonify(status="error", database=str(err)), 500


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
