import os, re, io, calendar
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from functools import wraps

import fitz
import numpy as np
import pandas as pd
import pymysql
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sklearn.ensemble import IsolationForest, RandomForestRegressor

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "development-key-change-me")
ALLOWED_EXTENSIONS = {"pdf", "csv"}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

def db():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "finance_monitor"),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False
    )

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def normalize_amount(value):
    if pd.isna(value):
        return None
    s = str(value).strip().replace(",", "").replace("₹", "").replace("$", "")
    if not s:
        return None
    negative = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    try:
        n = Decimal(s)
        return -abs(n) if negative else n
    except InvalidOperation:
        return None

def categorize(description, txn_type):
    d = (description or "").lower()
    if txn_type == "income" and any(x in d for x in ["salary", "payroll", "wage"]):
        return "Salary"
    rules = {
        "Food": ["restaurant", "swiggy", "zomato", "grocery", "supermarket", "cafe", "food"],
        "Shopping": ["amazon", "flipkart", "mall", "shopping", "retail"],
        "Transportation": ["uber", "ola", "fuel", "petrol", "metro", "bus", "rail", "transport"],
        "Healthcare": ["hospital", "pharmacy", "medical", "clinic", "health"],
        "Education": ["school", "college", "university", "course", "books", "tuition"],
        "Entertainment": ["movie", "netflix", "spotify", "cinema", "game"],
        "Bills": ["electricity", "water bill", "internet", "broadband", "mobile", "recharge", "emi", "rent"]
    }
    for category, words in rules.items():
        if any(word in d for word in words):
            return category
    return "Other" if txn_type == "expense" else "Other"

def parse_date(value):
    if pd.isna(value):
        return None
    if isinstance(value, (datetime, date, pd.Timestamp)):
        return value.date() if hasattr(value, "date") else value
    for dayfirst in (True, False):
        try:
            return pd.to_datetime(str(value), dayfirst=dayfirst, errors="raise").date()
        except Exception:
            pass
    return None

def rows_from_csv(raw):
    df = pd.read_csv(io.BytesIO(raw))
    if df.empty:
        return []
    # Flexible header matching. Preferred: Date, Description, Debit, Credit.
    cols = {str(c).strip().lower(): c for c in df.columns}
    def find(*names):
        for name in names:
            if name in cols:
                return cols[name]
        return None
    date_col = find("date", "transaction date", "txn date", "value date")
    desc_col = find("description", "narration", "particulars", "details", "transaction details")
    debit_col = find("debit", "withdrawal", "withdrawal amt", "debit amount")
    credit_col = find("credit", "deposit", "deposit amt", "credit amount")
    amount_col = find("amount", "transaction amount", "txn amount")
    type_col = find("type", "transaction type", "dr/cr")
    if not date_col or not desc_col or not (amount_col or debit_col or credit_col):
        raise ValueError("CSV needs Date, Description/Narration and Amount or Debit/Credit columns.")
    rows = []
    for _, r in df.iterrows():
        dt = parse_date(r[date_col])
        if not dt:
            continue
        desc = str(r[desc_col])[:500]
        if amount_col:
            amt = normalize_amount(r[amount_col])
            typetext = str(r[type_col]).lower() if type_col else ""
            is_credit = typetext in ("cr", "credit", "deposit") or (amt is not None and amt > 0)
            if amt is None or amt == 0:
                continue
            txn_type = "income" if is_credit else "expense"
            amount = abs(amt)
        else:
            debit = normalize_amount(r[debit_col]) if debit_col else None
            credit = normalize_amount(r[credit_col]) if credit_col else None
            if credit and credit != 0:
                txn_type, amount = "income", abs(credit)
            elif debit and debit != 0:
                txn_type, amount = "expense", abs(debit)
            else:
                continue
        rows.append({"date": dt, "description": desc, "amount": amount,
                     "type": txn_type, "category": categorize(desc, txn_type)})
    return rows

def rows_from_pdf(raw):
    doc = fitz.open(stream=raw, filetype="pdf")
    text = "\n".join(page.get_text() for page in doc)
    # Generic line parser: date + description + amount. PDF layouts vary by bank.
    rows = []
    date_re = re.compile(r"^(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+(.+?)\s+(-?\(?[\d,]+\.\d{2}\)?)$")
    for line in text.splitlines():
        line = " ".join(line.split())
        m = date_re.match(line)
        if not m:
            continue
        dt = parse_date(m.group(1))
        amt = normalize_amount(m.group(3))
        if not dt or amt is None or amt == 0:
            continue
        desc = m.group(2)[:500]
        # In generic PDF extraction, signed amounts determine direction.
        txn_type = "income" if amt > 0 else "expense"
        rows.append({"date": dt, "description": desc, "amount": abs(amt),
                     "type": txn_type, "category": categorize(desc, txn_type)})
    if not rows:
        raise ValueError("No transactions could be recognized in this PDF. PDF layouts differ by bank; export it as CSV and upload that file.")
    return rows

def financial_score(income, expenses, txn_count):
    if income <= 0:
        return 0
    savings_rate = max(0, (income - expenses) / income)
    expense_ratio = expenses / income
    score = 40 + min(35, savings_rate * 100 * 0.7) + (15 if expense_ratio <= 0.8 else 0) + (10 if txn_count > 0 else 0)
    return int(max(0, min(100, round(score))))

def ml_insights(transactions):
    # Transaction-level outlier flagging; requires enough records to be meaningful.
    expenses = [t for t in transactions if t["txn_type"] == "expense"]
    if len(expenses) < 8:
        return set()
    X = np.array([[float(t["amount"]), len(t["description"]), t["txn_date"].day,
                   t["txn_date"].month] for t in expenses])
    model = IsolationForest(contamination=0.08, random_state=42)
    labels = model.fit_predict(X)
    return {t["id"] for t, label in zip(expenses, labels) if label == -1 and t.get("id")}

def predict_next_month(monthly_expenses):
    values = [float(x) for x in monthly_expenses]
    if not values:
        return 0.0, "No expense history available yet."
    if len(values) < 4:
        return round(float(np.mean(values)), 2), "Baseline estimate using the average of available months; add more history for ML predictions."
    X = np.arange(len(values)).reshape(-1, 1)
    y = np.array(values)
    model = RandomForestRegressor(n_estimators=120, random_state=42, max_depth=3)
    model.fit(X, y)
    pred = max(0, float(model.predict([[len(values)]])[0]))
    return round(pred, 2), "Random Forest estimate based on monthly expense history."

def fetch_transactions(user_id):
    conn = db()
    try:
        with conn.cursor() as cur:
            cur.execute("""SELECT id, txn_date, description, amount, txn_type, category, is_anomaly
                           FROM transactions WHERE user_id=%s ORDER BY txn_date DESC, id DESC""", (user_id,))
            return cur.fetchall()
    finally:
        conn.close()

@app.route("/")
def home():
    return redirect(url_for("dashboard") if "user_id" in session else url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 8:
            flash("Enter your name, a valid email and a password of at least 8 characters.", "error")
            return render_template("register.html")
        conn = db()
        try:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO users(name,email,password_hash) VALUES(%s,%s,%s)",
                            (name, email, generate_password_hash(password)))
            conn.commit()
            flash("Account created. Please sign in.", "success")
            return redirect(url_for("login"))
        except pymysql.err.IntegrityError:
            conn.rollback()
            flash("That email is already registered.", "error")
        finally:
            conn.close()
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        conn = db()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE email=%s", (email,))
                user = cur.fetchone()
        finally:
            conn.close()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return redirect(url_for("dashboard"))
        flash("Incorrect email or password.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    txns = fetch_transactions(session["user_id"])
    income = sum(float(t["amount"]) for t in txns if t["txn_type"] == "income")
    expenses = sum(float(t["amount"]) for t in txns if t["txn_type"] == "expense")
    savings = income - expenses
    score = financial_score(income, expenses, len(txns))
    category_totals = {}
    monthly = {}
    for t in txns:
        if t["txn_type"] == "expense":
            category_totals[t["category"]] = category_totals.get(t["category"], 0) + float(t["amount"])
            key = t["txn_date"].strftime("%Y-%m")
            monthly[key] = monthly.get(key, 0) + float(t["amount"])
    sorted_months = sorted(monthly.items())[-12:]
    prediction, prediction_note = predict_next_month([v for _, v in sorted_months])
    recommendations = []
    if income and expenses / income > .8:
        recommendations.append("Your expenses are above 80% of recorded income. Review recurring and discretionary costs.")
    if income and savings / income < .2:
        recommendations.append("Consider setting a realistic savings target and reviewing non-essential spending.")
    if not recommendations:
        recommendations.append("Keep tracking transactions monthly and maintain an emergency savings buffer.")
    labels = [m for m, _ in sorted_months]
    values = [round(v, 2) for _, v in sorted_months]
    return render_template("dashboard.html", name=session.get("user_name"), income=income,
        expenses=expenses, savings=savings, score=score, tx_count=len(txns),
        categories=category_totals, month_labels=labels, month_values=values,
        prediction=prediction, prediction_note=prediction_note,
        recommendations=recommendations, recent=txns[:8])

@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        f = request.files.get("statement")
        if not f or not f.filename or not allowed_file(f.filename):
            flash("Choose a PDF or CSV bank statement.", "error")
            return redirect(url_for("upload"))
        raw = f.read()
        if not raw:
            flash("The uploaded file is empty.", "error")
            return redirect(url_for("upload"))
        ext = f.filename.rsplit(".", 1)[1].lower()
        try:
            rows = rows_from_csv(raw) if ext == "csv" else rows_from_pdf(raw)
            if not rows:
                raise ValueError("No valid transactions were found.")
            conn = db()
            try:
                with conn.cursor() as cur:
                    cur.execute("""INSERT INTO statements(user_id,original_filename,file_type,transaction_count)
                                   VALUES(%s,%s,%s,%s)""",
                                (session["user_id"], secure_filename(f.filename), ext, len(rows)))
                    statement_id = cur.lastrowid
                    for r in rows:
                        cur.execute("""INSERT INTO transactions
                            (user_id,statement_id,txn_date,description,amount,txn_type,category)
                            VALUES(%s,%s,%s,%s,%s,%s,%s)""",
                            (session["user_id"], statement_id, r["date"], r["description"],
                             str(r["amount"]), r["type"], r["category"]))
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
            flash(f"Imported {len(rows)} transactions successfully.", "success")
            return redirect(url_for("dashboard"))
        except Exception as e:
            flash(str(e), "error")
    return render_template("upload.html")

@app.route("/transactions")
@login_required
def transactions():
    txns = fetch_transactions(session["user_id"])
    # Mark likely anomalies for the current user's data.
    anomaly_ids = ml_insights(txns)
    if anomaly_ids:
        conn = db()
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE transactions SET is_anomaly=0 WHERE user_id=%s", (session["user_id"],))
                cur.executemany("UPDATE transactions SET is_anomaly=1 WHERE id=%s",
                                [(i,) for i in anomaly_ids])
            conn.commit()
        finally:
            conn.close()
        for t in txns:
            t["is_anomaly"] = t["id"] in anomaly_ids
    return render_template("transactions.html", transactions=txns)

@app.route("/health")
@login_required
def health():
    txns = fetch_transactions(session["user_id"])
    income = sum(float(t["amount"]) for t in txns if t["txn_type"] == "income")
    expenses = sum(float(t["amount"]) for t in txns if t["txn_type"] == "expense")
    savings = income - expenses
    score = financial_score(income, expenses, len(txns))
    ratio = (savings / income * 100) if income else 0
    return render_template("health.html", income=income, expenses=expenses,
                           savings=savings, score=score, ratio=ratio, count=len(txns))

@app.errorhandler(413)
def too_large(_):
    flash("File is too large. Maximum upload size is 10 MB.", "error")
    return redirect(url_for("upload"))

if __name__ == "__main__":
    app.run(debug=True)
