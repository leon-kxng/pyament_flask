from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    CheckoutRequestID = db.Column(db.String(100))
    ResultCode = db.Column(db.Integer)
    Amount = db.Column(db.Float)
    MpesaReceiptNumber = db.Column(db.String(100))
    PhoneNumber = db.Column(db.String(20))

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), unique=True)
    username = db.Column(db.String(100))
    password_hash = db.Column(db.String(128))  # Add password hash column
    profile_pic_id = db.Column(db.Integer, db.ForeignKey('image.id'))  # New column for profile picture ID
    profile_pic = db.relationship('Image', foreign_keys=[profile_pic_id])  # Relationship with the Image table

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_data = db.Column(db.LargeBinary)

