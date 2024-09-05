from applications.database import db
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


user_books = db.Table('user_books',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('book_id', db.Integer, db.ForeignKey('book.id'), primary_key=True)
)


    
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    book_requests = db.relationship('BookRequest', backref='user', lazy='dynamic')
    owned_books = db.relationship('Book', secondary=user_books, lazy='dynamic', backref=db.backref('owners', lazy='dynamic'))


class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(80))


class BookSection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(300))
    books = db.relationship('Book', backref='section', lazy='dynamic')

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    isbn = db.Column(db.String(13), nullable=False, unique=True)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    section_id = db.Column(db.Integer, db.ForeignKey('book_section.id'), nullable=True)
    content = db.Column(db.Text, nullable=True)
  
    def can_be_requested(self):
        return self.quantity > 0

class BookRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    status = db.Column(db.String(50), default='pending')  
    requested_on = db.Column(db.DateTime, default=datetime.utcnow)
    book = db.relationship('Book', backref='requests', lazy=True)




    def __repr__(self):
        return f"<Product {self.name}>"
    
