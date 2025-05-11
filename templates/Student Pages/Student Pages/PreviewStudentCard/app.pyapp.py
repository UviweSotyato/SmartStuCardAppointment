@app.route('/preview_card/<student_number>')
def preview_card(student_number):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT * FROM Students WHERE StudentNumber = %s", (student_number,))
    student = cursor.fetchone()

    cursor.close()
    connection.close()

    if not student:
        return "Student not found.", 404

    return render_template('student_card_preview.html', student=student)
