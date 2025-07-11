from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import Boolean, Integer


db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    wants_email = db.Column(Boolean, default=True)  # wants mail?
    email_hour = db.Column(Integer, default=9)      # what time user wants the mail send

class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    user = db.relationship('User', backref='cities')
