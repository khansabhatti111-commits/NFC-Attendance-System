# NFC Attendance System

A web-based student attendance management system developed using Python, Flask, MySQL, HTML, and CSS.

## Features

- NFC card-based attendance
- Manual attendance marking
- Duplicate attendance prevention
- Student registration
- NFC card registration
- Attendance records
- Search attendance by student ID, name, or course
- Attendance filtering by date
- Admin login
- Admin dashboard
- Student management
- Responsive user interface

## Technologies Used

- Python
- Flask
- MySQL
- HTML
- CSS
- Git
- GitHub

## How It Works

1. Students are registered with their Student ID, name, and NFC Card ID.
2. The NFC card is scanned to identify the student.
3. The system checks whether attendance has already been marked for that student and course on the same day.
4. If attendance has not been marked, the system records the date and time.
5. Administrators can view attendance records and student information through the dashboard.

## Project Structure

```text
NFC-Attendance-System
│
├── app.py
├── requirements.txt
├── .gitignore
│
├── templates
│   ├── index.html
│   ├── login.html
│   ├── dashboard.html
│   ├── nfc_scan.html
│   ├── register_student.html
│   ├── attendance.html
│   └── students.html
│
└── static
    └── style.css