from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    CheckoutRequestID = db.Column(db.String(100))
    ResultCode = db.Column(db.Integer)
    Amount = db.Column(db.Float)
    MpesaReceiptNumber = db.Column(db.String(100))
    PhoneNumber = db.Column(db.String(20))
