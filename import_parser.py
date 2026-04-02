"""
File parser for manufacturer quotes.
Supports CSV/TSV, Excel (.xlsx/.xls), and PDF files.
Returns normalized column headers and row data for the mapping step.
"""

import csv
import io
import os


def parse_file(filepath, filename):
    """
    Parse a manufacturer quote file and extract tabular data.

    Returns:
        dict with keys:
            - columns: list of column header strings
            - rows: list of lists (each row's cell values as strings)
            - raw_text: str or None (set only for PDF fallback when no table found)
    """
    ext = os.path.splitext(filename)[1].lower()

    if ext in ('.csv', '.tsv', '.txt'):
        return _parse_csv(filepath)
    elif ext in ('.xlsx', '.xls'):
        return _parse_excel(filepath)
    elif ext == '.pdf':
        return _parse_pdf(filepath)
    else:
        raise ValueError(f"Unsupported file format: {ext}")


def _parse_csv(filepath):
    """Parse CSV/TSV files with auto-detected delimiter."""
    with open(filepath, 'r', newline='', encoding='utf-8-sig') as f:
        sample = f.read(8192)
        f.seek(0)

        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=',\t;|')
        except csv.Error:
            dialect = csv.excel  # default to comma-separated

        reader = csv.reader(f, dialect)
        all_rows = list(reader)

    if not all_rows:
        return {'columns': [], 'rows': [], 'raw_text': None}

    # Find first non-empty row as header
    header_idx = 0
    for i, row in enumerate(all_rows):
        if any(cell.strip() for cell in row):
            header_idx = i
            break

    columns = [str(cell).strip() for cell in all_rows[header_idx]]
    rows = []
    for row in all_rows[header_idx + 1:]:
        if any(str(cell).strip() for cell in row):
            rows.append([str(cell).strip() for cell in row])

    return {'columns': columns, 'rows': rows, 'raw_text': None}


def _parse_excel(filepath):
    """Parse Excel files using openpyxl."""
    import openpyxl

    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    ws = wb.active

    all_rows = []
    for row in ws.iter_rows(values_only=True):
        all_rows.append(row)

    wb.close()

    if not all_rows:
        return {'columns': [], 'rows': [], 'raw_text': None}

    # Find first non-empty row as header
    header_idx = 0
    for i, row in enumerate(all_rows):
        if any(cell is not None and str(cell).strip() for cell in row):
            header_idx = i
            break

    columns = [str(cell).strip() if cell is not None else '' for cell in all_rows[header_idx]]
    rows = []
    for row in all_rows[header_idx + 1:]:
        if any(cell is not None and str(cell).strip() for cell in row):
            rows.append([str(cell).strip() if cell is not None else '' for cell in row])

    return {'columns': columns, 'rows': rows, 'raw_text': None}


def _parse_pdf(filepath):
    """Parse PDF files using pdfplumber. Returns all tables separately for AI selection."""
    import pdfplumber

    all_tables = []  # List of individual tables (each is a list of rows)
    all_text = []

    with pdfplumber.open(filepath) as pdf:
        for page_num, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    # Clean up each table
                    cleaned = []
                    for row in table:
                        if row and any(cell and str(cell).strip() for cell in row):
                            cleaned.append([str(cell).replace('\n', ' ').strip() if cell else '' for cell in row])
                    if cleaned:
                        all_tables.append({
                            'page': page_num + 1,
                            'rows': cleaned,
                        })

            text = page.extract_text()
            if text:
                all_text.append(text)

    if not all_tables:
        # No tables found -- return raw text for AI extraction
        raw_text = '\n\n'.join(all_text) if all_text else 'No text could be extracted from this PDF.'
        return {'columns': [], 'rows': [], 'raw_text': raw_text, 'tables': []}

    # Score each table to find the one most likely to contain line items.
    # Heuristic: the best table has price-like values ($, digits with commas)
    # and multiple data rows (not just a header or contact info).
    best_table = None
    best_score = -1

    for table_info in all_tables:
        rows = table_info['rows']
        score = 0
        price_pattern_count = 0

        for row in rows:
            for cell in row:
                if not cell:
                    continue
                # Price indicators
                if '$' in cell or 'per year' in cell.lower() or 'per month' in cell.lower():
                    price_pattern_count += 1
                # Quantity indicators
                if cell.strip().isdigit() or cell.strip() == 'N/A':
                    score += 1

        # Prefer tables with prices and multiple rows
        score += price_pattern_count * 3
        score += len(rows) * 2

        # Penalize tables that look like contact info (contain @, phone patterns)
        for row in rows:
            for cell in row:
                if cell and ('@' in cell or 'Phone:' in cell or '\n' in cell):
                    score -= 5

        if score > best_score:
            best_score = score
            best_table = table_info

    if best_table:
        rows = best_table['rows']
        # First row is header
        columns = rows[0]
        data_rows = rows[1:]

        # Clean up merged-header columns from PDF table extraction.
        # Common issue: a merged header like "Annual Recurring Fees" splits into
        # an empty-named column (with the data) and a named column (with no real data).
        if data_rows:
            num_cols = len(columns)

            # Count how many data rows have price-like or meaningful data per column
            col_data_count = [0] * num_cols
            col_price_count = [0] * num_cols
            for row in data_rows:
                for i, cell in enumerate(row):
                    if i < num_cols and cell and cell.strip():
                        col_data_count[i] += 1
                        if '$' in cell or cell.strip().replace(',', '').replace('.', '').replace('-', '').isdigit():
                            col_price_count[i] += 1

            # For empty-named columns that have price data, adopt the name from
            # the nearest named column that has LESS data (likely the split header)
            for i in range(num_cols):
                if not columns[i].strip() and col_price_count[i] > 0:
                    # Find best neighbor: named column with less data
                    best_neighbor = None
                    for neighbor in [i + 1, i - 1]:
                        if 0 <= neighbor < num_cols and columns[neighbor].strip():
                            if col_data_count[neighbor] < col_data_count[i]:
                                best_neighbor = neighbor
                                break
                    if best_neighbor is not None:
                        columns[i] = columns[best_neighbor].strip()
                        columns[best_neighbor] = ''  # Mark for removal

            # Remove columns that are now empty in both header and most data rows
            keep_cols = []
            for i in range(num_cols):
                if columns[i].strip() or col_data_count[i] > len(data_rows) * 0.3:
                    keep_cols.append(i)

            if len(keep_cols) < num_cols:
                columns = [columns[i] for i in keep_cols]
                data_rows = [
                    [row[i] if i < len(row) else '' for i in keep_cols]
                    for row in data_rows
                ]

        # Also return all tables so the AI/UI can choose differently if needed
        all_tables_serialized = []
        for t in all_tables:
            all_tables_serialized.append({
                'page': t['page'],
                'header': t['rows'][0] if t['rows'] else [],
                'rows': t['rows'][1:] if len(t['rows']) > 1 else [],
                'row_count': len(t['rows']),
            })

        return {
            'columns': columns,
            'rows': data_rows,
            'raw_text': None,
            'tables': all_tables_serialized,
            'selected_table_page': best_table['page'],
        }

    raw_text = '\n\n'.join(all_text) if all_text else 'No text could be extracted from this PDF.'
    return {'columns': [], 'rows': [], 'raw_text': raw_text, 'tables': []}
