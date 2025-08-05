from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vendor = db.Column(db.String(255))
    tax = db.Column(db.String(50))
    total = db.Column(db.String(50))
    currency = db.Column(db.String(10))
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    items = db.relationship('BillItem', backref='bill', lazy=True)

class BillItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.Integer, db.ForeignKey('bill.id'), nullable=False)
    name = db.Column(db.String(255))
    price = db.Column(db.Float)
