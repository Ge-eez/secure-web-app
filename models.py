import uuid

from flask_security import RoleMixin, UserMixin
from sqlalchemy_utils import UUIDType

from application import db

roles_users = db.Table(
    "roles_users",
    db.Column("user_id", db.Integer(), db.ForeignKey("user.id")),
    db.Column("role_id", db.Integer(), db.ForeignKey("role.id")),
)


class Role(db.Model, RoleMixin):
    __tablename__ = "role"
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    fs_uniquifier = db.Column(
        UUIDType(binary=False), default=uuid.uuid4, unique=True, nullable=False
    )
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    username = db.Column(db.String(200), nullable=True)
    roles = db.relationship(
        "Role", secondary=roles_users, backref=db.backref("user", lazy="dynamic")
    )
    active = db.Column(db.Boolean())


class Feedback(db.Model):
    __tablename__ = "feedbacks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    content = db.Column(db.Text)
    attachment = db.Column(db.String)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    reviewed = db.Column(db.Boolean, default=False)
    review_timestamp = db.Column(db.DateTime)
    user = db.relationship("User", backref=db.backref("feedbacks", lazy=True))


db.create_all()
