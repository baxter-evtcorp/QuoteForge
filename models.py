from database import db
from datetime import datetime

class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    document_type = db.Column(db.String(50), nullable=False)
    quote_name = db.Column(db.String(100), nullable=True)
    quote_date = db.Column(db.String(50), nullable=True)
    company_logo = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    doc_number = db.Column(db.String(50), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='draft')  # draft, approved

    # Fields for PO
    po_name = db.Column(db.String(100), nullable=True)
    po_date = db.Column(db.String(50), nullable=True)
    payment_terms = db.Column(db.String(100), nullable=True)
    shipping_name = db.Column(db.String(100), nullable=True)
    shipping_address = db.Column(db.String(200), nullable=True)
    shipping_city_state_zip = db.Column(db.String(100), nullable=True)
    billing_name = db.Column(db.String(100), nullable=True)
    billing_address = db.Column(db.String(200), nullable=True)
    billing_city_state_zip = db.Column(db.String(100), nullable=True)
    supplier_name = db.Column(db.String(100), nullable=True)
    supplier_quote = db.Column(db.String(100), nullable=True)
    supplier_contact = db.Column(db.String(100), nullable=True)
    end_user_name = db.Column(db.String(100), nullable=True)
    end_user_po = db.Column(db.String(100), nullable=True)
    end_user_contact = db.Column(db.String(100), nullable=True)
    po_amount = db.Column(db.String(50), nullable=True)

    items = db.relationship('LineItem', backref='quote', lazy=True, cascade="all, delete-orphan")

class LineItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey('quote.id'), nullable=False)
    item_type = db.Column(db.String(50), nullable=False)  # 'section' or 'item'
    title = db.Column(db.String(100), nullable=True)  # For sections
    part_number = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    item_category = db.Column(db.String(100), nullable=True)  # The actual item type from form
    unit_price = db.Column(db.Float, nullable=True)
    quantity = db.Column(db.Integer, nullable=True)
    discounted_price = db.Column(db.Float, nullable=True)
    extended_price = db.Column(db.Float, nullable=True)

    subcomponents = db.relationship('Subcomponent', backref='line_item', lazy=True, cascade="all, delete-orphan")

class Subcomponent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    line_item_id = db.Column(db.Integer, db.ForeignKey('line_item.id'), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
