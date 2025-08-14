from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Bill(db.Model):
    __tablename__ = 'bills'
    id = db.Column(db.Integer, primary_key=True)
    vendor = db.Column(db.String(255))
    total = db.Column(db.Float)
    tax = db.Column(db.Float) 
    date = db.Column(db.Date)
    filename = db.Column(db.String(255))
    user_id = db.Column(db.Integer, nullable=False)

class BillItem(db.Model):
    __tablename__ = 'bill_items'
    id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.Integer)
    name = db.Column(db.String(255))
    quantity = db.Column(db.Integer)
    price = db.Column(db.Float)

class UserInsight(db.Model):
    __tablename__ = 'user_insights'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    bill_id = db.Column(db.Integer, nullable=True)
    insight_text = db.Column(db.Text, nullable=False)
    insight_type = db.Column(db.String(50), default='per_bill')
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
