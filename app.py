from flask import Flask, render_template, request, make_response, redirect, url_for, jsonify
from weasyprint import HTML, CSS
import os
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
import csv
from werkzeug.utils import secure_filename
import base64
from database import db
from models import Quote, LineItem

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quotes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
db.init_app(app)

with app.app_context():
    db.create_all()

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Function to generate ID
def generate_id(prefix: str) -> str:
    utc_now = datetime.now(timezone.utc)
    return f"{prefix}{utc_now.strftime('%Y%m%d%H%M%S')}"

# Function to log ID to a CSV file
def log_id(id_type: str, unique_id: str):
    log_file = f"{id_type.lower()}_log.csv"
    file_exists = os.path.isfile(log_file)
    with open(log_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Type", "ID", "Generated_UTC"])
        writer.writerow([id_type.upper(), unique_id, datetime.now(timezone.utc).isoformat()])

@app.route('/')
def index():
    return redirect(url_for('quote_form'))

@app.route('/quote')
def quote_form():
    return render_template('index.html')

@app.route('/po')
def po_form():
    return render_template('po_form.html')

@app.route('/api/quotes', methods=['GET'])
def get_quotes():
    quotes = Quote.query.order_by(Quote.created_at.desc()).all()
    return jsonify([{
        'id': quote.id,
        'doc_number': quote.doc_number,
        'document_type': quote.document_type,
        'quote_name': quote.quote_name,
        'po_name': quote.po_name,
        'created_at': quote.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for quote in quotes])

@app.route('/api/quotes', methods=['POST'])
def create_quote():
    data = request.get_json()
    doc_type = data.get('document_type', 'quote')
    prefix = 'EVTPO' if doc_type == 'po' else 'EVTQ'
    doc_number = generate_id(prefix)

    new_quote = Quote(
        document_type=doc_type,
        quote_name=data.get('quote_name'),
        quote_date=data.get('quote_date'),
        notes=data.get('notes'),
        doc_number=doc_number,
        po_name=data.get('po_name'),
        po_date=data.get('po_date'),
        payment_terms=data.get('payment_terms'),
        shipping_name=data.get('shipping_name'),
        shipping_address=data.get('shipping_address'),
        shipping_city_state_zip=data.get('shipping_city_state_zip'),
        billing_name=data.get('billing_name'),
        billing_address=data.get('billing_address'),
        billing_city_state_zip=data.get('billing_city_state_zip'),
        supplier_name=data.get('supplier_name'),
        supplier_quote=data.get('supplier_quote'),
        supplier_contact=data.get('supplier_contact'),
        end_user_name=data.get('end_user_name'),
        end_user_po=data.get('end_user_po'),
        end_user_contact=data.get('end_user_contact'),
        po_amount=data.get('po_amount')
    )

    if 'company_logo_data' in data and data['company_logo_data']:
        # Handle base64 encoded image
        header, encoded = data['company_logo_data'].split(',', 1)
        image_data = base64.b64decode(encoded)
        filename = secure_filename(f"{doc_number}_logo.png")
        logo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        with open(logo_path, 'wb') as f:
            f.write(image_data)
        new_quote.company_logo = filename

    for item_data in data.get('items', []):
        line_item = LineItem(
            item_type=item_data['type'],
            title=item_data.get('title'),
            part_number=item_data.get('part_number'),
            description=item_data.get('description'),
            item_category=item_data.get('item_type'),  # Store the actual item type from form
            unit_price=float(item_data.get('unit_price', 0) or 0),
            quantity=int(item_data.get('quantity', 0) or 0),
            discounted_price=float(item_data.get('discounted_price', 0) or 0)
        )
        line_item.extended_price = line_item.quantity * line_item.discounted_price
        new_quote.items.append(line_item)
        
        # Add subcomponents if they exist
        for subcomponent_data in item_data.get('subcomponents', []):
            from models import Subcomponent
            subcomponent = Subcomponent(
                description=subcomponent_data['description'],
                quantity=int(subcomponent_data.get('quantity', 1))
            )
            line_item.subcomponents.append(subcomponent)

    db.session.add(new_quote)
    db.session.commit()
    log_id(doc_type, doc_number)

    return jsonify({'id': new_quote.id, 'doc_number': new_quote.doc_number})

@app.route('/quote/<int:quote_id>/pdf')
def generate_pdf(quote_id):
    quote = Quote.query.get_or_404(quote_id)
    
    # Prepare data for the template
    data = quote.__dict__
    data['doc_type_display'] = 'Purchase Order' if quote.document_type == 'po' else 'Quote'
    data['document_name'] = quote.po_name if quote.document_type == 'po' else quote.quote_name
    data['document_date'] = quote.po_date if quote.document_type == 'po' else quote.quote_date

    # Handle logo
    logo_base64 = None
    if quote.company_logo:
        logo_path = os.path.join(app.config['UPLOAD_FOLDER'], quote.company_logo)
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as image_file:
                logo_base64 = base64.b64encode(image_file.read()).decode('utf-8')
    data['logo_base64'] = logo_base64

    # Handle expiration date for quotes
    if quote.document_type == 'quote' and quote.quote_date:
        try:
            quote_date = datetime.strptime(quote.quote_date, '%Y-%m-%d')
            expiration_date = quote_date + relativedelta(months=1)
            data['expiration_date'] = expiration_date.strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            data['expiration_date'] = 'N/A'
    else:
        data['expiration_date'] = 'N/A'

    # Prepare line items
    items_for_template = []
    for item in quote.items:
        item_dict = {
            'type': item.item_type,
            'title': item.title,
            'part_number': item.part_number,
            'description': item.description,
            'item_type': item.item_category,  # Use the actual item type from form
            'unit_price': item.unit_price or 0,
            'quantity': item.quantity or 0,
            'discounted_price': item.discounted_price or 0,
            'extended_price': item.extended_price or 0
        }
        items_for_template.append(item_dict)
    data['items'] = items_for_template

    filename = f"{quote.document_type}_{quote.doc_number}.pdf"

    html_out = render_template('pdf_template.html', data=data)
    pdf = HTML(string=html_out, base_url=request.host_url).write_pdf()
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename={filename}'
    return response

@app.route('/api/quote/<int:quote_id>', methods=['GET'])
def get_quote(quote_id):
    quote = Quote.query.get_or_404(quote_id)
    quote_data = {
        'id': quote.id,
        'document_type': quote.document_type,
        'quote_name': quote.quote_name,
        'quote_date': quote.quote_date,
        'notes': quote.notes,
        'doc_number': quote.doc_number,
        'po_name': quote.po_name,
        'po_date': quote.po_date,
        'payment_terms': quote.payment_terms,
        'shipping_name': quote.shipping_name,
        'shipping_address': quote.shipping_address,
        'shipping_city_state_zip': quote.shipping_city_state_zip,
        'billing_name': quote.billing_name,
        'billing_address': quote.billing_address,
        'billing_city_state_zip': quote.billing_city_state_zip,
        'supplier_name': quote.supplier_name,
        'supplier_quote': quote.supplier_quote,
        'supplier_contact': quote.supplier_contact,
        'end_user_name': quote.end_user_name,
        'end_user_po': quote.end_user_po,
        'end_user_contact': quote.end_user_contact,
        'po_amount': quote.po_amount,
        'items': [{
            'id': item.id,
            'type': item.item_type,
            'title': item.title,
            'part_number': item.part_number,
            'description': item.description,
            'item_type': item.item_category,  # Use the actual item type from form
            'unit_price': item.unit_price,
            'quantity': item.quantity,
            'discounted_price': item.discounted_price,
            'extended_price': item.extended_price,
            'subcomponents': [{
                'id': sub.id,
                'description': sub.description,
                'quantity': sub.quantity
            } for sub in item.subcomponents]
        } for item in quote.items]
    }
    return jsonify(quote_data)

@app.route('/api/quote/<int:quote_id>', methods=['PUT'])
def update_quote(quote_id):
    quote = Quote.query.get_or_404(quote_id)
    data = request.get_json()

    # Update fields
    quote.document_type = data.get('document_type', quote.document_type)
    quote.quote_name = data.get('quote_name', quote.quote_name)
    quote.quote_date = data.get('quote_date', quote.quote_date)
    quote.notes = data.get('notes', quote.notes)
    quote.po_name = data.get('po_name', quote.po_name)
    quote.po_date = data.get('po_date', quote.po_date)
    quote.payment_terms = data.get('payment_terms', quote.payment_terms)
    quote.shipping_name = data.get('shipping_name', quote.shipping_name)
    quote.shipping_address = data.get('shipping_address', quote.shipping_address)
    quote.shipping_city_state_zip = data.get('shipping_city_state_zip', quote.shipping_city_state_zip)
    quote.billing_name = data.get('billing_name', quote.billing_name)
    quote.billing_address = data.get('billing_address', quote.billing_address)
    quote.billing_city_state_zip = data.get('billing_city_state_zip', quote.billing_city_state_zip)
    quote.supplier_name = data.get('supplier_name', quote.supplier_name)
    quote.supplier_quote = data.get('supplier_quote', quote.supplier_quote)
    quote.supplier_contact = data.get('supplier_contact', quote.supplier_contact)
    quote.end_user_name = data.get('end_user_name', quote.end_user_name)
    quote.end_user_po = data.get('end_user_po', quote.end_user_po)
    quote.end_user_contact = data.get('end_user_contact', quote.end_user_contact)
    quote.po_amount = data.get('po_amount', quote.po_amount)

    # Clear existing line items
    for item in quote.items:
        db.session.delete(item)

    # Add new line items
    for item_data in data.get('items', []):
        line_item = LineItem(
            item_type=item_data['type'],
            title=item_data.get('title'),
            part_number=item_data.get('part_number'),
            description=item_data.get('description'),
            item_category=item_data.get('item_type'),  # Store the actual item type from form
            unit_price=float(item_data.get('unit_price', 0) or 0),
            quantity=int(item_data.get('quantity', 0) or 0),
            discounted_price=float(item_data.get('discounted_price', 0) or 0)
        )
        line_item.extended_price = line_item.quantity * line_item.discounted_price
        quote.items.append(line_item)

    db.session.commit()
    return jsonify({'message': 'Quote updated successfully'})

@app.route('/api/quote/<int:quote_id>', methods=['DELETE'])
def delete_quote(quote_id):
    quote = Quote.query.get_or_404(quote_id)
    db.session.delete(quote)
    db.session.commit()
    return jsonify({'message': 'Quote deleted successfully'})

if __name__ == '__main__':
    app.run(debug=True, port=5001)
