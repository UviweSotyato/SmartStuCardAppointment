from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db_config import get_db_connection

bp = Blueprint('student_login', __name__)  # Unique name


from flask_login import login_user, logout_user, current_user, login_required, LoginManager, UserMixin
from app import login_manager
import db_config

class User(UserMixin):
    def __init__(self, id, student_number):
        self.id = id
        self.StudentNumber = student_number

@login_manager.user_loader
def load_user(user_id):
    connection = db_config.get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Students WHERE id = %s", (user_id,))
    user_data = cursor.fetchone()
    connection.close()
    if user_data:
        return User(user_data['id'], user_data['StudentNumber'])
    return None


# Route for the main page or homepage
@bp.route('/')
def main_home():
    return render_template("MainHomePage.html")

# Student login route
@bp.route('/Studlogin', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        student_number = request.form.get('student_number')

        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM Students WHERE StudentNumber = %s", (student_number,))
            student = cursor.fetchone()

            if student:
                session['logged_in'] = True
                session['student_number'] = student['StudentNumber']  # clearer key name
                return redirect(url_for('student_login.student_dashboard'))
            else:
                flash("Invalid student number", 'error')
            cursor.close()
            connection.close()
        else:
            flash("Database connection error", 'error')

    return render_template("StudentLoginPage.html")

# Student dashboard route
@bp.route('/student_dashboard')
def student_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('student_login.student_login'))
    
    student_number = session.get('student_number')

    connection = get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM Students WHERE StudentNumber = %s", (student_number,))
        student = cursor.fetchone()
        
        cursor.execute("""
            SELECT AppointmentDate, CollectionDate, CollectionTime, AppointmentStatus
            FROM Appointments
            WHERE StudentNumber = %s
        """, (student_number,))
        appointments = cursor.fetchall()

        cursor.close()
        connection.close()

        return render_template("Student_Dashboard.html", student=student, appointments=appointments)

    flash("Database connection error", 'error')
    return redirect(url_for('student_login.student_login'))

# Route for booking an appointment
@bp.route('/book_appointment/<student_number>', methods=['GET', 'POST'])
def book_appointment(student_number):
    if request.method == 'POST':
        appointment_date = request.form.get('appointment_date')
        collection_date = request.form.get('collection_date')
        collection_time = request.form.get('collection_time')

        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO Appointments (StudentNumber, AppointmentDate, CollectionDate, CollectionTime, AppointmentStatus)
                VALUES (%s, %s, %s, %s, 'Scheduled')
            """, (student_number, appointment_date, collection_date, collection_time))
            connection.commit()
            cursor.close()
            connection.close()
            flash("Appointment booked successfully!", 'success')
            return redirect(url_for('student_login.student_dashboard'))

        flash("Database connection error", 'error')
        return redirect(url_for('student_login.student_dashboard'))

    return render_template("BookAppointment.html", student_number=student_number)
