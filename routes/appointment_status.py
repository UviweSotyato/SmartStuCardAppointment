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

@status_bp.route('/edit/<status_id>', methods=['GET', 'POST'])
def edit_status(status_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    connection = db_config.get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM AppointmentStatus WHERE StatusID = %s", (status_id,))
        status = cursor.fetchone()
        if not status:
            return "Status not found", 404

        if request.method == 'POST':
            new_status_name = request.form['new_status_name']
            cursor.execute("UPDATE AppointmentStatus SET StatusName = %s WHERE StatusID = %s", (new_status_name, status_id))
            connection.commit()
            connection.close()
            return redirect(url_for('status.view_status'))

        connection.close()
        return render_template('EditStatus.html', status=status)
    else:
        return "Database connection failed", 500
