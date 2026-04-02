from dotenv import load_dotenv
load_dotenv(override=True)

from flask import Flask, render_template, request, make_response, redirect, url_for, jsonify
from pdf_gen import generate_quote_pdf
import os
import json
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from werkzeug.utils import secure_filename
import base64
from database import db
from models import Quote, LineItem, Subcomponent, ManufacturerMapping
from utils import generate_id, log_id
from import_parser import parse_file
from ai_mapper import suggest_mapping, analyze_pdf_content

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URI', 'sqlite:///quotes.db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads')
db.init_app(app)

with app.app_context():
    db.create_all()

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])


def build_line_item(item_data):
    """Build a LineItem with its Subcomponents from request data."""
    try:
        unit_price = float(item_data.get('unit_price', 0) or 0)
        quantity = int(item_data.get('quantity', 0) or 0)
        discounted_price = float(item_data.get('discounted_price', 0) or 0)
    except (ValueError, TypeError):
        unit_price = 0.0
        quantity = 0
        discounted_price = 0.0

    line_item = LineItem(
        item_type=item_data.get('type', 'item'),
        title=item_data.get('title'),
        part_number=item_data.get('part_number'),
        description=item_data.get('description'),
        item_category=item_data.get('item_type'),
        unit_price=unit_price,
        quantity=quantity,
        discounted_price=discounted_price
    )
    line_item.extended_price = line_item.quantity * line_item.discounted_price

    for sub_data in item_data.get('subcomponents', []):
        try:
            sub_qty = int(sub_data.get('quantity', 1))
        except (ValueError, TypeError):
            sub_qty = 1
        subcomponent = Subcomponent(
            description=sub_data.get('description', ''),
            quantity=sub_qty
        )
        line_item.subcomponents.append(subcomponent)

    return line_item


def serialize_line_item(item, include_id=False):
    """Serialize a LineItem to a dict."""
    result = {
        'type': item.item_type,
        'title': item.title,
        'part_number': item.part_number,
        'description': item.description,
        'item_type': item.item_category,
        'unit_price': item.unit_price,
        'quantity': item.quantity,
        'discounted_price': item.discounted_price,
        'extended_price': item.extended_price,
        'subcomponents': [{
            'description': sub.description,
            'quantity': sub.quantity,
            **(({'id': sub.id}) if include_id else {})
        } for sub in item.subcomponents]
    }
    if include_id:
        result['id'] = item.id
    return result


def serialize_quote(quote, include_items=False, include_ids=False):
    """Serialize a Quote to a dict, avoiding __dict__ leak."""
    data = {
        'id': quote.id,
        'document_type': quote.document_type,
        'doc_number': quote.doc_number,
        'quote_name': quote.quote_name,
        'quote_date': quote.quote_date,
        'status': quote.status,
        'notes': quote.notes,
        'company_logo': quote.company_logo,
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
        'customer_name': quote.customer_name,
        'supplier_number': quote.supplier_number,
        'cw_number': quote.cw_number,
        'ma_number': quote.ma_number,
    }
    if include_items:
        data['items'] = [serialize_line_item(item, include_id=include_ids) for item in quote.items]
    return data


def decode_logo(data_uri, doc_number):
    """Decode a base64 logo data URI and save to uploads. Returns filename or None."""
    try:
        header, encoded = data_uri.split(',', 1)
        image_data = base64.b64decode(encoded)
    except (ValueError, base64.binascii.Error):
        return None
    filename = secure_filename(f"{doc_number}_logo.png")
    logo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    with open(logo_path, 'wb') as f:
        f.write(image_data)
    return filename


@app.route('/health')
def health():
    return jsonify({'status': 'ok'})


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
        'id': q.id,
        'doc_number': q.doc_number,
        'document_type': q.document_type,
        'quote_name': q.quote_name,
        'po_name': q.po_name,
        'status': q.status,
        'created_at': q.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for q in quotes])


@app.route('/api/quotes', methods=['POST'])
def create_quote():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400

    doc_type = data.get('document_type', 'quote')
    if doc_type not in ('quote', 'po'):
        return jsonify({'error': 'document_type must be "quote" or "po"'}), 400

    prefix = 'EVTPO' if doc_type == 'po' else 'EVTQ'
    doc_number = generate_id(prefix)

    new_quote = Quote(
        document_type=doc_type,
        quote_name=data.get('quote_name'),
        quote_date=data.get('quote_date'),
        notes=data.get('notes'),
        doc_number=doc_number,
        status=data.get('status', 'draft'),
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
        po_amount=data.get('po_amount'),
        customer_name=data.get('customer_name'),
        supplier_number=data.get('supplier_number'),
        cw_number=data.get('cw_number'),
        ma_number=data.get('ma_number'),
    )

    logo_data = data.get('company_logo_data')
    if logo_data:
        filename = decode_logo(logo_data, doc_number)
        if filename:
            new_quote.company_logo = filename

    for item_data in data.get('items', []):
        new_quote.items.append(build_line_item(item_data))

    db.session.add(new_quote)
    db.session.commit()
    log_id(doc_type, doc_number)

    return jsonify({'id': new_quote.id, 'doc_number': new_quote.doc_number})


@app.route('/quote/<int:quote_id>/pdf')
def generate_pdf(quote_id):
    quote = Quote.query.get_or_404(quote_id)

    data = serialize_quote(quote, include_items=True)
    data['doc_type_display'] = 'Purchase Order' if quote.document_type == 'po' else 'Quote'
    data['document_name'] = quote.po_name if quote.document_type == 'po' else quote.quote_name
    data['document_date'] = quote.po_date if quote.document_type == 'po' else quote.quote_date

    # Logo path for fpdf2
    logo_path = None
    if quote.company_logo:
        lp = os.path.join(app.config['UPLOAD_FOLDER'], quote.company_logo)
        if os.path.exists(lp):
            logo_path = lp
    if not logo_path:
        default_logo = os.path.join(app.static_folder, 'images', 'EVT_logo.png')
        if os.path.exists(default_logo):
            logo_path = default_logo
    data['logo_path'] = logo_path

    if quote.document_type == 'quote' and quote.quote_date:
        try:
            quote_date = datetime.strptime(quote.quote_date, '%Y-%m-%d')
            expiration_date = quote_date + relativedelta(months=1)
            data['expiration_date'] = expiration_date.strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            data['expiration_date'] = 'N/A'
    else:
        data['expiration_date'] = 'N/A'

    filename = f"{quote.document_type}_{quote.doc_number}.pdf"
    pdf_bytes = generate_quote_pdf(data)
    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename={filename}'
    return response


@app.route('/api/quote/<int:quote_id>', methods=['GET'])
def get_quote(quote_id):
    quote = Quote.query.get_or_404(quote_id)
    return jsonify(serialize_quote(quote, include_items=True, include_ids=True))


@app.route('/api/quote/<int:quote_id>', methods=['PUT'])
def update_quote(quote_id):
    quote = Quote.query.get_or_404(quote_id)
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400

    quote.document_type = data.get('document_type', quote.document_type)
    quote.quote_name = data.get('quote_name', quote.quote_name)
    quote.quote_date = data.get('quote_date', quote.quote_date)
    quote.status = data.get('status', quote.status)
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
    quote.customer_name = data.get('customer_name', quote.customer_name)
    quote.supplier_number = data.get('supplier_number', quote.supplier_number)
    quote.cw_number = data.get('cw_number', quote.cw_number)
    quote.ma_number = data.get('ma_number', quote.ma_number)

    for item in quote.items:
        db.session.delete(item)

    for item_data in data.get('items', []):
        quote.items.append(build_line_item(item_data))

    db.session.commit()
    return jsonify({'message': 'Quote updated successfully'})


@app.route('/api/quote/<int:quote_id>', methods=['DELETE'])
def delete_quote(quote_id):
    quote = Quote.query.get_or_404(quote_id)
    db.session.delete(quote)
    db.session.commit()
    return jsonify({'message': 'Quote deleted successfully'})


@app.route('/api/quote/<int:quote_id>/copy', methods=['POST'])
def copy_quote(quote_id):
    original_quote = Quote.query.get_or_404(quote_id)

    doc_type = original_quote.document_type
    prefix = 'EVTPO' if doc_type == 'po' else 'EVTQ'
    new_doc_number = generate_id(prefix)

    new_quote = Quote(
        document_type=original_quote.document_type,
        quote_name=f"Copy of {original_quote.quote_name}" if original_quote.quote_name else None,
        quote_date=original_quote.quote_date,
        company_logo=original_quote.company_logo,
        notes=original_quote.notes,
        doc_number=new_doc_number,
        po_name=f"Copy of {original_quote.po_name}" if original_quote.po_name else None,
        po_date=original_quote.po_date,
        payment_terms=original_quote.payment_terms,
        shipping_name=original_quote.shipping_name,
        shipping_address=original_quote.shipping_address,
        shipping_city_state_zip=original_quote.shipping_city_state_zip,
        billing_name=original_quote.billing_name,
        billing_address=original_quote.billing_address,
        billing_city_state_zip=original_quote.billing_city_state_zip,
        supplier_name=original_quote.supplier_name,
        supplier_quote=original_quote.supplier_quote,
        supplier_contact=original_quote.supplier_contact,
        end_user_name=original_quote.end_user_name,
        end_user_po=original_quote.end_user_po,
        end_user_contact=original_quote.end_user_contact,
        po_amount=original_quote.po_amount,
        customer_name=original_quote.customer_name,
        supplier_number=original_quote.supplier_number,
        cw_number=original_quote.cw_number,
        ma_number=original_quote.ma_number,
    )

    db.session.add(new_quote)
    db.session.flush()

    for original_item in original_quote.items:
        new_item = LineItem(
            quote_id=new_quote.id,
            item_type=original_item.item_type,
            title=original_item.title,
            part_number=original_item.part_number,
            description=original_item.description,
            item_category=original_item.item_category,
            unit_price=original_item.unit_price,
            quantity=original_item.quantity,
            discounted_price=original_item.discounted_price,
            extended_price=original_item.extended_price
        )
        db.session.add(new_item)
        db.session.flush()

        for original_sub in original_item.subcomponents:
            new_sub = Subcomponent(
                line_item_id=new_item.id,
                description=original_sub.description,
                quantity=original_sub.quantity
            )
            db.session.add(new_sub)

    db.session.commit()

    return jsonify({
        'id': new_quote.id,
        'doc_number': new_quote.doc_number,
        'message': 'Quote copied successfully'
    })


@app.route('/api/quote/<int:source_quote_id>/copy-section/<int:target_quote_id>', methods=['POST'])
def copy_section_to_quote(source_quote_id, target_quote_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400

    section_title = data.get('section_title')
    section_items = data.get('section_items', [])

    source_quote = Quote.query.get_or_404(source_quote_id)
    target_quote = Quote.query.get_or_404(target_quote_id)

    section_line_item = LineItem(
        item_type='section',
        title=f"{section_title} (Copied from {source_quote.doc_number})"
    )
    target_quote.items.append(section_line_item)

    for item_data in section_items:
        target_quote.items.append(build_line_item(item_data))

    db.session.commit()

    return jsonify({
        'message': f'Section copied successfully to {target_quote.doc_number}'
    })


# --- Import Wizard Routes ---

ALLOWED_IMPORT_EXTENSIONS = {'.csv', '.tsv', '.txt', '.xlsx', '.xls', '.pdf'}


@app.route('/import')
def import_wizard():
    return render_template('import.html')


@app.route('/api/import/upload', methods=['POST'])
def import_upload():
    """Upload and parse a manufacturer quote file."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'error': 'No file selected'}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_IMPORT_EXTENSIONS:
        return jsonify({'error': f'Unsupported file type: {ext}'}), 400

    # Save the file
    filename = secure_filename(f"import_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        result = parse_file(filepath, file.filename)
    except Exception as e:
        return jsonify({'error': f'Failed to parse file: {str(e)}'}), 400

    # Return parsed data with preview (first 5 rows)
    return jsonify({
        'file_id': filename,
        'original_filename': file.filename,
        'columns': result['columns'],
        'preview_rows': result['rows'][:5],
        'total_rows': len(result['rows']),
        'raw_text': result.get('raw_text'),
        'tables': result.get('tables', []),
        'selected_table_page': result.get('selected_table_page'),
    })


@app.route('/api/import/ai-map', methods=['POST'])
def import_ai_map():
    """Use AI to suggest column mappings."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400

    columns = data.get('columns', [])
    sample_rows = data.get('sample_rows', [])
    manufacturer_name = data.get('manufacturer_name')
    raw_text = data.get('raw_text')

    # If raw text is provided (PDF fallback), use AI to extract structure
    if raw_text and not columns:
        pdf_result = analyze_pdf_content(raw_text, manufacturer_name)
        if pdf_result and pdf_result.get('columns'):
            return jsonify({
                'pdf_extraction': pdf_result,
                'mapping': {col: col for col in pdf_result['columns']},
                'confidence': {col: 'high' for col in pdf_result['columns']},
                'unmapped': [],
                'ai_available': True,
            })
        return jsonify({
            'error': 'Could not extract structured data from PDF',
            'ai_available': bool(os.environ.get('ANTHROPIC_API_KEY')),
        }), 400

    result = suggest_mapping(columns, sample_rows, manufacturer_name)
    return jsonify(result)


@app.route('/api/import/mappings', methods=['GET'])
def get_mappings():
    """List all saved manufacturer mappings."""
    mappings = ManufacturerMapping.query.order_by(ManufacturerMapping.manufacturer_name).all()
    return jsonify([{
        'id': m.id,
        'manufacturer_name': m.manufacturer_name,
        'column_map': json.loads(m.column_map),
        'file_format_hints': json.loads(m.file_format_hints) if m.file_format_hints else None,
        'updated_at': m.updated_at.strftime('%Y-%m-%d %H:%M:%S') if m.updated_at else None,
    } for m in mappings])


@app.route('/api/import/mappings/<name>', methods=['GET'])
def get_mapping(name):
    """Get a specific manufacturer mapping by name."""
    mapping = ManufacturerMapping.query.filter_by(manufacturer_name=name).first()
    if not mapping:
        return jsonify({'error': 'Mapping not found'}), 404
    return jsonify({
        'id': mapping.id,
        'manufacturer_name': mapping.manufacturer_name,
        'column_map': json.loads(mapping.column_map),
        'file_format_hints': json.loads(mapping.file_format_hints) if mapping.file_format_hints else None,
    })


@app.route('/api/import/mappings', methods=['POST'])
def save_mapping():
    """Create or update a manufacturer mapping."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400

    name = data.get('manufacturer_name', '').strip()
    column_map = data.get('column_map')

    if not name or not column_map:
        return jsonify({'error': 'manufacturer_name and column_map are required'}), 400

    # Upsert
    mapping = ManufacturerMapping.query.filter_by(manufacturer_name=name).first()
    if mapping:
        mapping.column_map = json.dumps(column_map)
        mapping.file_format_hints = json.dumps(data.get('file_format_hints')) if data.get('file_format_hints') else mapping.file_format_hints
        mapping.updated_at = datetime.utcnow()
    else:
        mapping = ManufacturerMapping(
            manufacturer_name=name,
            column_map=json.dumps(column_map),
            file_format_hints=json.dumps(data.get('file_format_hints')) if data.get('file_format_hints') else None,
        )
        db.session.add(mapping)

    db.session.commit()
    return jsonify({'message': f'Mapping saved for {name}', 'id': mapping.id})


@app.route('/api/import/process', methods=['POST'])
def import_process():
    """Apply column mapping to the full uploaded file and return mapped items."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400

    file_id = data.get('file_id')
    column_map = data.get('column_map', {})
    pdf_rows = data.get('pdf_rows')  # Pre-extracted rows from AI PDF analysis

    if not file_id and not pdf_rows:
        return jsonify({'error': 'file_id or pdf_rows required'}), 400

    if pdf_rows:
        # Use AI-extracted PDF data directly
        rows = pdf_rows
        columns = data.get('pdf_columns', ['part_number', 'description', 'item_category', 'unit_price', 'quantity'])
    else:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file_id)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404

        try:
            result = parse_file(filepath, file_id)
        except Exception as e:
            return jsonify({'error': f'Failed to parse file: {str(e)}'}), 400

        columns = result['columns']
        rows = result['rows']

    # Build reverse map: source column index -> evt field
    # Support both name-based and index-based mapping keys
    col_index_map = {}
    for source_col, evt_field in column_map.items():
        if evt_field and evt_field != 'skip':
            # Check if the key is a numeric index (e.g., "col_3")
            if source_col.startswith('col_'):
                try:
                    idx = int(source_col.split('_', 1)[1])
                    col_index_map[idx] = evt_field
                    continue
                except (ValueError, IndexError):
                    pass
            # Name-based lookup -- handle duplicate/empty column names
            # by finding the first matching column not already mapped
            mapped_indices = set(col_index_map.keys())
            for idx, col_name in enumerate(columns):
                if col_name == source_col and idx not in mapped_indices:
                    col_index_map[idx] = evt_field
                    break

    # Transform rows using mapping
    items = []
    for row in rows:
        item = {
            'part_number': '',
            'description': '',
            'item_category': '',
            'unit_price': 0,
            'quantity': 1,
        }

        for idx, evt_field in col_index_map.items():
            if idx < len(row):
                value = row[idx]
                if evt_field == 'unit_price':
                    # Clean and parse price - handle "$31,680 per Year", "($1,909)", etc.
                    cleaned = str(value)
                    is_negative = '(' in cleaned and ')' in cleaned
                    cleaned = cleaned.replace('$', '').replace(',', '').replace('(', '').replace(')', '')
                    # Remove trailing text like "per Year", "per Month"
                    for suffix in ['per year', 'per month', 'per quarter', '/yr', '/mo']:
                        idx_suffix = cleaned.lower().find(suffix)
                        if idx_suffix >= 0:
                            cleaned = cleaned[:idx_suffix]
                    cleaned = cleaned.strip()
                    try:
                        price = float(cleaned)
                        item[evt_field] = -price if is_negative else price
                    except (ValueError, TypeError):
                        item[evt_field] = 0
                elif evt_field == 'quantity':
                    try:
                        item[evt_field] = int(float(str(value).replace(',', '').strip()))
                    except (ValueError, TypeError):
                        item[evt_field] = 1
                else:
                    item[evt_field] = str(value).strip()

        # Skip empty rows and summary/total rows
        if not (item['part_number'] or item['description']):
            continue
        # Skip total/subtotal rows
        combined = (item['part_number'] + ' ' + item['description']).lower()
        if any(kw in combined for kw in ['total', 'subtotal', 'recurring fees']):
            continue
        items.append(item)

    return jsonify({'items': items, 'total': len(items)})


@app.route('/api/search', methods=['GET'])
def search_quotes():
    """Search across quotes and line items."""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'results': []})

    search_term = f'%{query}%'

    # Search line items
    matching_items = LineItem.query.filter(
        db.or_(
            LineItem.part_number.ilike(search_term),
            LineItem.description.ilike(search_term),
            LineItem.item_category.ilike(search_term),
        )
    ).all()

    # Get unique quote IDs from matching items
    quote_ids = set()
    item_results = []
    for item in matching_items:
        quote_ids.add(item.quote_id)
        item_results.append({
            'quote_id': item.quote_id,
            'part_number': item.part_number,
            'description': item.description,
            'item_category': item.item_category,
            'unit_price': item.unit_price,
            'quantity': item.quantity,
            'discounted_price': item.discounted_price,
            'extended_price': item.extended_price,
        })

    # Also search quote names
    matching_quotes = Quote.query.filter(
        db.or_(
            Quote.quote_name.ilike(search_term),
            Quote.doc_number.ilike(search_term),
            Quote.supplier_name.ilike(search_term),
        )
    ).all()

    for q in matching_quotes:
        quote_ids.add(q.id)

    # Fetch all matching quotes
    quotes = Quote.query.filter(Quote.id.in_(quote_ids)).all() if quote_ids else []
    quote_results = [{
        'id': q.id,
        'doc_number': q.doc_number,
        'quote_name': q.quote_name,
        'document_type': q.document_type,
        'status': q.status,
        'quote_date': q.quote_date,
    } for q in quotes]

    return jsonify({
        'quotes': quote_results,
        'items': item_results,
        'total_quotes': len(quote_results),
        'total_items': len(item_results),
    })


if __name__ == '__main__':
    app.run(debug=True, port=5001)
