from flask import Blueprint, jsonify
from flaskr.models import User, Post, Comment, Notification, Chat, Message, UserAudit
from flasgger import swag_from

database_bp = Blueprint("database", __name__)

@database_bp.route('/', methods=['GET'])
@swag_from('../docs/database/fetch_tables.yml')
def fetch_tables():
    users = User.query.all()
    user_list = [user.to_dict() for user in users]
    return jsonify(user_list)