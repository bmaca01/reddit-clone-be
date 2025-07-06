from flask import Blueprint, Flask
from .database import database_bp
from .registration_routes import register_bp
from .chat_routes import chat_bp
from .social_media_routes import social_media_bp
from .auth_routes import auth_bp
from .user_routes import user_bp

main_bp = Blueprint('main', __name__)

def register_routes(app: Flask):
    app.register_blueprint(database_bp, url_prefix='/test_connection')
    app.register_blueprint(chat_bp, url_prefix='/chat')
    app.register_blueprint(social_media_bp, url_prefix='/social_media')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(register_bp, url_prefix='/register')
    app.register_blueprint(user_bp, url_prefix='/user')
