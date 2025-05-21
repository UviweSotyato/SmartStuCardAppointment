# requests_blueprint.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
import db_config
from io import BytesIO
from flask import send_file
import pandas as pd

requests_bp = Blueprint('requests', __name__, url_prefix='/requests')

# For student or secretary viewing requests
@requests_bp.route('/student')
def view_sec_requests():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    connection = db_config.get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT * FROM requesttable")
        all_requests = cursor.fetchall()

        connection.close()
        return render_template('view_requests.html', requests=all_requests)
    else:
        return "Database connection failed"

@requests_bp.route('/')
def view_requests():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    connection = db_config.get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT * FROM requesttable")
        all_requests = cursor.fetchall()

        connection.close()
        return render_template('AdminReportPage.html', requests=all_requests)
    else:
        return "Database connection failed"

@requests_bp.route('/submit', methods=['GET', 'POST'])
def submit_request():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        student_number = request.form['student_number']
        request_type = request.form['request_type']
        request_message = request.form.get('request_message', 'No message').strip()
        appointment_id_raw = request.form.get('appointment_id', '').strip()

        appointment_id = int(appointment_id_raw) if appointment_id_raw else None

        connection = db_config.get_db_connection()
        if connection:
            cursor = connection.cursor()
            sql = """
                INSERT INTO requesttable 
                (StudentNumber, Appointment_Id, RequestType, RequestMessage, RequestStatus)
                VALUES (%s, %s, %s, %s, %s)
            """
            try:
                cursor.execute(sql, (
                    student_number,
                    appointment_id,
                    request_type,
                    request_message,
                    "Pending"
                ))
                connection.commit()
                connection.close()
                flash('Request submitted successfully!', 'success')
                return redirect(url_for('requests.view_requests'))
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
            cursor.execute("DELETE FROM requesttable WHERE StudentNumber = %s", (session['student_number'],))
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
            cursor.execute("SELECT * FROM requesttable")
            all_requests = cursor.fetchall()
            connection.close()

            
            if not all_requests:
                return "No requests found", 404

            # Prepare headers and table rows
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

            
            report_content = "\n".join(report_lines)

            
            return render_template('AdminReportPage.html', report_content=report_content)

        else:
            flash("Database connection failed!", 'error')
            return redirect(url_for('AdminReportPage.html'))
    except Exception as e:
        flash(f"An error occurred: {str(e)}", 'error')
        return redirect(url_for('AdminReportPage.html'))
    
@requests_bp.route('/mark_done/<int:request_id>', methods=['POST'])
def mark_done(request_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    new_status = request.form.get('new_status')

    try:
        connection = db_config.get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE requesttable SET RequestStatus = %s WHERE RequestID = %s",
                (new_status, request_id)
            )
            connection.commit()
            connection.close()
            flash("Status updated successfully!", "success")
        else:
            flash("Database connection failed!", "error")
    except Exception as e:
        flash(f"Error updating status: {str(e)}", "error")

    return redirect(url_for('requests.view_requests'))

@requests_bp.route('/stats')
def request_stats():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    try:
        connection = db_config.get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)

            # Total number of requests
            cursor.execute("SELECT COUNT(*) AS total_requests FROM requesttable")
            total_requests = cursor.fetchone()['total_requests']

            # Number of each request type
            cursor.execute("""
                SELECT RequestType, COUNT(*) AS count 
                FROM requesttable 
                GROUP BY RequestType
            """)
            request_type_counts = cursor.fetchall()

            # Number of each request status
            cursor.execute("""
                SELECT RequestStatus, COUNT(*) AS count 
                FROM requesttable 
                GROUP BY RequestStatus
            """)
            status_counts = cursor.fetchall()

            connection.close()

            return render_template(
                'RequestStatsPage.html',
                total_requests=total_requests,
                request_type_counts=request_type_counts,
                status_counts=status_counts
            )
        else:
            return "Database connection failed", 500
    except Exception as e:
        return f"An error occurred: {str(e)}", 500
