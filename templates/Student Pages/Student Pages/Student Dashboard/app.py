from flask import Flask, render_template, request, redirect, url_for
import mysql.connector

app = Flask(__name__)

# Database connection
def get_db_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="yourpassword",
        database="StudentCardSystem"
    )
    return connection

# Student Dashboard Route
@app.route('/student/<student_number>')
def student_dashboard(student_number):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Fetch student details by student number
    cursor.execute("SELECT * FROM Students WHERE StudentNumber = %s", (student_number,))
    student = cursor.fetchone()

    # Fetch all appointments for this student
    cursor.execute("SELECT * FROM Appointments WHERE StudentNumber = %s", (student_number,))
    appointments = cursor.fetchall()

    cursor.close()
    connection.close()
    
    return render_template('student_dashboard.html', student=student, appointments=appointments)

# Book Appointment Route
@app.route('/student/book_appointment/<student_number>', methods=['GET', 'POST'])
def book_appointment(student_number):
    if request.method == 'POST':
        appointment_date = request.form['appointment_date']
        collection_date = request.form['collection_date']
        collection_time = request.form['collection_time']
        status = 'Scheduled'

        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Insert new appointment into the database
        cursor.execute("""
            INSERT INTO Appointments (StudentNumber, AppointmentDate, CollectionDate, CollectionTime, AppointmentStatus)
            VALUES (%s, %s, %s, %s, %s)
        """, (student_number, appointment_date, collection_date, collection_time, status))

        connection.commit()
        cursor.close()
        connection.close()

        return redirect(url_for('student_dashboard', student_number=student_number))

    return render_template('book_appointment.html', student_number=student_number)

# Start the Flask server
if __name__ == '__main__':
    app.run(debug=True)
