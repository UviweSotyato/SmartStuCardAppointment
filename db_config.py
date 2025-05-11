import mysql.connector

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",  # Use 'localhost' for local MySQL server
            user="root",       # Username is 'root'
            password="root",   # Password is 'root'
            database="smartstudcardDB",  # Use your database name here
        )
        print("✅ Connected to database successfully!")
        return connection
    except mysql.connector.Error as err:
        print(f"❌ Database connection error: {err}")
        return None

# Test connection when running the script
connection = get_db_connection()
if connection:
    print("✅ Database connection is working")
else:
    print("❌ Failed to connect to database")
