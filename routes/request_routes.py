# requests_blueprint.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
import db_config
from io import BytesIO
from flask import send_file
import pandas as pd

requests_bp = Blueprint('requests', __name__, url_prefix='/requests')

@requests_bp.route('/')
def view_requests():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    student_number = session.get('student_number')  # get from session

    connection = db_config.get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)

        # Fetch all requests
        cursor.execute("SELECT * FROM requesttable WHERE StudentNumber = %s", (student_number,))
        all_requests = cursor.fetchall()

        # Optional: fetch student details if needed (example query)
        cursor.execute("SELECT * FROM Students WHERE StudentNumber = %s", (student_number,))
        student = cursor.fetchone()

        connection.close()

        return render_template('View_requests.html', requests=all_requests, student=student)
    else:
        return "Database connection failed"

@requests_bp.route('/submit', methods=['GET', 'POST'])
def submit_request():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        student_number = request.form['student_number']
        request_type = request.form['request_type']  # "cancel" or "change_date"
        new_date = request.form.get('new_date')  # Only required if request_type is change_date

        connection = db_config.get_db_connection()
        if connection:
            cursor = connection.cursor()
            sql = "INSERT INTO requesttable  (StudentNumber, RequestType, NewDate) VALUES (%s, %s, %s)"
            try:
                cursor.execute(sql, (student_number, request_type, new_date))
                connection.commit()
                connection.close()
                flash('Request submitted successfully!', 'success')
                return redirect(url_for('requests.submit_request'))
            except Exception as e:
                connection.rollback()
                connection.close()
                flash(f'Request submission failed: {str(e)}', 'error')
                return redirect(url_for('requests.submit_request'))
        else:
            flash('Database connection failed!', 'error')
            return redirect(url_for('requests.submit_request'))

    return render_template('SubmitRequestPage.html')

@requests_bp.route('/delete_all', methods=['POST'])
def delete_all_requests():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    try:
        connection = db_config.get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM requesttable  WHERE StudentNumber = %s", (session['student_number'],))
            connection.commit()
            connection.close()
            return jsonify({"message": "All requests deleted successfully"}), 200
        else:
            return jsonify({"error": "Database connection failed"}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@requests_bp.route('/print_requests')
def print_requests():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    try:
        connection = db_config.get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM requesttable")  # Fetch all requests from the requesttable
            all_requests = cursor.fetchall()
            connection.close()

            # Check if there are any records
            if not all_requests:
                return "No requests found", 404

            # Prepare the table headers
            headers = ["RequestID", "StudentNumber", "Appointment_Id", "RequestType", "RequestMessage", "RequestDate", "RequestStatus"]

            # Prepare the report content in a similar format as the second code
            report_lines = ["+----------------+-------------+------+-----+-------------------+-------------------+"]
            report_lines.append("| Field          | Type        | Null | Key | Default           | Extra             |")
            report_lines.append("+----------------+-------------+------+-----+-------------------+-------------------+")
            for row in all_requests:
                row_data = [
                    str(row.get("RequestID", "")),
                    str(row.get("StudentNumber", "")),
                    str(row.get("Appointment_Id", "")),
                    row.get("RequestType", ""),
                    row.get("RequestMessage", ""),
                    str(row.get("RequestDate", "")),
                    row.get("RequestStatus", "")
                ]
                report_lines.append("| {:<14} | {:<12} | {:<4} | {:<3} | {:<17} | {:<17} |".format(*row_data))
            report_lines.append("+----------------+-------------+------+-----+-------------------+-------------------+")

            # Convert the list of lines to a single string
            report_content = "\n".join(report_lines)

            # Render the report in an HTML page
            return render_template('AdminReportPage.html', report_content=report_content)

        else:
            flash("Database connection failed!", 'error')
            return redirect(url_for('AdminReportPage.html'))
    except Exception as e:
        flash(f"An error occurred: {str(e)}", 'error')
        return redirect(url_for('AdminReportPage.html'))
