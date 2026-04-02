"""
PDF generator using fpdf2 (pure Python, no native dependencies).
Generates customer-facing EVT quotes with 5 columns:
Part #, Description, Qty, Unit Price, Extended Price
"""

from fpdf import FPDF
import os


# Column widths: Part#, Description, Qty, Unit Price, Extended Price
COL_W = [35, 70, 15, 35, 35]
TABLE_W = sum(COL_W)


class QuotePDF(FPDF):
    def __init__(self, data):
        super().__init__()
        self.data = data
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(10, 10, 10)

    def header(self):
        data = self.data

        # Left side: Logo + supplier IDs
        logo_path = data.get('logo_path')
        if logo_path and os.path.exists(logo_path):
            self.image(logo_path, 10, 8, 28)

        # Supplier IDs under the logo
        supplier_num = data.get('supplier_number')
        cw_num = data.get('cw_number')
        ma_num = data.get('ma_number')
        id_y = 22 if logo_path else 10
        if supplier_num or cw_num or ma_num:
            self.set_font('Helvetica', '', 7)
            self.set_text_color(80, 80, 80)
            if supplier_num:
                self.set_xy(10, id_y)
                self.cell(40, 3.5, f'Supplier #: {supplier_num}')
                id_y += 3.5
            if cw_num:
                self.set_xy(10, id_y)
                self.cell(40, 3.5, f'CW #: {cw_num}')
                id_y += 3.5
            if ma_num:
                self.set_xy(10, id_y)
                self.cell(40, 3.5, f'MA #: {ma_num}')

        # Right side: Doc type + company info
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(51, 51, 51)
        self.set_xy(100, 8)
        self.cell(0, 6, data.get('doc_type_display', 'QUOTE').upper(), align='R', new_x='LMARGIN', new_y='NEXT')
        self.set_font('Helvetica', '', 8)
        self.set_text_color(80, 80, 80)
        for line in ['Enterprise Vision Technologies',
                     '201 Wilshire Blvd, Suite A-9',
                     'Santa Monica, CA 90401',
                     'Phone: (214)517-0666',
                     'Email: bconley@evtcorp.com']:
            self.set_x(100)
            self.cell(0, 3.5, line, align='R', new_x='LMARGIN', new_y='NEXT')

        # Divider
        self.set_draw_color(100, 100, 100)
        self.line(10, 33, 200, 33)
        self.set_y(35)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 7)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', align='C')


def generate_quote_pdf(data):
    """Generate a PDF from quote data and return bytes."""
    pdf = QuotePDF(data)
    pdf.alias_nb_pages()
    pdf.add_page()

    # Draft watermark
    if data.get('status') == 'draft':
        pdf.set_font('Helvetica', 'B', 60)
        pdf.set_text_color(255, 200, 200)
        x_center = pdf.w / 2
        y_center = pdf.h / 2
        with pdf.rotation(45, x_center, y_center):
            pdf.set_xy(x_center - 50, y_center - 10)
            pdf.cell(100, 20, 'DRAFT', align='C')
        pdf.set_text_color(0, 0, 0)

    # Quote title
    pdf.set_font('Helvetica', 'B', 13)
    pdf.set_text_color(80, 80, 80)
    customer_name = data.get('customer_name', '')
    title = f'Customer Quote For {customer_name}' if customer_name else 'Customer Quote'
    pdf.cell(0, 8, title, align='C', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(2)

    # Quote info - two columns
    pdf.set_text_color(51, 51, 51)
    info_items = [
        ('Quote #:', data.get('doc_number', '')),
        ('Quote Name:', data.get('document_name', '')),
        ('Quote Date:', data.get('document_date', '')),
        ('Expiration Date:', data.get('expiration_date', 'N/A')),
    ]
    for label, value in info_items:
        pdf.set_font('Helvetica', 'B', 8)
        pdf.cell(30, 5, label)
        pdf.set_font('Helvetica', '', 8)
        pdf.cell(0, 5, str(value), new_x='LMARGIN', new_y='NEXT')
    pdf.ln(4)

    # Line items by section
    items = data.get('items', [])
    grand_total = 0.0
    section_total = 0.0
    in_section = False
    row_index = 0  # for alternating row colors

    for item in items:
        if item.get('type') == 'section':
            if in_section:
                _draw_section_subtotal(pdf, section_total)
                pdf.ln(2)

            section_total = 0.0
            in_section = True
            row_index = 0  # reset per section

            # Section header
            pdf.set_font('Helvetica', 'B', 10)
            pdf.set_text_color(51, 51, 51)
            pdf.cell(0, 7, item.get('title', ''), new_x='LMARGIN', new_y='NEXT')
            pdf.set_draw_color(200, 200, 200)
            pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + TABLE_W, pdf.get_y())
            pdf.ln(1)

            # Table header row
            _draw_table_header(pdf)

        elif item.get('type') == 'item':
            ext_price = float(item.get('extended_price', 0) or 0)
            sell_price = float(item.get('discounted_price', 0) or 0)
            qty = item.get('quantity', 0)
            part_num = str(item.get('part_number', '') or '')
            desc = str(item.get('description', '') or '')

            # Calculate row height based on content wrapping
            pdf.set_font('Helvetica', '', 6.5)
            part_lines = pdf.multi_cell(COL_W[0], 5, part_num, split_only=True)
            desc_lines = pdf.multi_cell(COL_W[1], 5, desc, split_only=True)
            row_lines = max(len(part_lines), len(desc_lines), 1)
            row_h = max(row_lines * 5, 6)

            # Check if we need a new page
            if pdf.get_y() + row_h > pdf.h - 25:
                pdf.add_page()
                _draw_table_header(pdf)

            pdf.set_text_color(51, 51, 51)
            y_start = pdf.get_y()
            x_start = pdf.get_x()

            # Alternating row fill
            is_shaded = (row_index % 2 == 1)
            if is_shaded:
                pdf.set_fill_color(245, 245, 245)
            else:
                pdf.set_fill_color(255, 255, 255)

            # First pass: measure row height
            pdf.set_font('Helvetica', '', 6.5)
            part_lines_m = pdf.multi_cell(COL_W[0], 5, part_num, split_only=True)
            desc_lines_m = pdf.multi_cell(COL_W[1], 5, desc, split_only=True)
            actual_row_h = max(len(part_lines_m), len(desc_lines_m), 1) * 5

            # Draw background fill for the full row
            pdf.rect(x_start, y_start, TABLE_W, actual_row_h, 'F')

            # Part number (wrapping)
            pdf.set_font('Helvetica', '', 6.5)
            pdf.set_xy(x_start, y_start)
            pdf.multi_cell(COL_W[0], 5, part_num, border='LR', align='L', fill=False)
            y_after_part = pdf.get_y()

            # Description (wrapping)
            pdf.set_xy(x_start + COL_W[0], y_start)
            pdf.multi_cell(COL_W[1], 5, desc, border='LR', align='L', fill=False)
            y_after_desc = pdf.get_y()

            y_bottom = max(y_after_part, y_after_desc)

            # Qty, Unit Price, Extended Price
            pdf.set_xy(x_start + COL_W[0] + COL_W[1], y_start)
            pdf.cell(COL_W[2], y_bottom - y_start, str(qty), border='LR', align='C')

            pdf.set_xy(x_start + COL_W[0] + COL_W[1] + COL_W[2], y_start)
            pdf.cell(COL_W[3], y_bottom - y_start, f'${sell_price:,.2f}', border='LR', align='R')

            pdf.set_xy(x_start + COL_W[0] + COL_W[1] + COL_W[2] + COL_W[3], y_start)
            pdf.cell(COL_W[4], y_bottom - y_start, f'${ext_price:,.2f}', border='LR', align='R')

            # Draw bottom border across full row
            pdf.line(x_start, y_bottom, x_start + TABLE_W, y_bottom)
            pdf.set_y(y_bottom)

            row_index += 1

            section_total += ext_price
            grand_total += ext_price

            # Subcomponents
            for sub in item.get('subcomponents', []):
                pdf.set_font('Helvetica', 'I', 6)
                pdf.set_text_color(108, 117, 125)
                pdf.cell(COL_W[0], 4, '', border=0)
                sub_desc = f"  -> {sub.get('description', '')} (x{sub.get('quantity', 1)})"
                pdf.cell(COL_W[1], 4, sub_desc, border=0)
                pdf.cell(COL_W[2] + COL_W[3] + COL_W[4], 4, '', border=0)
                pdf.ln()

    # Close last section
    if in_section:
        _draw_section_subtotal(pdf, section_total)

    # Grand total
    pdf.ln(4)
    pdf.set_draw_color(80, 80, 80)
    total_label_w = COL_W[0] + COL_W[1] + COL_W[2] + COL_W[3]
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(total_label_w, 8, 'Grand Total:', align='R')
    pdf.cell(COL_W[4], 8, f'${grand_total:,.2f}', align='R')
    pdf.ln()
    pdf.line(pdf.get_x() + total_label_w, pdf.get_y(), pdf.get_x() + TABLE_W, pdf.get_y())

    # Draft notice
    if data.get('status') == 'draft':
        pdf.ln(8)
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_text_color(180, 0, 0)
        pdf.cell(0, 5, 'DRAFT STATUS NOTICE:', new_x='LMARGIN', new_y='NEXT')
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(80, 80, 80)
        pdf.multi_cell(0, 4, 'This quote is in DRAFT status and is not final. No purchase orders should be issued against this draft quote. This document is for review purposes only and subject to change.')

    # Notes
    notes = data.get('notes')
    if notes:
        pdf.ln(4)
        pdf.set_draw_color(200, 200, 200)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(2)
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(80, 80, 80)
        pdf.multi_cell(0, 4, notes)

    return bytes(pdf.output())


def _draw_table_header(pdf):
    """Draw the column header row for the items table."""
    pdf.set_font('Helvetica', 'B', 7)
    pdf.set_fill_color(242, 242, 242)
    pdf.set_text_color(0, 0, 0)
    headers = ['Part #', 'Description', 'Qty', 'Unit Price', 'Extended Price']
    for i, h in enumerate(headers):
        align = 'R' if i >= 3 else ('C' if i == 2 else 'L')
        pdf.cell(COL_W[i], 6, h, border=1, fill=True, align=align)
    pdf.ln()


def _draw_section_subtotal(pdf, section_total):
    """Draw a section subtotal row."""
    pdf.set_font('Helvetica', 'B', 7)
    pdf.set_text_color(51, 51, 51)
    label_w = COL_W[0] + COL_W[1] + COL_W[2] + COL_W[3]
    pdf.cell(label_w, 6, 'Section Subtotal:', align='R')
    pdf.cell(COL_W[4], 6, f'${section_total:,.2f}', align='R')
    pdf.ln()
