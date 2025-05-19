# students.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
import base64
import db_config
from utils.face_detection import contains_face


feedback_bp = Blueprint('feedbacks', __name__, url_prefix='/feedbacks')

@feedback_bp.route('/')
def view_feedbacks():
    connection = db_config.get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Feedbacks")
        feedbacks = cursor.fetchall()
        connection.commit()
        connection.close()
        return render_template('extra-info.html',  feedbacks = feedbacks)
    else:
        return "Database connection failed"

@feedback_bp.route('/feedbacks')
def view_sec_feedbacks():
    connection = db_config.get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Feedbacks")
        feedbacks = cursor.fetchall()
        connection.commit()
        connection.close()
        return render_template('feedbacks.html',  feedbacks = feedbacks)
    else:
        return "Database connection failed"

@feedback_bp.route('/delete_feedback/<int:feedback_id>', methods=['POST'])
def delete_feedback(feedback_id):
    try:
        connection = db_config.get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM feedbacks WHERE id = %s", (feedback_id,))
            connection.commit()
            cursor.close()
            connection.close()
            return redirect(url_for('feedbacks.view_sec_feedbacks'))
        else:
            return jsonify({"error": "Database connection failed"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
 
@feedback_bp.route('/add_feedback', methods=['GET', 'POST'])
def add_feedback():
    if request.method == 'POST':
        studentNumber = request.form['studentNumber']
        firstName = request.form['firstname']   # fixed typo 'firsname' to 'firstname'
        lastName = request.form['lastname']
        feedback = request.form['feedback']
        emotion = request.form.get('emotion')   # new field for heart or broken heart
        starRatings = request.form['ratings']
        faculty = request.form['faculty']
        course = request.form['course']

        connection = db_config.get_db_connection()
        if connection:
            cursor = connection.cursor()
            sql = """
                INSERT INTO Feedbacks 
                (StudentNumber, firstName, lastName, feedback, emotion, starRatings, faculty, course) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            try:
                cursor.execute(sql, (studentNumber, firstName, lastName, feedback, emotion, starRatings, faculty, course))
                connection.commit()
                connection.close()
                flash('Feedback successful!', 'success')
                return redirect(url_for('feedbacks.view_feedbacks'))
            except Exception as e:
                connection.rollback()
                connection.close()
                flash(f'Feedback failed: {str(e)}', 'error')
                return render_template('feedbackPage.html')
        else:
            flash('Database connection failed!', 'error')
            return render_template('feedbackPage.html')

    return render_template('feedbackPage.html')
from flask import render_template
from collections import defaultdict

@feedback_bp.route('/report')
def feedback_report():
    try:
        connection = db_config.get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)

            # Average star rating
            cursor.execute("SELECT AVG(starRatings) as avg_rating FROM Feedbacks")
            avg_rating = cursor.fetchone()['avg_rating']

            # Count of emotions
            cursor.execute("SELECT emotion, COUNT(*) as count FROM Feedbacks GROUP BY emotion")
            emotion_counts = {row['emotion']: row['count'] for row in cursor.fetchall()}
            heart_count = emotion_counts.get('heart', 0)
            broken_heart_count = emotion_counts.get('broken_heart', 0)

            # Count by faculty (converted to dict)
            cursor.execute("SELECT faculty, COUNT(*) as count FROM Feedbacks GROUP BY faculty")
            faculty_counts = {row['faculty']: row['count'] for row in cursor.fetchall()}

            # Count by course (converted to dict)
            cursor.execute("SELECT course, COUNT(*) as count FROM Feedbacks GROUP BY course")
            course_counts = {row['course']: row['count'] for row in cursor.fetchall()}

            # Weekly feedbacks (e.g., by start of each week)
            cursor.execute("""
                SELECT DATE_FORMAT(DATE_SUB(created_at, INTERVAL WEEKDAY(created_at) DAY), '%Y-%m-%d') as week_start,
                       COUNT(*) as count
                FROM Feedbacks
                GROUP BY week_start
                ORDER BY week_start DESC
            """)
            weekly_feedbacks = {row['week_start']: row['count'] for row in cursor.fetchall()}

            # Get all feedbacks
            cursor.execute("SELECT id, StudentNumber, feedback, created_at FROM Feedbacks ORDER BY created_at DESC")
            feedbacks = cursor.fetchall()

            connection.close()

            return render_template(
                'feedback_report.html',
                avg_rating=round(avg_rating, 2) if avg_rating else 0,
                heart_count=heart_count,
                broken_heart_count=broken_heart_count,
                faculty_counts=faculty_counts,
                course_counts=course_counts,
                weekly_feedbacks=weekly_feedbacks,
                feedbacks=feedbacks
            )
        else:
            return "Database connection failed", 500
    except Exception as e:
        return f"Error: {str(e)}", 500
