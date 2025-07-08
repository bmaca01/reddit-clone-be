from flask import Response, jsonify
from flask_jwt_extended.exceptions import JWTExtendedException

from .auth_service import user_id_credentials
from .chat_service import get_current_chat, add_message
from .social_media_service import get_all_posts, get_comments_of_post_auth, delete_comment, \
    delete_post, update_comment, update_post, create_comment, create_post, \
    inc_post_upvotes, dec_post_upvotes, inc_post_dnvotes, dec_post_dnvotes, \
    handle_comment_vote, handle_post_vote, get_all_posts_auth
from .registration_service import add_user
from .user_service import get_user_info_by_id

__all__ = [
    'user_id_credentials',
    'get_current_chat', 'add_message',
    'get_all_posts', 'get_comments_of_post_auth', 'delete_comment', 'delete_post', 
    'update_comment', 'update_post', 'create_comment', 'create_post', 
    'inc_post_upvotes', 'dec_post_upvotes', 'inc_post_dnvotes', 
    'dec_post_dnvotes', 'handle_comment_vote', 'handle_post_vote', 
    'get_all_posts_auth',
    'add_user',
    'get_user_info_by_id',
]

# AUTHORIZATION EXCEPTION RESPONSES
class UnauthorizedError(JWTExtendedException):
    pass

def USER_NOT_AUTHORIZED(uid: int|None=None) -> Response:
    if uid:
        print(f'User with id {uid} does not have permission to this resource')
        return jsonify({
            'error': f'User with id {uid} does not have permission to this resource'
        }), 401
    return jsonify({'error': 'User does not have permission to this resource'}), 401
   
