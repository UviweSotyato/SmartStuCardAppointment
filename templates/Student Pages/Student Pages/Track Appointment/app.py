@app.route('/track_appointment', methods=['GET', 'POST'])
def track_appointment():
    status_data = None

    if request.method == 'POST':
        student_number = request.form['student_number']

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Get appointment(s) for this student
        cursor.execute("""
            SELECT AppointmentDate, CollectionDate, CollectionTime, AppointmentStatus
            FROM Appointments
            WHERE StudentNumber = %s
            ORDER BY AppointmentDate DESC
        """, (student_number,))
        status_data = cursor.fetchall()

        cursor.close()
        connection.close()

    return render_template('track_appointment.html', status_data=status_data)
