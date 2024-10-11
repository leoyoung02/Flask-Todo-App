from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    due_date = db.Column(db.DateTime, nullable=True)  # New: Due date
    is_completed = db.Column(db.Boolean, default=False)  # New: Completion status
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    todos = db.relationship('Todo')