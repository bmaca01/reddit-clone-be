from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user
from flaskr.models import User
from flaskr.services import get_comments_of_post_auth, get_all_posts, delete_post, \
    delete_comment, update_comment, update_post, create_comment, create_post, \
    handle_post_vote, handle_comment_vote, get_all_posts_auth, \
    USER_NOT_AUTHORIZED, UnauthorizedError
from flaskr.struct import VoteDirection
from flasgger import swag_from

social_media_bp = Blueprint('social_media', __name__)

@social_media_bp.route('/', methods=['GET'], strict_slashes=False)
@jwt_required(optional=True)
@swag_from('../docs/social_media_routes/get_posts.yml')
def get_posts():
    sort_by = request.args.get('sort_by', 'created_at')
    order = request.args.get('order', 'desc')
    page = request.args.get('page', 1)
    per_page = request.args.get('per_page', 20)

    # Validate pagination parameters
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 20
    if per_page > 100:  # Prevent overly large requests
        per_page = 100

    try:
        if current_user:
            posts = get_all_posts_auth(current_user.user_id, 
                                       sort_by=sort_by, 
                                       order=order,
                                       page=page,
                                       per_page=per_page
                                       )
            #posts = get_all_posts(sort_by=sort_by, order=order)
            posts['user_id'] = current_user.user_id
        else:
            posts = get_all_posts(sort_by=sort_by, order=order, page=page, per_page=per_page)
        return jsonify(posts), 200
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

@social_media_bp.route('/<int:post_id>/comments', methods=['GET'], strict_slashes=False)
@jwt_required(optional=True)
#@swag_from('../docs/social_media_routes/get_post_comments.yml')
def get_post_comments(post_id):
    sort_by = request.args.get('sort_by', 'created_at')
    order = request.args.get('order', 'asc')
    try:
        comments = get_comments_of_post_auth(current_user.user_id, post_id, sort_by, order)
        return jsonify(comments), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@social_media_bp.route('/post/<int:post_id>', methods=['DELETE'])
@jwt_required()
#@swag_from('../docs/social_media_routes/delete_post.yml')
def delete_posts(post_id):
    #if ((current_user.account_type.name != 'SuperUser') 
    #    and (current_user.user_id != user_id)):
    #    return USER_NOT_AUTHORIZED(current_user.user_id)

    try:
        result = delete_post(current_user, post_id)
    except UnauthorizedError as e:
        return USER_NOT_AUTHORIZED(current_user.user_id)
    except ValueError as e:
        return jsonify({"error": "Post not found or unauthorized"}), 404
    except Exception as e:
        return jsonify({"error": "Post not found or unauthorized"}), 404
    return jsonify(result), 200

@social_media_bp.route('/comment/<int:comment_id>', methods=['DELETE'])
@jwt_required()
#@swag_from('../docs/social_media_routes/delete_comment.yml')
def delete_comments(comment_id):
    try:
        result = delete_comment(current_user, comment_id)
    except UnauthorizedError as e:
        return USER_NOT_AUTHORIZED(current_user.user_id)
    except ValueError as e:
        return jsonify({"error": "Comment not found or unauthorized"}), 404
    except Exception as e:
        return jsonify({"error": "Comment not found or unauthorized"}), 404
    return jsonify(result), 200

@social_media_bp.route('/<int:user_id>/post/<int:post_id>', methods=['PUT'])
@jwt_required()
@swag_from('../docs/social_media_routes/update_post.yml')
def update_posts(user_id, post_id):
    if ((current_user.account_type.name != 'SuperUser') 
        and (current_user.user_id != user_id)):
        return USER_NOT_AUTHORIZED(current_user.user_id)
    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data provided"}), 400

    result = update_post(user_id, post_id, data)
    if not result:
        return jsonify({"error": "Post not found or unauthorized"}), 404

    return jsonify(result), 200

@social_media_bp.route('/<int:user_id>/comment/<int:comment_id>', methods=['PUT'])
@jwt_required()
@swag_from('../docs/social_media_routes/update_comment.yml')
def update_comments(user_id, comment_id):
    if ((current_user.account_type.name != 'SuperUser') 
        and (current_user.user_id != user_id)):
        return USER_NOT_AUTHORIZED(current_user.user_id)
    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data provided"}), 400

    result = update_comment(user_id, comment_id, data)
    if not result:
        return jsonify({"error": "Comment not found or unauthorized"}), 404

    return jsonify(result), 200

@social_media_bp.route('/<int:user_id>/post', methods=['POST'])
@jwt_required()
@swag_from('../docs/social_media_routes/create_posts.yml')
def create_posts(user_id):
    if ((current_user.account_type.name != 'SuperUser') 
        and (current_user.user_id != user_id)):
        return USER_NOT_AUTHORIZED(current_user.user_id)
    data = request.get_json()
    title = data.get("title")
    content = data.get("content")
    temp_id = data.get("temp_id")
    if not title:
        return jsonify({"error": "Title is required"}), 400
    if not content:
        return jsonify({"error": "content is required"}), 400
    if not temp_id:
        return jsonify({"error": "temp_id is required"}), 400
    result = create_post(user_id, temp_id, title, content)
    return jsonify({
                    "message": "Post Created Successfully",
                    "post" : result
        }), 201

@social_media_bp.route('/<int:user_id>/post/<int:post_id>/comment', methods=['POST'])
@jwt_required()
@swag_from('../docs/social_media_routes/create_comments.yml')
def create_comments(user_id, post_id):
    data = request.get_json()
    content = data.get("content")
    temp_id = data.get("temp_id")
    if (not content) or (not temp_id):
        return jsonify({"error": "Content and temp_id is required"}), 400
    result = create_comment(current_user.user_id, post_id, content, temp_id)
    return jsonify({
                    "message": "Comment Created Successfully",
                    "comment" : result
        }), 201

@social_media_bp.route('/post/<int:post_id>', methods=['POST'])
@jwt_required()
def vote_post(post_id):
    data = request.get_json()
    vote = str(data.get("vote")).lower()
    if vote == 'none':
        return jsonify({"error": "error"}), 500
    elif vote == 'up':
        vote = VoteDirection.UP
    elif vote == 'down':
        vote = VoteDirection.DOWN
    else:
        return jsonify({"error": "error"}), 500

    try: 
        res = handle_post_vote(post_id, vote, current_user.user_id)
        up, down, total = res
    except:
        return jsonify({"error": "error"}), 500

    return jsonify(
        {
            "post_id": post_id,
            "up_votes": up,
            "down_votes": down,
            "total_votes": total
        }
    ), 200


@social_media_bp.route('/comment/<int:comment_id>', methods=['POST'])
@jwt_required()
def vote_comment(comment_id):
    data = request.get_json()
    vote = data.get("vote")
    if vote == 'none':
        return jsonify({"error": "error"}), 500
    elif vote == 'up':
        vote = VoteDirection.UP
    elif vote == 'down':
        vote = VoteDirection.DOWN
    else:
        return jsonify({"error": "error"}), 500

    try: 
        res = handle_comment_vote(comment_id, vote, current_user.user_id)
        up, down, total = res
    except Exception as e:
        print(e)
        return jsonify({"error": "error"}), 500

    return jsonify(
        {
            "comment_id": comment_id,
            "up_votes": up,
            "down_votes": down,
            "total_votes": total
        }
    ), 200