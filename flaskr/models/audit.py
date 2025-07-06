from flaskr.extensions import db
import enum

class AccountType(enum.Enum):
    SuperUser = 'super_user'

class Action(enum.Enum):
    CREATE = 'create'
    UPDATE = 'update'
    DELETE = 'delete'

class UserAudit(db.Model):
    __tablename__ = 'user_audit'

    audit_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    username_old = db.Column(db.String(80), nullable=False)
    username_new = db.Column(db.String(80), nullable=False)
    password_old = db.Column(db.String(255), nullable=False)
    password_new = db.Column(db.String(255), nullable=False)
    account_type_old = db.Column(db.Enum(AccountType), nullable=False)
    account_type_new = db.Column(db.Enum(AccountType), nullable=False)
    created_at_old = db.Column(db.DateTime, server_default=db.func.now())
    created_at_new = db.Column(db.DateTime, server_default=db.func.now())
    updated_at_old = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    updated_at_new = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    action = db.Column(db.Enum(Action), nullable=False)
    audit_timestamp = db.Column(db.DateTime, server_default=db.func.now())
    audit_user = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
