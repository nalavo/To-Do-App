from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import date
from sqlalchemy import Time


db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    tasks = db.relationship('Task', backref='user', lazy=True)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(200), nullable=False)
    due_date = db.Column(db.Date, nullable=True)  # 🆕 New column
    done = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    priority = db.Column(db.String(10), nullable=True)  # 'Low', 'Medium', 'High'
