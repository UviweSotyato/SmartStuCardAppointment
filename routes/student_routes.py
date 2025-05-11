# students.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
import base64
import db_config
from utils.face_detection import contains_face


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
        picture = request.files.get('picture')
        signature_data_url = request.form.get('signatureData')

        signature_data = None
        if signature_data_url:
            try:
                _, base64_data = signature_data_url.split(',')
                signature_data = base64.b64decode(base64_data)
            except Exception as e:
                flash(f'Error decoding signature: {str(e)}', 'error')
                return render_template('RegistrationPage.html')

        if picture:
            picture_data = picture.read()
            if not contains_face(picture_data):
                flash('The uploaded picture does not contain a clear face.', 'error')
                return render_template('RegistrationPage.html')

            connection = db_config.get_db_connection()
            if connection:
                cursor = connection.cursor()
                sql = "INSERT INTO Students (StudentNumber, FirstName, LastName, Email, Residence, Picture, Signature) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                try:
                    cursor.execute(sql, (studentNumber, firstName, lastName, email, residence, picture_data, signature_data))
                    connection.commit()
                    connection.rollback()
                    connection.close()
                    flash('Registration successful!', 'success')
                    return redirect(url_for('main_home'))
                except Exception as e:
                    connection.rollback()
                    connection.close()
                    flash(f'Registration failed: {str(e)}', 'error')
                    return render_template('RegistrationPage.html')
            else:
                flash('Database connection failed!', 'error')
                return render_template('RegistrationPage.html')
        else:
            flash('Please upload a picture of your face.', 'error')
            return render_template('RegistrationPage.html')

    return render_template('RegistrationPage.html')

@students_bp.route('/generate_report')
def generate_report():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    try:
        connection = db_config.get_db_connection()
        if connection:
            cursor = connection.cursor()

            # Get counts from Students and Appointments tables
            cursor.execute("SELECT COUNT(*) FROM appointments  WHERE AppointmentStatus = 'Declined'")
            declined = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM appointments  WHERE AppointmentStatus = 'Collected'")
            collected = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM appointments  WHERE AppointmentStatus = 'Completed'")
            completed_not_collected = cursor.fetchone()[0]

            # Retrieve all students
            cursor.execute("SELECT * FROM Students")
            students = cursor.fetchall()

            connection.close()

            # Prepare the report content
            report_content = f"""
            *** Student Card Report ***

            - Students Declined: {declined}
            - Students Collected Cards: {collected}
            - Completed Cards (Not Collected): {completed_not_collected}
            
            *** Students ***
            {students}
            """

            return render_template('ReportPage.html', report_content=report_content)

        else:
            return "Database connection failed", 500

    except Exception as e:
        return f"Error generating report: {str(e)}", 500
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


            return render_template('AdminReportPage.html', report_content=report_content, admins=admins)

        else:
            return "Database connection failed", 500

    except Exception as e:
        return f"Error generating admin report: {str(e)}", 500