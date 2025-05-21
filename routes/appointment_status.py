# appointment_status.py
from flask import Blueprint, render_template, request, redirect, url_for, session
import db_config

status_bp = Blueprint('status', __name__, url_prefix='/status')

@status_bp.route('/')
def view_status():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    connection = db_config.get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM AppointmentStatus")
        statuses = cursor.fetchall()
        connection.close()
        return render_template('AppointmentStatusPage.html', statuses=statuses)
    else:
        return "Database connection failed"

@status_bp.route('/update_status/<int:status_id>', methods=['POST'])
def update_status(status_id):
    if not session.get('logged_in'):
        return redirect(url_for('auth_routes.login'))

    status_message = request.form.get('status_message')  # Only get what's in the form

    connection = db_config.get_db_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE appointmentstatus SET StatusMessage = %s WHERE StatusID = %s",
            (status_message, status_id)
        )
        connection.commit()
        cursor.close()
        connection.close()
        return redirect(url_for('status.view_status'))
    else:
        return "Database connection failed", 500

@status_bp.route('/update_status/<int:status_id>', methods=['POST'])
def update_status_message(status_id):
    if not session.get('logged_in'):
        return redirect(url_for('auth_routes.login'))

    status_message = request.form.get('status_message')
    
    connection = db_config.get_db_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE appointmentstatus SET StatusMessage = %s WHERE StatusID = %s",
            (status_message, status_id)
        )
        connection.commit()
        cursor.close()
        connection.close()
        return redirect(url_for('status.view_status'))
    else:
        return "Database connection failed", 500
