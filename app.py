import os, csv
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
from datetime import datetime, timedelta
from bcrypt import hashpw, gensalt, checkpw
from io import StringIO

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Database initialization
DATABASE = "database/FireDepot.db"

def init_db():
    """Initializes the database and creates required tables."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            forename TEXT NOT NULL,
            surname TEXT NOT NULL,
            basePay REAL NOT NULL,
            location TEXT NOT NULL
        )
        """)

        # Callouts table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS callouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            userId INTEGER NOT NULL,
            date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            description TEXT NOT NULL,
            position TEXT NOT NULL,
            FOREIGN KEY(userId) REFERENCES users(id)
        )
        """)

        conn.commit()

def calculate_salary(start_time, end_time, basePay):
    """Calculates salary based on callout duration, accounting for day and night rates."""
    # Convert times to datetime objects
    start = datetime.strptime(start_time, "%H:%M")
    end = datetime.strptime(end_time, "%H:%M")

    # Adjust end time if it crosses midnight
    if end < start:
        end += timedelta(days=1)

    # Define daytime range (8 AM to 8 PM)
    day_start = datetime.strptime("08:00", "%H:%M")
    day_end = datetime.strptime("20:00", "%H:%M")

    # Calculate rates
    day_rate_min = (basePay / 2) / 60
    night_rate_min = (basePay * 2) / 60
    day_first_hour = basePay
    night_first_hour = basePay * 2

    # Initialize salary
    salary = 0

    # Handle time before first hour is over
    first_hour_end = start + timedelta(hours=1)
    first_hour_seconds = min((first_hour_end - start).total_seconds(), (end - start).total_seconds())
    first_hour_mins = int(first_hour_seconds // 60)

    if start >= day_start and start < day_end:
        # Daytime first hour
        salary += day_first_hour
        remaining_minutes = max(0, first_hour_mins - 60)
    else:
        # Nighttime first hour
        salary += night_first_hour
        remaining_minutes = max(0, first_hour_mins - 60)

    # Adjust the start time to calculate remaining time
    remaining_start = start + timedelta(minutes=first_hour_mins)

    # Process remaining minutes
    while remaining_start < end:
        # Determine if current time is day or night
        if day_start <= remaining_start < day_end:
            # Daytime rate
            next_boundary = min(day_end, end)
            period_seconds = (next_boundary - remaining_start).total_seconds()
            salary += (period_seconds // 60) * day_rate_min
        else:
            # Nighttime rate
            next_boundary = min(day_start + timedelta(days=1), end)
            period_seconds = (next_boundary - remaining_start).total_seconds()
            salary += (period_seconds // 60) * night_rate_min

        # Move to the next period
        remaining_start = next_boundary

    return round(salary, 2)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Handles user registration."""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]
        forename = request.form["forename"]
        surname = request.form["surname"]
        basePay = float(request.form["basePay"])
        location = request.form["location"]
        hashed_password = hashpw(password.encode('utf-8'), gensalt())

        try:
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO users (username, password, email, forename, surname, basePay, location)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (username, hashed_password, email, forename, surname, basePay, location))
                conn.commit()
                flash("Registration successful!", "success")
                return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username or email already exists. Try another one.", "danger")
            return redirect(url_for("register"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Handles user login."""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, password, forename, surname FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()

            if result:
                user_id, hashed_password_from_db, forename, surname = result

                if isinstance(hashed_password_from_db, str):
                    hashed_password_from_db = hashed_password_from_db.encode('utf-8')

                if checkpw(password.encode('utf-8'), hashed_password_from_db):
                    session["user_id"] = user_id
                    session["username"] = username
                    session["forename"] = forename
                    session["surname"] = surname
                    flash("Login successful!", "success")
                    return redirect(url_for("home"))
                else:
                    flash("Invalid username or password", "danger")
            else:
                flash("Invalid username or password", "danger")

    return render_template("login.html")

@app.route("/home")
def home():
    """Displays the home page with the callouts table."""
    if "user_id" not in session:
        flash("Please log in to access this page.", "warning")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    forename = session.get("forename")
    surname = session.get("surname")

    # Fetch callouts and calculate salaries
    callouts = []
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT c.id, c.date, c.start_time, c.end_time, c.description, c.position, u.basePay
        FROM callouts c
        JOIN users u ON c.userId = u.id
        WHERE c.userId = ?
        """, (user_id,))
        results = cursor.fetchall()

        for row in results:
            callout_id, date, start_time, end_time, description, position, basePay = row
            salary = calculate_salary(start_time, end_time, basePay)
            callouts.append({
                "id": callout_id,
                "date": date,
                "start_time": start_time,
                "end_time": end_time,
                "description": description,
                "position": position,
                "salary": salary
            })

    return render_template("home.html", forename=forename, surname=surname, callouts=callouts)

@app.route("/delete_callout/<int:callout_id>", methods=["POST"])
def delete_callout(callout_id):
    """Handles the deletion of a callout."""
    if "user_id" not in session:
        flash("Please log in to access this page.", "warning")
        return redirect(url_for("login"))

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM callouts WHERE id = ? AND userId = ?", (callout_id, session["user_id"]))
        conn.commit()

    flash("Callout deleted successfully.", "success")
    return redirect(url_for("home"))

@app.route("/edit_details", methods=["GET", "POST"])
def edit_details():
    """Allows users to edit their account details."""
    if "user_id" not in session:
        flash("Please log in to access this page.", "warning")
        return redirect(url_for("login"))

    user_id = session["user_id"]

    if request.method == "POST":
        email = request.form["email"]
        basePay = request.form["basePay"]

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET email = ?, basePay = ? WHERE id = ?", (email, basePay, user_id))
            conn.commit()
            flash("Your details have been updated successfully.", "success")
            return redirect(url_for("home"))

    # Fetch current user details
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT email, basePay FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()

    return render_template("edit_details.html", email=result[0], basePay=result[1])

@app.route("/add_callout", methods=["POST"])
def add_callout():
    """Handles the addition of a new callout."""
    if "user_id" not in session:
        flash("Please log in to access this page.", "warning")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    date = request.form["date"]
    start_time = request.form["start_time"]
    end_time = request.form["end_time"]
    description = request.form["description"]
    position = request.form["position"]

    if not description.strip():
        flash("Description is required.", "danger")
        return redirect(url_for("home"))

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO callouts (userId, date, start_time, end_time, description, position)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, date, start_time, end_time, description, position))
        conn.commit()

    flash("Callout added successfully!", "success")
    return redirect(url_for("home"))

@app.route("/logout")
def logout():
    """Logs out the user."""
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    """Handles the Forgot Password functionality."""
    if request.method == "POST":
        email = request.form["email"]

        # Simulate sending a reset email or token
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM users WHERE email = ?", (email,))
            result = cursor.fetchone()

            if result:
                flash(f"A password reset link has been sent to {email}.", "info")
                return redirect(url_for("login"))
            else:
                flash("No account found with that email address.", "danger")

    return render_template("forgot_password.html")

@app.route("/download_callouts", methods=["GET"])
def download_callouts():
    """Generates a CSV file with all callouts for the logged-in user."""
    if "user_id" not in session:
        flash("Please log in to access this feature.", "warning")
        return redirect(url_for("login"))

    user_id = session["user_id"]

    # Fetch callouts for the user
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT date, start_time, end_time, description, position
        FROM callouts
        WHERE userId = ?
        """, (user_id,))
        callouts = cursor.fetchall()

    # Create a CSV in-memory
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Start Time", "End Time", "Description", "Position"])  # CSV Header
    writer.writerows(callouts)

    # Prepare the response
    output.seek(0)
    response = Response(output, mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=callouts.csv"
    return response

if __name__ == "__main__":
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
