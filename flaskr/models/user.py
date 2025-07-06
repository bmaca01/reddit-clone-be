from werkzeug.security import generate_password_hash, check_password_hash
from flaskr.extensions import db
from flaskr.struct import AccountType

class User(db.Model):
    __tablename__ = 'user'
    
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(512), nullable=False)
    account_type = db.Column(db.Enum(AccountType), nullable=False, default=AccountType.REGULAR)
    address_id = db.Column(db.Integer, db.ForeignKey('address.address_id'), nullable=True)

    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    address = db.relationship('Address', backref=db.backref('user', lazy=True))

    post_votes = db.relationship('PostVotes', back_populates='user', cascade='all, delete-orphan')
    comment_votes = db.relationship('CommentVotes', back_populates='user', cascade='all, delete-orphan')

    def __init__(self, username, password, address_id=None, account_type=AccountType.REGULAR):
        self.username = username
        self.password = generate_password_hash(password)
        self.address_id = address_id
        self.account_type = account_type

    @classmethod
    def authenticate(cls, **kwargs):
        username = kwargs.get('username')
        password = kwargs.get('password')

        if not (username and password):
            return None
        
        user = cls.query.filter_by(username=username).first()
        if not (user and check_password_hash(user.password, password)):
            return None
        
        return user

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "username": self.username,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class SuperUser(db.Model):
    __tablename__ = 'super_user'
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), primary_key=True)
    user = db.relationship('User', backref=db.backref('super_user', uselist=False))

    def to_dict(self):
        return {
            "user_id": self.user_id
        }