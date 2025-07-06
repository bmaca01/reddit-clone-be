from flaskr.extensions import db
from flaskr.struct import VoteDirection

class PostVotes(db.Model):
    __tablename__ = 'post_votes'

    post_id = db.Column(db.Integer, db.ForeignKey('post.post_id'), primary_key=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), primary_key=True, nullable=False)
    vote_direction = db.Column(db.Enum(VoteDirection), default=VoteDirection.NONE, nullable=False)

    user = db.relationship('User', back_populates='post_votes')
    post = db.relationship('Post', back_populates='votes')

    def to_dict(self):
        result = {
            'post_id': self.post_id,
            'user_id': self.user_id,
            'vote_direction': self.vote_direction.value
        }
        return result

class CommentVotes(db.Model):
    __tablename__ = 'comment_votes'

    comment_id = db.Column(db.Integer, db.ForeignKey('comment.comment_id'), primary_key=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), primary_key=True, nullable=False)
    vote_direction = db.Column(db.Enum(VoteDirection), default=VoteDirection.NONE, nullable=False)

    user = db.relationship('User', back_populates='comment_votes')
    comment = db.relationship('Comment', back_populates='votes')

    def to_dict(self):
        result = {
            'comment_id': self.comment_id,
            'user_id': self.user_id,
            'vote_direction': self.vote_direction.value
        }
        return result