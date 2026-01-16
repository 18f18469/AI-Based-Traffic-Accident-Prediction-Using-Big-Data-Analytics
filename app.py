from flask import Flask, render_template, request, redirect, url_for, session, flash
from db import get_db
from ml import predict_risk, get_known_locations, get_known_days

app = Flask(__name__)
app.secret_key = "change-me-please"


# -----------------------------
# Language helper
# -----------------------------
def current_lang():
    return session.get("language", "ar")


# -----------------------------
# Translation dictionary
# -----------------------------
T = {
    "ar": {
        "title": "نظام التنبؤ بحوادث المرور",
        "project_title": "نظام التنبؤ بحوادث المرور باستخدام تحليل البيانات الضخمة",
        "login": "تسجيل الدخول",
        "username": "اسم المستخدم",
        "password": "كلمة المرور",
        "submit": "دخول",
        "logout": "تسجيل خروج",
        "predict": "تنفيذ التنبؤ",
        "day": "اليوم",
        "hour": "الساعة",
        "injuries": "عدد الإصابات",
        "location": "الموقع / الشارع",
        "result": "نتيجة التنبؤ",
        "risk_score": "مستوى الخطورة",
        "risk_level": "تصنيف الخطورة",
        "admin_panel": "لوحة الأدمن",
        "history": "سجل التنبؤات",
        "bad_login": "اسم المستخدم أو كلمة المرور غير صحيحة",
    },
    "en": {
        "title": "Traffic Accident Prediction System",
        "project_title": "AI-Based Traffic Accident Prediction Using Big Data Analytics",
        "login": "Login",
        "username": "Username",
        "password": "Password",
        "submit": "Sign in",
        "logout": "Logout",
        "predict": "Run Prediction",
        "day": "Day",
        "hour": "Hour",
        "injuries": "Injuries",
        "location": "Location / Road",
        "result": "Prediction Result",
        "risk_score": "Risk Score",
        "risk_level": "Risk Level",
        "admin_panel": "Admin Panel",
        "history": "Prediction History",
        "bad_login": "Invalid username or password",
    }
}


# -----------------------------
# Change language
# -----------------------------
@app.route("/lang/<code>")
def set_lang(code):
    if code not in ["ar", "en"]:
        code = "ar"
    session["language"] = code
    return redirect(request.referrer or url_for("index"))


# -----------------------------
# Login
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    lang = current_lang()

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (username, password)
        )
        user = cur.fetchone()
        cur.close()
        db.close()

        if not user:
            flash(T[lang]["bad_login"], "danger")
            return redirect(url_for("login"))

        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role"] = user["role"]
        session["language"] = user.get("language", lang)

        return redirect(url_for("index"))

    return render_template("login.html", t=T[lang], lang=lang)


# -----------------------------
# Logout
# -----------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# -----------------------------
# Auth helper
# -----------------------------
def require_login():
    return "user_id" in session


# -----------------------------
# Main page (Dashboard + Prediction)
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    if not require_login():
        return redirect(url_for("login"))

    lang = current_lang()
    days = get_known_days()
    locations = get_known_locations()

    risk_score = None
    risk_level = None

    # ----- Prediction -----
    if request.method == "POST":
        day = request.form.get("day")
        hour = int(request.form.get("hour"))
        injuries = int(request.form.get("injuries"))
        location = request.form.get("location")

        risk_score, risk_level = predict_risk(day, hour, injuries, location)

        # Save prediction
        db = get_db()
        cur = db.cursor()
        cur.execute(
            """
            INSERT INTO predictions
            (user_id, day, hour, injuries, location, prediction_result)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                session["user_id"],
                day,
                hour,
                injuries,
                location,
                f"{risk_score}% ({risk_level})"
            )
        )
        db.commit()
        cur.close()
        db.close()

    # ----- History -----
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute(
        """
        SELECT * FROM predictions
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 50
        """,
        (session["user_id"],)
    )
    history = cur.fetchall()
    cur.close()
    db.close()

    # ----- Risk statistics (Dashboard & Pie Chart) -----
    low = medium = high = 0
    for r in history:
        pr = r["prediction_result"]
        if pr and "Low" in pr:
            low += 1
        elif pr and "Medium" in pr:
            medium += 1
        elif pr and "High" in pr:
            high += 1

    risk_stats = {
        "low": low,
        "medium": medium,
        "high": high,
        "total": low + medium + high
    }

    return render_template(
        "index.html",
        t=T[lang],
        lang=lang,
        days=days,
        locations=locations,
        risk_score=risk_score,
        risk_level=risk_level,
        history=history,
        risk_stats=risk_stats,
        user=session.get("username"),
        role=session.get("role"),
    )


# -----------------------------
# Admin page
# -----------------------------
@app.route("/admin")
def admin():
    if not require_login():
        return redirect(url_for("login"))
    if session.get("role") != "admin":
        return redirect(url_for("index"))

    lang = current_lang()

    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute(
        """
        SELECT p.*, u.username
        FROM predictions p
        JOIN users u ON u.id = p.user_id
        ORDER BY p.created_at DESC
        LIMIT 200
        """
    )
    rows = cur.fetchall()
    cur.close()
    db.close()

    return render_template(
        "admin.html",
        t=T[lang],
        lang=lang,
        rows=rows,
        user=session.get("username")
    )


# -----------------------------
# Run app
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
