from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import check_password_hash
from db_config import get_db_connection

bp = Blueprint('auth_routes', __name__)

@bp.route('/')
def main_home():
    return render_template("MainHomePage.html")

@bp.route('/admin_login_page')
def admin_login_page():
    return render_template("AdminLoginPage.html")

@bp.route('/login', methods=['GET', 'POST'])
def login():
    name = request.form.get('username')
    password = request.form.get('password')

    connection = get_db_connection()
    
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Admin WHERE Name = %s", (name,))
        admin = cursor.fetchone()

        if admin and admin['Password'] == password:  # <-- Direct comparison
            session['logged_in'] = True
            session['name'] = admin['Name']
            return redirect(url_for('auth_routes.admin_home'))
        else:
            error = "Invalid name or password"
            return render_template("AdminLoginPage.html", error=error)
    else:
        error = "Database connection error"
        return render_template("AdminLoginPage.html", error=error)

@bp.route('/AdminHomePage')
def admin_home():
    if not session.get('logged_in'):
        return redirect(url_for('auth_routes.admin_login_page'))
    return render_template("AdminHomePage.html")

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth_routes.main_home'))
