import warnings
from sqlalchemy import text, select, func, and_, exc as sa_exc
from flaskr.models import Post, Comment, PostVotes, CommentVotes, User
from flaskr.extensions import db
from datetime import datetime

def get_all_posts(
    sort_by: str = 'created_at', 
    order: str = 'asc', 
    page: int = 1,
    per_page: int = 20,
    include_total: bool = True,
    **kwargs
) -> dict[str]:
    if ((not hasattr(Post, sort_by)) and (sort_by != 'total_votes')):
        raise ValueError(f"Invalid sort field: {sort_by!r}")

    # Calculate offset
    offset = (page - 1) * per_page

    sort_votes = sort_by == 'total_votes'

    if not sort_votes:
        column = getattr(Post, sort_by)

    if not sort_votes and (order.lower() == 'desc'):
        column = column.desc()
    elif not sort_votes and (order.lower() == 'asc'):
        column = column.asc()
    elif ((not sort_votes or sort_votes)
        and (order.lower() != 'desc') 
        and (order.lower() != 'asc')):
        raise ValueError(f"Invalid order: {order}")

    stmt = select(Post)
    if not sort_votes:
        stmt = stmt.order_by(column)

    posts = db.paginate(stmt, error_out=False)

    ls = []
    for post in posts:
        d = post.to_dict()
        d.update({'total_votes': post.upvotes_cnt - post.dnvotes_cnt, 'user_vote': None})
        if len(post.comments) > 0:
            cmts = []
            for comment in post.comments:
                if comment.post_id == post.post_id:
                    cmt = comment.to_dict()
                    cmt.update({
                        'total_votes': comment.upvotes_cnt - comment.dnvotes_cnt,
                        'user_vote': None
                    })
                    cmts.append(cmt)
            d['comments'] = cmts
        else:
            #d['comments'] = { 'items': [] }
            d['comments'] = []
        ls.append(d)

    rtn = {
        'pagination': {
            'page': posts.page,
            'per_page': posts.per_page,
            'offset': offset,
            'has_prev': posts.has_prev,
            'has_next': posts.has_next,
            'prev_page': posts.prev_num,
            'next_page': posts.next_num
        }
    }

    # Add total-dependent fields if total was calculated
    if include_total:
        rtn['pagination'].update({
            'total': posts.total,
            'total_pages': posts.pages,
        })

    if sort_votes:
        ls = sorted(
            ls, 
            key=lambda it: it['total_votes'], 
            reverse=(order == 'desc')
        )

    rtn['items'] = ls
    return rtn

def get_all_posts_auth(
    user_id: int, 
    sort_by: str = 'created_at', 
    order: str = 'asc', 
    page: int = 1,
    per_page: int = 20,
    include_total: bool = True,
    **kwargs
) -> dict[str]:
    if ((not hasattr(Post, sort_by)) 
        and (sort_by != 'total_votes')
        and (sort_by != 'user_vote')):
        raise ValueError(f"Invalid sort field: {sort_by!r}")

    _s = ((sort_by != 'total_votes') and (sort_by != 'user_vote'))

    if _s:
        column = getattr(Post, sort_by)
    if _s and (order.lower() == 'desc'):
        column = column.desc()
    elif _s and (order.lower() == 'asc'):
        column = column.asc()
    elif ((_s or not _s)
        and (order.lower() != 'desc') 
        and (order.lower() != 'asc')):
        raise ValueError(f"Invalid order: {order}")
    
    # Calculate offset
    offset = (page - 1) * per_page

    with warnings.catch_warnings():
        warnings.simplefilter('ignore', category=sa_exc.SAWarning)
        stmt = (
            select(Post, PostVotes.vote_direction)
            .join_from(
                Post,
                PostVotes,
                onclause=and_(
                    PostVotes.post_id == Post.post_id,
                    PostVotes.user_id == user_id
                ),
                isouter=True
            )
        )

        if _s:
            stmt = stmt.order_by(column)

        stmt = stmt.offset(offset).limit(per_page)
        
        res = db.session.execute(stmt)
        items = res.all()

        # Get total count if requested
        total = None
        total_pages = None
        if include_total:
            # Count query - only count posts (not the joined votes)
            count_stmt = select(func.count(Post.post_id)).outerjoin(
                PostVotes,
                and_(
                    PostVotes.post_id == Post.post_id,
                    PostVotes.user_id == user_id
                )
            )
            total_result = db.session.execute(count_stmt)
            total = total_result.scalar()
            total_pages = (total + per_page - 1) // per_page  # Ceiling division

    # Build pagination metadata
    pagination_info = {
        'page': page,
        'per_page': per_page,
        'offset': offset,
        'has_prev': page > 1,
        'has_next': len(items) == per_page,  # Approximate, accurate if include_total=True
        'prev_page': page - 1 if page > 1 else None,
        'next_page': page + 1 if len(items) == per_page else None,
    }
    
    # Add total-dependent fields if total was calculated
    if include_total:
        pagination_info.update({
            'total': total,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'next_page': page + 1 if page < total_pages else None,
        })
        
    rtn = []
    for row in items:
        post, user_vote = row
        d = post.to_dict()
        if len(post.comments) > 0:
            cmts = get_comments_of_post_auth(user_id, post.post_id)
            d['comments'] = cmts
        else:
            #d['comments'] = { 'items': [] }
            d['comments'] = []

        d['total_votes'] = post.upvotes_cnt - post.dnvotes_cnt
        d['user_vote'] = user_vote.value if user_vote else None
        rtn.append(d)

    if sort_by in {'total_votes', 'user_vote'}:
        rtn = sorted(
            rtn, 
            key=lambda it: it[sort_by], 
            reverse=(order == 'desc')
        )
    return {
        'items': rtn,
        'pagination': pagination_info
    }

def get_comments_of_post_auth(
    user_id: int, 
    post_id: int, 
    sort_by: str = 'created_at', 
    order: str = 'asc'
):
    post = Post.query.get(post_id)
    if not post:
        raise ValueError("Post not found")

    if (not hasattr(Comment, sort_by) 
        and (sort_by != 'total_votes')
        and (sort_by != 'user_vote')):
        raise ValueError(f"Invalid sort field: {sort_by!r}")
    _s = ((sort_by != 'total_votes') and (sort_by != 'user_vote'))
    if _s:
        column = getattr(Comment, sort_by)
    if _s and (order.lower() == 'desc'):
        column = column.desc()
    elif _s and (order.lower() == 'asc'):
        column = column.asc()
    elif ((not _s or _s) 
          and (order.lower() != 'desc')
          and (order.lower() != 'asc')):
        raise ValueError(f"Invalid order: {order}")

    with warnings.catch_warnings():
        warnings.simplefilter('ignore', category=sa_exc.SAWarning)
        stmt = (
            select(Comment, CommentVotes.vote_direction)
            .join_from(
                Comment, CommentVotes,
                onclause=and_(
                    CommentVotes.comment_id == Comment.comment_id,
                    CommentVotes.user_id == user_id
                ), isouter=True
            )
        )

        if _s:
            stmt = stmt.order_by(column)
        res = db.session.execute(stmt)
    items = res.all()

    rtn = []
    for row in items:
        cmt, user_vote = row
        if cmt.post_id == post_id:
            d = cmt.to_dict()
            d['total_votes'] = cmt.upvotes_cnt - cmt.dnvotes_cnt
            d['user_vote'] = user_vote.value if user_vote else None
            rtn.append(d)

    if sort_by in {'total_votes', 'user_vote'}:
        rtn = sorted(
            rtn, 
            key=lambda it: it[sort_by], 
            reverse=(order == 'desc')
        )
    return rtn

def delete_post(user, post_id):
    from flaskr.services import UnauthorizedError
    #return {'msg': 'pass'}
    post: Post = Post.query.filter_by(post_id=post_id).first()
    is_su = user.account_type.value == 'superuser'
    is_author = user.user_id == post.user_id
    if not post:
        raise ValueError("Post not found")
    if ((not is_author) and (not is_su)):
        raise UnauthorizedError
    post_dict = post.to_dict(comments=True)
    db.session.delete(post)
    db.session.commit()
    return {"message": "Post deleted successfully", "post": post_dict}

def delete_comment(user, comment_id):
    from flaskr.services import UnauthorizedError
    comment = Comment.query.filter_by(comment_id=comment_id).first()
    is_su = user.account_type.value == 'superuser'
    is_author = user.user_id == comment.user_id
    if not comment:
        raise ValueError("Post not found")
    if ((not is_author) and (not is_su)):
        raise UnauthorizedError
    cmt_dict = comment.to_dict()
    db.session.delete(comment)
    db.session.commit()
    return {"message": "Comment deleted successfully", "comment": cmt_dict}

def update_post(user_id, post_id, new_data):
    post = Post.query.filter_by(post_id=post_id, user_id=user_id).first()
    if not post:
        return None
    if "title" in new_data:
        post.title = new_data["title"]
    if "content" in new_data:
        post.content = new_data["content"]
    db.session.commit()
    return post.to_dict()

def update_comment(user_id, comment_id, new_data):
    comment = Comment.query.filter_by(comment_id=comment_id, user_id=user_id).first()
    if not comment:
        return
    if "content" in new_data:
        comment.content = new_data["content"]
    db.session.commit()
    return comment.to_dict()

def create_post(user_id, temp_id, title, content):
    now = datetime.now()
    new_post = Post(
        user_id=user_id,
        temp_id=temp_id,
        title=title,
        content=content,
        created_at=now,
        updated_at=now
    )
    db.session.add(new_post)
    db.session.commit()
    return new_post.to_dict()

def create_comment(user_id, post_id, content, temp_id):
    now = datetime.now()
    new_comment = Comment(
        temp_id=temp_id,
        user_id=user_id,
        post_id=post_id,
        content=content,
        created_at=now,
        updated_at=now
    )
    db.session.add(new_comment)
    db.session.commit()
    return new_comment.to_dict()

def handle_post_vote(post_id, vote_direction, user_id):
    res = PostVotes.query.filter_by(post_id=post_id, user_id=user_id).first()
    if not res:
        # Create a new vote
        if vote_direction.value == 'up':
            inc_post_upvotes(post_id)
        elif vote_direction.value == 'down':
            inc_post_dnvotes(post_id)
        else:
            raise ValueError("wtf")
        new_vote = PostVotes(
            post_id=post_id,
            user_id=user_id,
            vote_direction=vote_direction
        )
        db.session.add(new_vote)
        db.session.commit()
    elif ((res != None) and (res.vote_direction == vote_direction)):
        # Remove / undo a vote
        # 1) delete the table entry
        db.session.delete(res)
        # 2) decrement the corresponding counter
        if res.vote_direction.value == 'up':
            dec_post_upvotes(post_id)
        elif res.vote_direction.value == 'down':
            dec_post_dnvotes(post_id)
        else:
            raise ValueError("wtf")
    elif ((res != None) and (res.vote_direction != vote_direction)):
        # Change a vote from one direction to the other
        old_direction = res.vote_direction.value
        res.vote_direction = vote_direction
        if old_direction == 'up':
            dec_post_upvotes(post_id)
            inc_post_dnvotes(post_id)
        elif old_direction == 'down':
            dec_post_dnvotes(post_id)
            inc_post_upvotes(post_id)
        else:
            raise ValueError("wtf")
    else:
        raise ValueError("wtf")
    return get_post_votes(post_id)

def handle_comment_vote(comment_id, vote_direction, user_id):
    res = CommentVotes.query.filter_by(comment_id=comment_id, user_id=user_id).first()
    if not res:
        # Create a new vote
        if vote_direction.value == 'up':
            inc_comment_upvotes(comment_id)
        elif vote_direction.value == 'down':
            inc_comment_dnvotes(comment_id)
        else:
            raise ValueError("wtf")
        new_vote = CommentVotes(
            comment_id=comment_id,
            user_id=user_id,
            vote_direction=vote_direction
        )
        db.session.add(new_vote)
        db.session.commit()
    elif ((res != None) and (res.vote_direction == vote_direction)):
        # Remove / undo a vote
        # 1) delete the table entry
        db.session.delete(res)
        # 2) decrement the corresponding counter
        if res.vote_direction.value == 'up':
            dec_comment_upvotes(comment_id)
        elif res.vote_direction.value == 'down':
            dec_comment_dnvotes(comment_id)
        else:
            raise ValueError("wtf")
    elif ((res != None) and (res.vote_direction != vote_direction)):
        # Change a vote from one direction to the other
        old_direction = res.vote_direction.value
        res.vote_direction = vote_direction
        if old_direction == 'up':
            dec_comment_upvotes(comment_id)
            inc_comment_dnvotes(comment_id)
        elif old_direction == 'down':
            dec_comment_dnvotes(comment_id)
            inc_comment_upvotes(comment_id)
        else:
            raise ValueError("wtf")
    else:
        raise ValueError("wtf")
    return get_comment_votes(comment_id)

def inc_post_upvotes(post_id):
    post = Post.query.filter_by(post_id=post_id).first()
    post.upvotes_cnt += 1
    db.session.commit()
    return post
    
def dec_post_upvotes(post_id):
    post = Post.query.filter_by(post_id=post_id).first()
    post.upvotes_cnt -= 1
    db.session.commit()
    return post

def inc_post_dnvotes(post_id):
    post = Post.query.filter_by(post_id=post_id).first()
    post.dnvotes_cnt += 1
    db.session.commit()
    return post
    
def dec_post_dnvotes(post_id):
    post = Post.query.filter_by(post_id=post_id).first()
    post.dnvotes_cnt -= 1
    db.session.commit()
    return post

def inc_comment_upvotes(comment_id):
    comment = Comment.query.filter_by(comment_id=comment_id).first()
    comment.upvotes_cnt += 1
    db.session.commit()
    return comment

def dec_comment_upvotes(comment_id):
    comment = Comment.query.filter_by(comment_id=comment_id).first()
    comment.upvotes_cnt -= 1
    db.session.commit()
    return comment

def inc_comment_dnvotes(comment_id):
    comment = Comment.query.filter_by(comment_id=comment_id).first()
    comment.dnvotes_cnt += 1
    db.session.commit()
    return comment

def dec_comment_dnvotes(comment_id):
    comment = Comment.query.filter_by(comment_id=comment_id).first()
    comment.dnvotes_cnt -= 1
    db.session.commit()
    return comment

def get_post_votes(post_id):
    post = Post.query.filter_by(post_id=post_id).first()
    up_votes = post.upvotes_cnt
    dn_votes = post.dnvotes_cnt
    total_votes = up_votes - dn_votes
    return up_votes, dn_votes, total_votes
    
def get_comment_votes(comment_id):
    comment = Comment.query.filter_by(comment_id=comment_id).first()
    up_votes = comment.upvotes_cnt
    dn_votes = comment.dnvotes_cnt
    total_votes = up_votes - dn_votes
    return up_votes, dn_votes, total_votes