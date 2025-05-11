from flask import Blueprint, render_template, redirect, url_for, jsonify, session , request
import db_config


notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')

@notifications_bp.route('/')
def view_notifications():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    connection = db_config.get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM notificationtable ")
        notifications = cursor.fetchall()
        # Example
        cursor.execute("SELECT * FROM Students WHERE StudentNumber  = %s", (session['student_number'],))
        student = cursor.fetchone()

        connection.commit()
        connection.close()
        return render_template('view_notifications.html', notifications=notifications, student=student)

    else:
        return "Database connection failed", 500

@notifications_bp.route('/delete_all', methods=['POST'])
def delete_all_notifications():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    connection = db_config.get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM notificationtable ")
            connection.commit()
            connection.close()
            return jsonify({'message': 'All notifications deleted successfully'}), 200
        except Exception as e:
            connection.rollback()
            connection.close()
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'Database connection failed'}), 500

@notifications_bp.route('/filter')
def filter_notifications_by_date():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    filter_date = request.args.get('date')  # expects YYYY-MM-DD

    if not filter_date:
        return "Missing date parameter", 400

    connection = db_config.get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM notificationtable  WHERE DATE(NotificationDate) = %s", (filter_date,))
            filtered_notifications = cursor.fetchall()
            connection.commit()
            connection.close()
            return render_template('view_notifications.html', notifications=filtered_notifications)
        except Exception as e:
            connection.commit()
            connection.close()
            return jsonify({'error': str(e)}), 500
    else:
        return "Database connection failed", 500

