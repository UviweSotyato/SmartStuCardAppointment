from flask import Flask
from flask_cors import CORS
import secrets
from flask_login import LoginManager

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.secret_key = secrets.token_hex(16)
    CORS(app)

    login_manager.init_app(app)
    login_manager.login_view = 'auth_routes.login'  # Your login route endpoint here

    # Import blueprints here
    from routes import (
        auth_routes, student_routes, appointments, appointment_status,
        student_login, request_routes, notification, feedback, suggestion
    )

    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(student_routes.students_bp)
    app.register_blueprint(appointments.appointment_bp)
    app.register_blueprint(appointment_status.status_bp)
    app.register_blueprint(student_login.bp)
    app.register_blueprint(request_routes.requests_bp)
    app.register_blueprint(notification.notifications_bp)
    app.register_blueprint(feedback.feedback_bp)
    app.register_blueprint(suggestion.suggestions_bp)

    return app
