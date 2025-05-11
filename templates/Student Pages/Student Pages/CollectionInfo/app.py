@app.route('/collection_info', methods=['GET', 'POST'])
def collection_info():
    collection_data = None

    if request.method == 'POST':
        student_number = request.form['student_number']

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT a.AppointmentDate, a.CollectionDate, a.CollectionTime, a.AppointmentStatus,
                   s.FirstName, s.LastName, s.Residence
            FROM Appointments a
            JOIN Students s ON a.StudentNumber = s.StudentNumber
            WHERE a.StudentNumber = %s
            ORDER BY a.CollectionDate DESC
        """, (student_number,))
        collection_data = cursor.fetchall()

        cursor.close()
        connection.close()

    return render_template('collection_info.html', collection_data=collection_data)
