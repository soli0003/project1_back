from datetime import datetime
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.sqlite3'
app.config['SECRET_KEY'] = "random string"


db = SQLAlchemy(app)


# Model
class Book(db.Model):
    id = db.Column('book_id', db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    author = db.Column(db.String(50))
    year_published = db.Column(db.String(200))
    book_type = db.Column(db.Integer)
    loan_active = db.Column(db.Boolean, default=False)
    book_deleted = db.Column(db.Boolean, default=False)
   

    def __init__(self, name, author, year_published, book_type, loan_active, book_deleted):
        self.name = name
        self.author = author
        self.year_published = year_published
        self.book_type = book_type
        self.loan_active = loan_active
        self.book_deleted = book_deleted

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'author': self.author,
            'year_published': self.year_published,
            'book_type': self.book_type,
            'loan_active': self.loan_active,
            'book_deleted': self.book_deleted
        }



class Customer(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    identification_number = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone = db.Column(db.Integer)
    city = db.Column(db.String(50))
    age = db.Column(db.Integer)
    active = db.Column(db.Boolean, default=True)

    def __init__(self, identification_number, name, email, phone, city, age, active):
        self.identification_number = identification_number
        self.name = name
        self.email = email
        self.phone = phone
        self.city = city
        self.age = age
        self.active = active

    def to_dict(self):
        return {
            'id': self.id,
            'identification_number': self.identification_number,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'city': self.city,
            'age': self.age,
            'active': self.active
        }


class Loan(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    cust_id = db.Column('cust_id', db.Integer, db.ForeignKey('customer.id'))
    book_id = db.Column('book_id', db.Integer, db.ForeignKey('book.book_id'))
    loan_date = db.Column('loan_date', db.Date)
    return_date = db.Column('return_date', db.Date)

    book = db.relationship("Book", backref="loans", foreign_keys=[book_id])
    customer = db.relationship("Customer", backref="loans", foreign_keys=[cust_id])

    def __init__(self, cust_id, book_id, loan_date, return_date):
        self.cust_id = cust_id
        self.book_id = book_id
        self.loan_date = loan_date
        self.return_date = return_date

    def to_dict(self):
        return {
            'id': self.id,
            'cust_id': self.cust_id,
            'book_id': self.book_id,
            'loan_date': self.loan_date,
            'return_date': self.return_date
        }
