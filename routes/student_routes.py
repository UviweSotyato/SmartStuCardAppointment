# students.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
import base64
import db_config
from utils.face_detection import contains_face
from datetime import datetime, timedelta


students_bp = Blueprint('students', __name__, url_prefix='/students')

@students_bp.route('/')
def view_students():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    connection = db_config.get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Students")
        students = cursor.fetchall()
        connection.commit()
        connection.close()
        return render_template('ViewStudentsPage.html', students=students)
    else:
        return "Database connection failed"

@students_bp.route('/delete_student/<student_number>', methods=['POST'])
def delete_student(student_number):
    try:
        connection = db_config.get_db_connection()
        if connection:
            cursor = connection.cursor()

            # Delete related records in the notificationtable first
            cursor.execute("DELETE FROM notificationtable WHERE StudentNumber = %s", (student_number,))

            # Delete related records in the requesttable (if any)
            cursor.execute("DELETE FROM requesttable WHERE Appointment_Id IN (SELECT Appointment_Id FROM Appointments WHERE StudentNumber = %s)", (student_number,))

            # Delete related records in the appointmentstatus table (if any)
            cursor.execute("DELETE FROM appointmentstatus WHERE Appointment_Id IN (SELECT Appointment_Id FROM Appointments WHERE StudentNumber = %s)", (student_number,))

            # Delete related appointments (if foreign key constraints are not cascading)
            cursor.execute("DELETE FROM Appointments WHERE StudentNumber = %s", (student_number,))

            # Finally, delete the student record from the Students table
            cursor.execute("DELETE FROM Students WHERE StudentNumber = %s", (student_number,))

            # Commit the changes to the database
            connection.commit()
            connection.close()

            return redirect(url_for('students.view_students'))  # Redirect to the student view page after deletion

        else:
            return jsonify({"error": "Database connection failed"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@students_bp.route('/edit', methods=['GET', 'POST'])
def edit_student():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            student_number = request.form['student_number']
            new_residence = request.form['new_residence']
            connection = db_config.get_db_connection()
            if connection:
                cursor = connection.cursor()
                cursor.execute("UPDATE Students SET Residence = %s WHERE StudentNumber = %s", (new_residence, student_number))
                connection.commit()
                connection.close()
                flash("Residence updated successfully!", "success")
                return redirect(url_for('students.view_students'))
            else:
                flash("Database connection failed", "error")
                return redirect(url_for('students.view_students'))
        except Exception as e:
            flash(f"Error: {str(e)}", "error")
            return redirect(url_for('students.view_students'))

    student_number = request.args.get('student_number')
    if not student_number:
        return "Missing student number", 400

    connection = db_config.get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Students WHERE StudentNumber = %s", (student_number,))
        student = cursor.fetchone()
        connection.close()

        if student:
            return render_template('EditStudentPage.html', student=student)
        else:
            return "Student not found", 404
    else:
        return "Database connection failed", 500


@students_bp.route('/register', methods=['GET', 'POST'])
def register_student():
    if request.method == 'POST':
        studentNumber = request.form['studentNumber']
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        email = request.form['email']
        residence = request.form['residence']

        student_data = (
            studentNumber,
            firstName,
            lastName,
            email,
            residence
        )

        connection = db_config.get_db_connection()
        if connection:
            cursor = connection.cursor()
            try:
                # Insert new student
                cursor.execute("""
                    INSERT INTO Students (StudentNumber, FirstName, LastName, Email, Residence)
                    VALUES (%s, %s, %s, %s, %s)
                """, student_data)
                connection.commit()

                # Now automatically book appointment for this student

                now = datetime.now()
                appointment_date_str = now.strftime('%Y-%m-%d %H:%M:%S')
                appointment_date = now

                # Calculate initial collection date (2 weeks later)
                collection_date = appointment_date + timedelta(weeks=2)

                # Adjust if collection date falls on weekend
                if collection_date.weekday() == 5:  # Saturday
                    collection_date -= timedelta(days=1)
                elif collection_date.weekday() == 6:  # Sunday
                    collection_date += timedelta(days=1)

                # Count morning appointments (before 12)
                cursor.execute("""
                    SELECT COUNT(*) FROM Appointments 
                    WHERE DATE(CollectionDate) = %s AND TIME(CollectionTime) < '12:00:00'
                """, (collection_date.date(),))
                before_12_count = cursor.fetchone()[0]

                # Count afternoon appointments (12 and after)
                cursor.execute("""
                    SELECT COUNT(*) FROM Appointments 
                    WHERE DATE(CollectionDate) = %s AND TIME(CollectionTime) >= '12:00:00'
                """, (collection_date.date(),))
                after_12_count = cursor.fetchone()[0]

                # Assign time slot
                if before_12_count < 5:
                    collection_time = collection_date.replace(hour=10, minute=0, second=0)
                elif after_12_count < 5:
                    collection_time = collection_date.replace(hour=14, minute=0, second=0)
                else:
                    # Find next weekday with free slot
                    while True:
                        collection_date += timedelta(days=1)
                        if collection_date.weekday() < 5:
                            break
                    collection_time = collection_date.replace(hour=10, minute=0, second=0)

                # Insert appointment
                cursor.execute("""
                    INSERT INTO Appointments 
                    (StudentNumber, AppointmentDate, CollectionDate, CollectionTime, AppointmentStatus)
                    VALUES (%s, %s, %s, %s, 'Pending')
                """, (
                    studentNumber,
                    appointment_date_str,
                    collection_date.date(),
                    collection_time.strftime('%Y-%m-%d %H:%M:%S')
                ))

                connection.commit()
                flash('Registration successful! Appointment booked automatically.', 'success')
                return redirect(url_for('auth_routes.main_home'))

            except Exception as e:
                connection.rollback()
                flash(f'Registration failed: {str(e)}', 'error')

            finally:
                cursor.close()
                connection.close()
        else:
            flash('Database connection failed!', 'error')

    return render_template('RegistrationPage.html')
   
@students_bp.route('/generate_admin_report')
def generate_admin_report():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    try:
        connection = db_config.get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)

            # Retrieve all admins
            cursor.execute("SELECT * FROM Admin")
            admins = cursor.fetchall()

            # Count number of male and female admins
            cursor.execute("SELECT COUNT(*) FROM Admin WHERE Gender = 'Male'")
            male_count = cursor.fetchone()['COUNT(*)']

            cursor.execute("SELECT COUNT(*) FROM Admin WHERE Gender = 'Female'")
            female_count = cursor.fetchone()['COUNT(*)']

            connection.close()

            # Prepare a readable report content
            report_lines = [f"""*** Admin Report ***

            - Number of Male Admins: {male_count}
            - Number of Female Admins: {female_count}

            -------------------------------
            """]
            for admin in admins:
                report_lines.append(f"""
            Admin ID: {admin.get('AdminID')}
            First Name: {admin.get('Name')}
            Last Name: {admin.get('Surname')}
            Email: {admin.get('Email')}
            Gender: {admin.get('Gender')}
            -------------------------------
            """)

            report_content = "\n".join(report_lines)


            return render_template('adminRPage.html', report_content=report_content, admins=admins)

        else:
            return "Database connection failed", 500

    except Exception as e:
        return f"Error generating admin report: {str(e)}", 500

@students_bp.route('/generate_student_report')
def generate_student_report():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    try:
        connection = db_config.get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)

            # Total number of students
            cursor.execute("SELECT COUNT(*) AS total_students FROM Students")
            total_students = cursor.fetchone()['total_students']

            # Count students grouped by appointment status
            cursor.execute("""
                SELECT AppointmentStatus, COUNT(DISTINCT StudentNumber) AS count
                FROM Appointments
                GROUP BY AppointmentStatus
            """)
            status_counts = cursor.fetchall()  # Already in structured format

            connection.close()

            return render_template(
                'StudentReportPage.html',
                total_students=total_students,
                status_counts=status_counts
            )
        else:
            return "Database connection failed", 500

    except Exception as e:
        return f"Error generating student report: {str(e)}", 500
