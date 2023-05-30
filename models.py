import os
from application import db, bcrypt


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    feedbacks = db.relationship("Feedback", backref="user", lazy=True)


class Feedback(db.Model):
    __tablename__ = "feedbacks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    content = db.Column(db.Text)
    attachment = db.Column(db.String)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    reviewed = db.Column(db.Boolean, default=False)
    review_timestamp = db.Column(db.DateTime)


class Admin(db.Model):
    __tablename__ = "admin"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)


db.create_all()

# Hash the password
hashed_password = bcrypt.generate_password_hash(os.getenv("ADMIN_PASSWORD")).decode(
    "utf-8"
)

# Create a new admin instance
new_admin = Admin(username="admin", password=hashed_password)

# Add the new admin to the session
db.session.add(new_admin)

# Commit the session to save the new admin in the database
db.session.commit()
