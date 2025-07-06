from datetime import datetime, timezone
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user
from flask_socketio import emit, join_room
from flaskr.services import get_current_chat, add_message, USER_NOT_AUTHORIZED, UnauthorizedError
from flaskr.extensions import sio
from flasgger import swag_from

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/', methods=['GET'])
@jwt_required()
@swag_from('../docs/chat_routes/get_chat.yml')
def get_chat():
    try:
        chat = get_current_chat()
        #return jsonify(chat), 200
        return jsonify({"message": "Not yet implemented"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except UnauthorizedError as e:
        return USER_NOT_AUTHORIZED(current_user.user_id)
    

@chat_bp.route('/appointment/', methods=['PUT'])
@jwt_required()
@swag_from('../docs/chat_routes/put_message.yml')
def put_message():
    data = request.get_json()
    user_id = data.get("user_id")
    message_content = data.get("message")

    if not user_id or not message_content:
        return jsonify({"error": "user id and message are required"}), 400

    #result = add_message()
    result = None
    if result is None:
        return jsonify({"error": "Invalid appointment id"}), 404

    return jsonify(result), 201

"""
# Socket IO
@sio.event(namespace='/chat')
def connect():
    emit('Connected to chat')

@sio.on('join', namespace='/chat')
def handle_join(data):
    # Expecting json payload with appointment id
    room = data['appointment_id']
    join_room(room)

@sio.on('message', namespace='/chat')
def handle_message(data):
    # Expecting json payload with:
    # appointment_id, user_id, message content
    emit('message', {
        'user_id': data['user_id'], 
        'message': data['message'], 
        'timestamp': datetime.now(tz=timezone.utc).isoformat()
    }, namespace='/chat', to=data['appointment_id'])

    add_message(data['appointment_id'], data['user_id'], data['message'])

@sio.on('endChat', namespace='/chat')
def handle_end(data):
    # Expecting json payload with:
    # appointment_id
    emit('endChat', { 'msg': 'this meeting has finished' }, 
         namespace='/chat', to=data['appointment_id'])

    # Generate invoice on message end
    invoice_id = handle_meeting_end(data['appointment_id'])

@sio.on('disconnect', namespace='/chat')
def handle_disconnect(reason):
    print(f'client disconnected: {reason}')
"""