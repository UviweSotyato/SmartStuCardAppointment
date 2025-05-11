@app.route('/update_details', methods=['GET', 'POST'])
def update_details():
    message = None
    student_data = None

    if request.method == 'POST':
        student_number = request.form['student_number']

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Get student details
        cursor.execute("SELECT * FROM Students WHERE StudentNumber = %s", (student_number,))
        student_data = cursor.fetchone()

        if 'update' in request.form and student_data:
            # Updating the student's details
            new_email = request.form['email']
            new_residence = request.form['residence']

            cursor.execute("""
                UPDATE Students 
                SET Email = %s, Residence = %s 
                WHERE StudentNumber = %s
            """, (new_email, new_residence, student_number))
            connection.commit()
            message = "Details updated successfully."

            # Refresh data
            cursor.execute("SELECT * FROM Students WHERE StudentNumber = %s", (student_number,))
            student_data = cursor.fetchone()

        cursor.close()
        connection.close()

    return render_template('update_details.html', student_data=student_data, message=message)
