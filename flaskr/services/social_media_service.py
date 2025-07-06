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

    for post in posts:
        print(post.comments)
        if len(post.comments) != 0:
            for comment in post.comments:
                print(comment)
                print(comment.to_dict())

    res = [(
        post.to_dict(comments=True) | {
            "total_votes": post.upvotes_cnt - post.dnvotes_cnt,
            "user_vote": None,
        }
    ) for post in posts]

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
        res = sorted(
            res, 
            key=lambda it: it['total_votes'], 
            reverse=(order == 'desc')
        )

    rtn['items'] = res
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
        print(row)
        post, user_vote = row
        d = post.to_dict(comments=True)
        d['total_votes'] = post.upvotes_cnt - post.dnvotes_cnt
        d['user_vote'] = user_vote.value if user_vote else None
        print(d)
        rtn.append(d)

    if sort_by in {'total_votes', 'user_vote'}:
        return sorted(
            res, 
            key=lambda it: it[sort_by], 
            reverse=(order == 'desc')
        )
    return {
        'items': rtn,
        'pagination': pagination_info
    }

def get_all_posts_auth_old(user_id, sort_by='created_at', order='asc', **kwargs):
    class TextClausePagination:
        def __init__(self, text_clause, page, per_page, params=None):
            self.text_clause = text_clause
            self.page = page
            self.per_page = per_page
            self.params = params or {}
            self._items = None
            self._total = None
        
        @property
        def items(self):
            if self._items is None:
                self._load_items()
            return self._items
        
        @property
        def total(self):
            if self._total is None:
                self._load_total()
            return self._total
        
        def _load_items(self):
            offset = (self.page - 1) * self.per_page
            sql = self.text_clause.text + f" LIMIT {self.per_page} OFFSET {offset}"
            result = db.session.execute(text(sql), self.params)
            self._items = result.fetchall()
        
        def _load_total(self):
            count_sql = f"SELECT COUNT(*) FROM ({self.text_clause.text}) as count_query"
            result = db.session.execute(text(count_sql), self.params)
            self._total = result.scalar()
        
        @property
        def pages(self):
            return (self.total + self.per_page - 1) // self.per_page
        
        @property
        def has_prev(self):
            return self.page > 1
        
        @property
        def has_next(self):
            return self.page < self.pages
    
        @property
        def prev_num(self):
            return self.page - 1 if self.has_prev else None
    
        @property
        def next_num(self):
            return self.page + 1 if self.has_next else None
    
        # Make the pagination object iterable
        def __iter__(self):
            """Make the pagination object iterable over items"""
            return iter(self.items)
    
        def __len__(self):
            """Return the number of items on current page"""
            return len(self.items)
    
        def __getitem__(self, index):
            """Allow indexing into the items"""
            return self.items[index]

    if ((not hasattr(Post, sort_by))
        and (sort_by != 'total_votes')
        and (sort_by != 'user_vote')):
        raise ValueError(f"Invalid sort field: {sort_by!r}")

    stmt = text(
        f""" 
        SELECT 
	        p.post_id, pv.user_id AS user_vote, p.user_id, 
            p.title, p.content, 
            pv.vote_direction, (p.upvotes_cnt - p.dnvotes_cnt) AS total_votes,
            p.upvotes_cnt, p.dnvotes_cnt,
            p.created_at, p.updated_at,
            u1.username 
        FROM post AS p
        LEFT JOIN post_votes AS pv ON pv.post_id = p.post_id
        LEFT JOIN user AS u1 ON u1.user_id = p.user_id
        LEFT JOIN user AS u2 ON u2.user_id = {user_id}
        ORDER BY {sort_by} {order}
        """)

    posts = TextClausePagination(
        text_clause=stmt,
        page=kwargs.get('page', 1),
        per_page=kwargs.get('per_page', 20),
    )

    res = []
    print(posts[0]._fields)
    for i in posts:
        res.append({
            'author': {
                'username': i.username
            },
            'post_id': i.post_id
            
        })
    #return [dict(r._mapping) for r in posts]
    return

def get_comments_of_post(post_id, sort_by='created_at', order='asc'):
    post = Post.query.get(post_id)
    if not post:
        raise ValueError("Post not found")
    if not hasattr(Comment, sort_by):
        raise ValueError(f"Invalid sort field: {sort_by!r}")
    column = getattr(Comment, sort_by)
    if order.lower() == 'desc':
        column = column.desc()
    elif order.lower() == 'asc':
        column = column.asc()
    else:
        raise ValueError(f"Invalid order: {order}")
    #comments = Comment.query.filter_by(post_id=post_id).order_by(column).all()
    comments = db.paginate(db.select(Comment)
                           .where(Comment.post_id == post_id)
                           .order_by(column), error_out=False)

    return [comment.to_dict() for comment in comments]

def delete_post(user_id, post_id):
    post = Post.query.filter_by(post_id=post_id, user_id=user_id).first()
    if not post:
        return None
    db.session.delete(post)
    db.session.commit()
    return {"message": "Post and it comments deleted successfully", "post_id": post_id}

def delete_comment(user_id, comment_id):
    comment = Comment.query.filter_by(comment_id=comment_id, user_id=user_id).first()
    if not comment:
        return None
    db.session.delete(comment)
    db.session.commit()
    return {"message": "Comment deleted successfully", "comment_id": comment_id}

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

def create_post(user_id, title, content):
    now = datetime.now()
    new_post = Post(
        user_id=user_id,
        title=title,
        content=content,
        created_at=now,
        updated_at=now
    )
    db.session.add(new_post)
    db.session.commit()
    return new_post.to_dict()

def create_comment(user_id, post_id, content):
    now = datetime.now()
    new_comment = Comment(
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
    print("here 1")
    print(f"res: {res}")
    if not res:
        # Create a new vote
        if vote_direction.value == 'up':
            print("here 2")
            inc_comment_upvotes(comment_id)
        elif vote_direction.value == 'down':
            print("here 3")
            inc_comment_dnvotes(comment_id)
        else:
            print("here 4")
            raise ValueError("wtf")
        new_vote = CommentVotes(
            comment_id=comment_id,
            user_id=user_id,
            vote_direction=vote_direction
        )
        print("here 5")
        db.session.add(new_vote)
        print("here 6")
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
    print("here 7")
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