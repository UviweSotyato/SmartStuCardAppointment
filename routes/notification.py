from flask import Blueprint, render_template, redirect, url_for, jsonify, session , request , flash
import db_config
from datetime import datetime



notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')

@notifications_bp.route('/')
def view_notifications():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    student_number = session['student_number']

    connection = db_config.get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)

        # Get student details
        cursor.execute("SELECT * FROM Students WHERE StudentNumber = %s", (student_number,))
        student = cursor.fetchone()

        # Fetch notifications for the student
        cursor.execute("""
            SELECT 
                Message,
                DateSent
            FROM notificationtable
            WHERE StudentNumber = %s
            ORDER BY DateSent DESC
        """, (student_number,))
        notifications = cursor.fetchall()

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

    filter_date = request.args.get('date')  # expects format: YYYY-MM-DD

    if not filter_date:
        return "Missing date parameter", 400

    connection = db_config.get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT * FROM notificationtable 
                WHERE DATE(DateSent) = %s
            """, (filter_date,))
            filtered_notifications = cursor.fetchall()
            connection.close()
            return render_template('view_notifications.html', notifications=filtered_notifications)
        except Exception as e:
            connection.close()
            return jsonify({'error': str(e)}), 500
    else:
        return "Database connection failed", 500

@notifications_bp.route('/send-notification', methods=['GET', 'POST'])
def send_notification():
    connection = db_config.get_db_connection()
    cursor = connection.cursor()

    if request.method == 'POST':
        student_number = request.form['student_number']
        message = request.form['message']

        try:
            cursor.execute("""
                INSERT INTO notificationtable (StudentNumber, Message, DateSent)
                VALUES (%s, %s, %s)
            """, (student_number, message, datetime.now()))

            connection.commit()
            flash("Notification sent successfully!", "success")
            return redirect(url_for('notifications.send_notification'))

        except Exception as e:
            connection.rollback()
            return f"Error sending notification: {e}", 500
        finally:
            connection.close()

    return render_template("send_notification.html")
