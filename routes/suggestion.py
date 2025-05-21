from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
import db_config

suggestions_bp = Blueprint('suggestions', __name__, url_prefix='/suggestions')

@suggestions_bp.route('/')
def view_suggestions():
    connection = db_config.get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Suggestions")
        suggestions = cursor.fetchall()
        connection.commit()
        connection.close()
        return render_template('extra-info.html', suggestions=suggestions)
    else:
        return "Database connection failed"

@suggestions_bp.route('/suggestions')
def view_sec_suggestions():
    connection = db_config.get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Suggestions")
        suggestions = cursor.fetchall()
        connection.commit()
        connection.close()
        return render_template('Suggestions.html', suggestions=suggestions)
    else:
        return "Database connection failed"

@suggestions_bp.route('/delete_suggestion/<int:suggestion_id>', methods=['POST'])
def delete_suggestions(suggestion_id):
    try:
        connection = db_config.get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM Suggestions WHERE id = %s", (suggestion_id,))
            connection.commit()
            connection.close()
            return redirect(url_for('suggestions.view_sec_suggestions'))
        else:
            return jsonify({"error": "Database connection failed"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@suggestions_bp.route('/add_suggestion', methods=['GET', 'POST'])
def add_suggestion():
    if request.method == 'POST':
        studentNumber = request.form.get('studentNumber')
        username = request.form.get('username')
        suggestion = request.form.get('suggestion')
        faculty = request.form.get('faculty')
        course = request.form.get('course')

        if not studentNumber or not username or not suggestion or not faculty:
            flash('Please fill in all required fields', 'error')
            return render_template('suggestion-box.html')

        connection = db_config.get_db_connection()
        if connection:
            cursor = connection.cursor()
            sql = "INSERT INTO Suggestions (StudentNumber, username, suggestion , faculty , course ) VALUES (%s, %s, %s, %s , %s)"
            try:
                cursor.execute(sql, (studentNumber, username, suggestion, faculty, course))
                connection.commit()
                connection.close()
                flash('Suggestion successful!', 'success')
                # Redirect to view suggestions page
                return redirect(url_for('suggestions.view_suggestions'))
            except Exception as e:
                connection.rollback()
                connection.close()
                flash(f'Suggestion failed: {str(e)}', 'error')
                return render_template('suggestion-box.html')
        else:
            flash('Database connection failed!', 'error')
            return render_template('suggestion-box.html')

    # For GET request show the suggestion form
    return render_template('suggestion-box.html')

@suggestions_bp.route('/report')
def suggestion_report():
    try:
        connection = db_config.get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)

            # Count by faculty
            cursor.execute("SELECT faculty, COUNT(*) as count FROM Suggestions GROUP BY faculty")
            faculty_counts = {row['faculty']: row['count'] for row in cursor.fetchall()}

            # Count by course
            cursor.execute("SELECT course, COUNT(*) as count FROM Suggestions GROUP BY course")
            course_counts = {row['course']: row['count'] for row in cursor.fetchall()}

            # Get all suggestions (latest first)
            cursor.execute("SELECT StudentNumber, username, suggestion, faculty, course FROM Suggestions ")
            suggestions = cursor.fetchall()

            connection.close()

            return render_template(
                'suggestion_report.html',
                faculty_counts=faculty_counts,
                course_counts=course_counts,
                suggestions=suggestions
            )
        else:
            return "Database connection failed", 500
    except Exception as e:
        return f"Error: {str(e)}", 500