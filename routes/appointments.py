# routes/appointment_routes.py
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session
from datetime import datetime, timedelta
import db_config

appointment_bp = Blueprint('appointments', __name__)

@appointment_bp.route('/appointments')
def view_appointments():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    connection = db_config.get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Appointments")
        appointments = cursor.fetchall()
        connection.close()
        return render_template('AppointmentsPage.html', appointments=appointments)
    else:
        return "Database connection failed"

@appointment_bp.route('/delete_appointment/<appointment_id>', methods=['GET'])
def delete_appointment(appointment_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    try:
        connection = db_config.get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM Appointments WHERE Appointment_Id = %s", (appointment_id,))
            connection.commit()
            connection.close()
            return redirect(url_for('appointments.view_appointments'))  # Updated
        else:
            return jsonify({"error": "Database connection failed"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@appointment_bp.route('/edit_appointment/<appointment_id>', methods=['GET', 'POST'])
def edit_appointment(appointment_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    connection = db_config.get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Appointments WHERE Appointment_Id = %s", (appointment_id,))
        appointment = cursor.fetchone()
        if not appointment:
            connection.close()
            return "Appointment not found", 404
        if request.method == 'POST':
            new_status = request.form['new_status']
            cursor.execute("UPDATE Appointments SET AppointmentStatus = %s WHERE Appointment_Id = %s",
                           (new_status, appointment_id))
            connection.commit()
            connection.close()
            return redirect(url_for('appointments.view_appointments'))  # Updated
        connection.close()
        return render_template('EditAppointment.html', appointment=appointment)
    else:
        return "Database connection failed", 500

@appointment_bp.route('/add_appointment', methods=['POST'])
def add_appointment():
    try:
        student_number = request.form['student_number']
        appointment_date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%d %H:%M:%S')

        collection_date = appointment_date + timedelta(weeks=2)

        # Adjust for weekends
        if collection_date.weekday() == 5:
            collection_date -= timedelta(days=1)
        elif collection_date.weekday() == 6:
            collection_date += timedelta(days=1)

        connection = db_config.get_db_connection()
        if connection:
            cursor = connection.cursor()

            # Check if student exists
            cursor.execute("SELECT StudentName FROM Students WHERE StudentNumber = %s", (student_number,))
            student_name_result = cursor.fetchone()

            if student_name_result:
                student_name = student_name_result[0]

                # Determine collection time slot
                cursor.execute("SELECT COUNT(*) FROM Appointments WHERE DATE(CollectionDate) = %s AND TIME(CollectionDate) < '12:00:00'",
                               (collection_date.date(),))
                before_12_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM Appointments WHERE DATE(CollectionDate) = %s AND TIME(CollectionDate) >= '12:00:00'",
                               (collection_date.date(),))
                after_12_count = cursor.fetchone()[0]

                if before_12_count < 5:
                    collection_time = collection_date.replace(hour=10, minute=0, second=0)
                elif after_12_count < 5:
                    collection_time = collection_date.replace(hour=14, minute=0, second=0)
                else:
                    collection_date += timedelta(days=1)
                    # Adjust for weekends
                    if collection_date.weekday() == 5:
                        collection_date -= timedelta(days=1)
                    elif collection_date.weekday() == 6:
                        collection_date += timedelta(days=1)
                    collection_time = collection_date.replace(hour=10, minute=0, second=0)

                collection_time_str = collection_time.strftime('%Y-%m-%d %H:%M:%S')

                # Insert appointment
                cursor.execute(
                    "INSERT INTO Appointments (StudentNumber, StudentName, AppointmentDate, CollectionDate, Status) "
                    "VALUES (%s, %s, %s, %s, 'Pending')",
                    (student_number, student_name, appointment_date_str, collection_time_str)
                )
                connection.commit()
                connection.close()
                return jsonify({"message": "Appointment added successfully"}), 201
            else:
                connection.close()
                return jsonify({"error": "Student not found"}), 404
        else:
            return jsonify({"error": "Database connection failed"}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@appointment_bp.route('/update_collection_time', methods=['POST'])
def update_collection_time():
    try:
        student_number = request.form['student_number']
        new_collection_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        connection = db_config.get_db_connection()
        if connection:
            cursor = connection.cursor()

            cursor.execute("SELECT * FROM Appointments WHERE StudentNumber = %s", (student_number,))
            appointment_result = cursor.fetchone()

            if appointment_result:
                cursor.execute(
                    "UPDATE Appointments SET CollectionTime = %s WHERE StudentNumber = %s",
                    (new_collection_time, student_number)
                )
                connection.commit()
                connection.close()
                return jsonify({"message": "Collection time updated successfully"}), 200
            else:
                connection.close()
                return jsonify({"error": "Appointment not found for this student"}), 404
        else:
            return jsonify({"error": "Database connection failed"}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
