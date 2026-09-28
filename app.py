from flask import Flask, render_template, request, session, redirect, url_for
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = "nfc_attendance_secret_key"

# Connect Flask with MySQL
db = mysql.connector.connect(
    host=os.getenv("MYSQL_HOST"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DATABASE")
)


# Home Page
@app.route("/")
def home():
    return render_template("index.html")


# Mark Attendance
@app.route("/mark-attendance", methods=["POST"])
def mark_attendance():

    student_id = request.form["student_id"]
    student_name = request.form["student_name"]
    course_code = request.form["course_code"]

    # Buffered cursor
    cursor = db.cursor(buffered=True)

    # Add student
    # If student already exists, update the name
    cursor.execute(
        "INSERT INTO students (student_id, student_name) VALUES (%s, %s) "
        "ON DUPLICATE KEY UPDATE student_name = %s",
        (student_id, student_name, student_name)
    )

    # Check whether attendance is already marked today
    cursor.execute(
        "SELECT * FROM attendance "
        "WHERE student_id = %s "
        "AND course_code = %s "
        "AND attendance_date = CURDATE()",
        (student_id, course_code)
    )

    existing_attendance = cursor.fetchone()

    # Already marked
    if existing_attendance:
        cursor.close()

        return render_template(
            "already_marked.html",
            student_id=student_id,
            student_name=student_name,
            course_code=course_code
        )

    # Mark new attendance
    cursor.execute(
        "INSERT INTO attendance "
        "(student_id, course_code, attendance_date, attendance_time) "
        "VALUES (%s, %s, CURDATE(), CURTIME())",
        (student_id, course_code)
    )

    db.commit()

    cursor.close()

    return render_template(
        "success.html",
        student_id=student_id,
        student_name=student_name,
        course_code=course_code
    )

# NFC Scan
@app.route("/nfc-scan", methods=["GET", "POST"])
def nfc_scan():

    if request.method == "GET":
        return render_template("nfc_scan.html")

    nfc_card_id = request.form["nfc_card_id"]
    course_code = request.form["course_code"]

    cursor = db.cursor(buffered=True, dictionary=True)

    # Find student using NFC Card ID
    cursor.execute(
        "SELECT student_id, student_name "
        "FROM students "
        "WHERE nfc_card_id = %s",
        (nfc_card_id,)
    )

    student = cursor.fetchone()

    # If NFC card is not registered
    if not student:
        cursor.close()

        return "NFC Card not registered."

    student_id = student["student_id"]
    student_name = student["student_name"]

    # Check if attendance is already marked today
    cursor.execute(
        "SELECT * FROM attendance "
        "WHERE student_id = %s "
        "AND course_code = %s "
        "AND attendance_date = CURDATE()",
        (student_id, course_code)
    )

    existing_attendance = cursor.fetchone()

    if existing_attendance:
        cursor.close()

        return render_template(
            "already_marked.html",
            student_id=student_id,
            student_name=student_name,
            course_code=course_code
        )

    # Mark attendance
    cursor.execute(
        "INSERT INTO attendance "
        "(student_id, course_code, attendance_date, attendance_time) "
        "VALUES (%s, %s, CURDATE(), CURTIME())",
        (student_id, course_code)
    )

    db.commit()

    cursor.close()

    return render_template(
        "success.html",
        student_id=student_id,
        student_name=student_name,
        course_code=course_code
    )
    # Register Student
@app.route("/register-student", methods=["GET", "POST"])
def register_student():

    if request.method == "GET":
        return render_template("register_student.html")

    student_id = request.form["student_id"]
    student_name = request.form["student_name"]
    nfc_card_id = request.form["nfc_card_id"]

    cursor = db.cursor(buffered=True)

    # Check if student ID already exists
    cursor.execute(
        "SELECT * FROM students WHERE student_id = %s",
        (student_id,)
    )

    existing_student = cursor.fetchone()

    if existing_student:
        cursor.close()
        return "Student ID already registered."

    # Check if NFC card already exists
    cursor.execute(
        "SELECT * FROM students WHERE nfc_card_id = %s",
        (nfc_card_id,)
    )

    existing_card = cursor.fetchone()

    if existing_card:
        cursor.close()
        return "NFC Card ID already assigned to another student."

        # Add new student
    cursor.execute(
        "INSERT INTO students "
        "(student_id, student_name, nfc_card_id) "
        "VALUES (%s, %s, %s)",
        (student_id, student_name, nfc_card_id)
    )

    db.commit()

    cursor.close()

    return render_template(
        "registration_success.html",
        student_id=student_id,
        student_name=student_name,
        nfc_card_id=nfc_card_id
    )

# Admin Login
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        return render_template("login.html")

    username = request.form["username"]
    password = request.form["password"]

    if username == os.getenv("ADMIN_USERNAME") and password == os.getenv("ADMIN_PASSWORD"):

        session["admin_logged_in"] = True

        return redirect(url_for("dashboard"))

    return "Invalid username or password."
    # Admin Logout
@app.route("/logout")
def logout():

    session.pop("admin_logged_in", None)

    return redirect(url_for("login"))
# Admin Dashboard
@app.route("/dashboard")
def dashboard():

    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))



    cursor = db.cursor(buffered=True, dictionary=True)

    # Count total students
    cursor.execute(
        "SELECT COUNT(*) AS total_students FROM students"
    )

    total_students = cursor.fetchone()["total_students"]

    # Count all attendance records
    cursor.execute(
        "SELECT COUNT(*) AS total_attendance FROM attendance"
    )

    total_attendance = cursor.fetchone()["total_attendance"]

    # Count today's attendance
    cursor.execute(
        "SELECT COUNT(*) AS today_attendance "
        "FROM attendance "
        "WHERE attendance_date = CURDATE()"
    )

    today_attendance = cursor.fetchone()["today_attendance"]
    # Calculate today's attendance rate
    if total_students > 0:
        attendance_rate = (today_attendance / total_students) * 100
    else:
        attendance_rate = 0
    # Get recent attendance records
    cursor.execute("""
        SELECT
            attendance.student_id,
            students.student_name,
            attendance.course_code,
            attendance.attendance_date,
            attendance.attendance_time,
            attendance.status
        FROM attendance
        JOIN students
        ON attendance.student_id = students.student_id
        ORDER BY attendance.attendance_id DESC
        LIMIT 10
    """)

    recent_records = cursor.fetchall()

    cursor.close()
    return render_template(
        "dashboard.html",
        total_students=total_students,
        total_attendance=total_attendance,
        today_attendance=today_attendance,
        attendance_rate=attendance_rate,
        recent_records=recent_records
    )
# Attendance Records
@app.route("/attendance")
def attendance():

    search = request.args.get("search", "")
    selected_date = request.args.get("date", "")

    cursor = db.cursor(buffered=True, dictionary=True)

    query = """
        SELECT 
            attendance.attendance_id,
            attendance.student_id,
            students.student_name,
            attendance.course_code,
            attendance.attendance_date,
            attendance.attendance_time,
            attendance.status
        FROM attendance
        JOIN students
        ON attendance.student_id = students.student_id
        WHERE (
            attendance.student_id LIKE %s
            OR students.student_name LIKE %s
            OR attendance.course_code LIKE %s
        )
    """

    parameters = [
        "%" + search + "%",
        "%" + search + "%",
        "%" + search + "%"
    ]

    if selected_date:
        query += " AND attendance.attendance_date = %s"
        parameters.append(selected_date)

    query += " ORDER BY attendance.attendance_id DESC"

    cursor.execute(query, parameters)

    records = cursor.fetchall()

    cursor.close()

    return render_template(
        "attendance.html",
        records=records,
        search=search,
        selected_date=selected_date
    )

# Student List
@app.route("/students")
def students():

    search = request.args.get("search", "")

    cursor = db.cursor(buffered=True, dictionary=True)

    cursor.execute("""
        SELECT student_id, student_name, nfc_card_id
        FROM students
        WHERE student_id LIKE %s
        OR student_name LIKE %s
        OR nfc_card_id LIKE %s
        ORDER BY student_id
    """, (
        "%" + search + "%",
        "%" + search + "%",
        "%" + search + "%"
    ))

    students = cursor.fetchall()

    cursor.close()

    return render_template(
        "students.html",
        students=students,
        search=search
    )



# Run Flask
if __name__ == "__main__":
    app.run(debug=True)