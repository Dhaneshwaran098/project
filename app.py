from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session
import sqlite3
import os
from werkzeug.utils import secure_filename

# ---------------- APP SETUP ----------------
app = Flask(__name__)
app.secret_key = "secret"

UPLOAD_FOLDER = "uploads/permissions"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ---------------- DATABASE ----------------
def get_db():
    return sqlite3.connect("database.db")

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS leave_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT,
            reason TEXT,
            permission_file TEXT,
            attendance INTEGER,
            instructor_status TEXT DEFAULT 'Pending',
            hod_status TEXT DEFAULT 'Pending'
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        role = request.form.get("role")

        session["username"] = username
        session["role"] = role

        if role == "student":
            return redirect(url_for("student"))
        elif role == "instructor":
            return redirect(url_for("instructor"))
        elif role == "hod":
            return redirect(url_for("hod"))

    return render_template("login.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------------- STUDENT ----------------
@app.route("/student", methods=["GET", "POST"])
def student():
    if "username" not in session or session["role"] != "student":
        return redirect(url_for("login"))

    student_name = session["username"]

    if request.method == "POST":
        reason = request.form.get("reason")
        attendance = request.form.get("attendance")
        file = request.files.get("file")

        filename = None
        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO leave_requests
            (student_name, reason, permission_file, attendance)
            VALUES (?, ?, ?, ?)
        """, (student_name, reason, filename, attendance))
        conn.commit()
        conn.close()

        return redirect(url_for("student"))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM leave_requests WHERE student_name=?", (student_name,))
    data = cur.fetchall()
    conn.close()

    return render_template("student_dashboard.html", data=data)

# ---------------- INSTRUCTOR ----------------
@app.route("/instructor", methods=["GET", "POST"])
def instructor():
    if "username" not in session or session["role"] != "instructor":
        return redirect(url_for("login"))

    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        request_id = request.form.get("id")
        status = request.form.get("status")
        cur.execute(
            "UPDATE leave_requests SET instructor_status=? WHERE id=?",
            (status, request_id)
        )
        conn.commit()

    cur.execute("SELECT * FROM leave_requests WHERE instructor_status='Pending'")
    pending = cur.fetchall()

    cur.execute("SELECT * FROM leave_requests WHERE instructor_status!='Pending'")
    history = cur.fetchall()

    conn.close()

    return render_template(
        "instructor_dashboard.html",
        pending=pending,
        history=history
    )

# ---------------- HOD ----------------
@app.route("/hod", methods=["GET", "POST"])
def hod():
    if "username" not in session or session["role"] != "hod":
        return redirect(url_for("login"))

    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        request_id = request.form.get("id")
        status = request.form.get("status")
        cur.execute(
            "UPDATE leave_requests SET hod_status=? WHERE id=?",
            (status, request_id)
        )
        conn.commit()

    cur.execute("SELECT * FROM leave_requests WHERE hod_status='Pending'")
    pending = cur.fetchall()

    cur.execute("SELECT * FROM leave_requests WHERE hod_status!='Pending'")
    history = cur.fetchall()

    conn.close()

    return render_template(
        "hod_dashboard.html",
        pending=pending,
        history=history
    )

# ---------------- DELETE HISTORY ----------------
@app.route("/delete_history/<role>", methods=["POST"])
def delete_history(role):
    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cur = conn.cursor()

    if role == "student":
        cur.execute(
            "DELETE FROM leave_requests WHERE student_name=?",
            (session["username"],)
        )
    elif role == "instructor":
        cur.execute(
            "DELETE FROM leave_requests WHERE instructor_status!='Pending'"
        )
    elif role == "hod":
        cur.execute(
            "DELETE FROM leave_requests WHERE hod_status!='Pending'"
        )

    conn.commit()
    conn.close()

    return redirect(request.referrer)

# ---------------- FILE VIEW ----------------
@app.route("/uploads/permissions/<filename>")
def view_permission(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True, port=5001)
