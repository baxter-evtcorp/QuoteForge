"""
AI-powered column mapper using Claude API.
Analyzes manufacturer file headers and sample data to suggest
column mappings to EVT quote fields.
"""

import json
import os


# EVT target fields that manufacturer columns can map to
EVT_FIELDS = {
    'part_number': 'Part Number / SKU',
    'description': 'Item Description',
    'item_category': 'Category (hardware, software, service, etc.)',
    'unit_price': 'Unit Price / Cost',
    'quantity': 'Quantity',
}


def suggest_mapping(columns, sample_rows, manufacturer_name=None):
    """
    Use Claude API to suggest column mappings from source to EVT fields.

    Args:
        columns: list of source column header strings
        sample_rows: list of lists (first 3-5 rows of data)
        manufacturer_name: optional manufacturer name for context

    Returns:
        dict with keys:
            - mapping: { "source_col": "evt_field", ... }
            - confidence: { "source_col": "high"|"medium"|"low", ... }
            - unmapped: list of source columns that don't map to any EVT field
            - ai_available: bool indicating if AI was used
    """
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return _fallback_mapping(columns)

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
    except Exception:
        return _fallback_mapping(columns)

    # Build the prompt
    sample_data = _format_sample_data(columns, sample_rows)
    manufacturer_context = f" from {manufacturer_name}" if manufacturer_name else ""

    prompt = f"""You are analyzing a manufacturer quote{manufacturer_context} to map its columns to a standardized quote format.

The target fields are:
- part_number: The product SKU, part number, or product ID
- description: The item/product description
- item_category: The category (hardware, software, service, license, support, etc.)
- unit_price: The per-unit cost/price
- quantity: The number of units

Here is the source data:

{sample_data}

For each source column, determine which target field it maps to, or mark it as "skip" if it doesn't map to any target field.

Respond with ONLY a JSON object in this exact format:
{{
    "mapping": {{"Source Column Name": "target_field_or_skip", ...}},
    "confidence": {{"Source Column Name": "high|medium|low", ...}},
    "sections_detected": ["section name 1", "section name 2"]
}}

Rules:
- Each target field should be mapped at most once
- Use "skip" for columns that don't match any target field (like extended price, discount %, notes, etc.)
- "high" confidence = obvious match (e.g., "SKU" -> part_number)
- "medium" confidence = likely match but ambiguous (e.g., "Price" could be unit or extended)
- "low" confidence = uncertain guess
- sections_detected: list any section headers you see in the data (e.g., "SOFTWARE", "HARDWARE", "SERVICES")"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text.strip()
        # Extract JSON from response (handle markdown code blocks)
        if '```' in response_text:
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
            response_text = response_text.strip()

        result = json.loads(response_text)

        mapping = result.get('mapping', {})
        confidence = result.get('confidence', {})
        sections = result.get('sections_detected', [])

        # Filter out "skip" entries from the mapping
        clean_mapping = {k: v for k, v in mapping.items() if v != 'skip'}
        unmapped = [col for col in columns if col not in clean_mapping]

        return {
            'mapping': clean_mapping,
            'confidence': confidence,
            'unmapped': unmapped,
            'sections_detected': sections,
            'ai_available': True,
        }

    except Exception as e:
        print(f"AI mapping failed: {e}")
        return _fallback_mapping(columns)


def analyze_pdf_content(raw_text, manufacturer_name=None):
    """
    Use Claude API to extract structured data from raw PDF text
    when table extraction failed.

    Args:
        raw_text: raw text extracted from PDF
        manufacturer_name: optional manufacturer name

    Returns:
        dict with columns, rows, and detected sections
    """
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return None

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
    except Exception:
        return None

    manufacturer_context = f" from {manufacturer_name}" if manufacturer_name else ""

    prompt = f"""You are extracting structured quote data from a manufacturer quote{manufacturer_context}.

The raw text from the PDF is:

{raw_text[:8000]}

Extract the line items into a structured table. For each item, identify:
- part_number: SKU or part number
- description: item description
- item_category: category (hardware, software, service, etc.)
- unit_price: per-unit price (number only, no currency symbols)
- quantity: number of units

Also identify any section headers (e.g., "SOFTWARE", "HARDWARE", "SERVICES").

Respond with ONLY a JSON object:
{{
    "columns": ["part_number", "description", "item_category", "unit_price", "quantity"],
    "rows": [
        ["SKU-001", "Product description", "hardware", "1500.00", "10"],
        ...
    ],
    "sections": [
        {{"title": "HARDWARE", "start_row": 0}},
        ...
    ]
}}

If you cannot extract structured data, respond with:
{{"columns": [], "rows": [], "sections": [], "error": "reason"}}"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text.strip()
        if '```' in response_text:
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
            response_text = response_text.strip()

        return json.loads(response_text)

    except Exception as e:
        print(f"AI PDF analysis failed: {e}")
        return None


def _fallback_mapping(columns):
    """
    Rule-based fallback when AI is not available.
    Uses keyword matching on column names.
    """
    mapping = {}
    confidence = {}

    keywords = {
        'part_number': ['part', 'sku', 'product id', 'product number', 'item number',
                        'item #', 'part #', 'pn', 'model', 'catalog'],
        'description': ['description', 'desc', 'name', 'product name', 'item name',
                        'product description', 'item description', 'title'],
        'item_category': ['category', 'type', 'class', 'group', 'product type',
                          'item type', 'product category'],
        'unit_price': ['unit price', 'price', 'cost', 'unit cost', 'msrp', 'list price',
                       'list', 'each', 'unit', 'rate'],
        'quantity': ['quantity', 'qty', 'count', 'units', 'amount', 'num'],
    }

    used_targets = set()

    for col in columns:
        col_lower = col.lower().strip()
        matched = False

        for target, kws in keywords.items():
            if target in used_targets:
                continue
            for kw in kws:
                if kw in col_lower or col_lower in kw:
                    mapping[col] = target
                    confidence[col] = 'medium'
                    used_targets.add(target)
                    matched = True
                    break
            if matched:
                break

    unmapped = [col for col in columns if col not in mapping]

    return {
        'mapping': mapping,
        'confidence': confidence,
        'unmapped': unmapped,
        'sections_detected': [],
        'ai_available': False,
    }


def _format_sample_data(columns, sample_rows):
    """Format columns and sample rows as a readable table for the AI prompt."""
    lines = []
    lines.append("Columns: " + " | ".join(columns))
    lines.append("-" * 80)
    for i, row in enumerate(sample_rows[:5]):
        # Pad row to match column count
        padded = row + [''] * (len(columns) - len(row))
        lines.append(f"Row {i+1}: " + " | ".join(str(cell) for cell in padded[:len(columns)]))
    return '\n'.join(lines)
