document.addEventListener('DOMContentLoaded', function () {
    // --- State ---
    let currentStep = 1;
    let fileId = null;
    let sourceColumns = [];
    let previewRows = [];
    let allRows = [];
    let columnMapping = {};
    let mappedItems = [];
    let pricedItems = [];
    let savedMappingLoaded = false;
    let pdfExtraction = null; // AI-extracted PDF data

    // --- Elements ---
    const manufacturerInput = document.getElementById('manufacturer-name');
    const fileInput = document.getElementById('import-file');
    const uploadBtn = document.getElementById('upload-btn');
    const uploadStatus = document.getElementById('upload-status');
    const savedMappingBanner = document.getElementById('saved-mapping-banner');
    const applyMappingBtn = document.getElementById('apply-mapping-btn');
    const applyPricingBtn = document.getElementById('apply-pricing-btn');
    const createQuoteBtn = document.getElementById('create-quote-btn');
    const priceSearchBtn = document.getElementById('price-search-btn');

    // --- Load saved manufacturers for autocomplete ---
    loadManufacturerList();

    // --- Event Listeners ---
    uploadBtn.addEventListener('click', handleUpload);
    applyMappingBtn.addEventListener('click', handleApplyMapping);
    applyPricingBtn.addEventListener('click', handleApplyPricing);
    createQuoteBtn.addEventListener('click', handleCreateQuote);
    priceSearchBtn.addEventListener('click', handlePriceSearch);

    // Check for saved mapping when manufacturer name changes
    let mappingCheckTimeout;
    manufacturerInput.addEventListener('input', function () {
        clearTimeout(mappingCheckTimeout);
        mappingCheckTimeout = setTimeout(checkSavedMapping, 500);
    });

    // Pricing mode toggle
    document.querySelectorAll('input[name="pricing-mode"]').forEach(radio => {
        radio.addEventListener('change', handlePricingModeChange);
    });

    // --- Step Navigation ---
    window.goToStep = function (step) {
        document.getElementById(`step-${currentStep}`).style.display = 'none';
        document.getElementById(`step-${step}`).style.display = 'block';

        // Update progress indicators
        document.querySelectorAll('.wizard-step').forEach(el => {
            const s = parseInt(el.dataset.step);
            el.classList.remove('active', 'completed');
            if (s === step) el.classList.add('active');
            else if (s < step) el.classList.add('completed');
        });

        currentStep = step;
    };

    // --- Step 1: Upload ---

    async function handleUpload() {
        const file = fileInput.files[0];
        if (!file) {
            showStatus(uploadStatus, 'Please select a file.', 'error');
            return;
        }

        uploadBtn.disabled = true;
        showStatus(uploadStatus, 'Uploading and parsing...', 'loading');

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/import/upload', {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();
            if (!response.ok) throw new Error(result.error || 'Upload failed');

            fileId = result.file_id;
            sourceColumns = result.columns;
            previewRows = result.preview_rows;

            if (result.raw_text && sourceColumns.length === 0) {
                // PDF fallback - try AI extraction
                showStatus(uploadStatus, 'No tables found in PDF. Trying AI extraction...', 'loading');
                await handlePdfFallback(result.raw_text);
            } else {
                showStatus(uploadStatus, `Parsed ${result.total_rows} rows successfully.`, 'success');
                await setupColumnMapping();
            }
        } catch (error) {
            showStatus(uploadStatus, error.message, 'error');
        } finally {
            uploadBtn.disabled = false;
        }
    }

    async function handlePdfFallback(rawText) {
        try {
            const response = await fetch('/api/import/ai-map', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    raw_text: rawText,
                    manufacturer_name: manufacturerInput.value.trim(),
                }),
            });

            const result = await response.json();
            if (!response.ok) throw new Error(result.error || 'AI extraction failed');

            if (result.pdf_extraction) {
                pdfExtraction = result.pdf_extraction;
                sourceColumns = pdfExtraction.columns;
                previewRows = pdfExtraction.rows.slice(0, 5);
                allRows = pdfExtraction.rows;

                showStatus(uploadStatus, `AI extracted ${pdfExtraction.rows.length} items from PDF.`, 'success');

                // For AI-extracted PDF data, columns are already EVT fields
                // Skip to mapping confirmation
                setupPdfMapping();
            } else {
                showStatus(uploadStatus, 'Could not extract data from PDF. Try a different format.', 'error');
            }
        } catch (error) {
            showStatus(uploadStatus, `PDF extraction failed: ${error.message}`, 'error');
        }
    }

    function setupPdfMapping() {
        // PDF AI extraction already returns EVT-named columns
        // Show preview and auto-map
        renderPreviewTable(sourceColumns, previewRows);

        // Auto-create identity mapping
        columnMapping = {};
        sourceColumns.forEach(col => {
            columnMapping[col] = col;
        });

        renderMappingDropdowns(sourceColumns, columnMapping, {});
        goToStep(2);
    }

    async function setupColumnMapping() {
        renderPreviewTable(sourceColumns, previewRows);

        // Check for saved mapping first
        const manufacturer = manufacturerInput.value.trim();
        let aiMapping = null;

        if (savedMappingLoaded && columnMapping && Object.keys(columnMapping).length > 0) {
            // Use saved mapping
            renderMappingDropdowns(sourceColumns, columnMapping, {});
            const aiStatus = document.getElementById('ai-status');
            aiStatus.textContent = 'Using saved mapping for ' + manufacturer + '.';
            aiStatus.className = 'info-banner success';
            aiStatus.style.display = 'block';
        } else {
            // Try AI mapping
            const aiStatus = document.getElementById('ai-status');
            aiStatus.textContent = 'Analyzing columns with AI...';
            aiStatus.className = 'info-banner';
            aiStatus.style.display = 'block';

            try {
                const response = await fetch('/api/import/ai-map', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        columns: sourceColumns,
                        sample_rows: previewRows,
                        manufacturer_name: manufacturer,
                    }),
                });

                aiMapping = await response.json();

                if (aiMapping.ai_available) {
                    aiStatus.textContent = 'AI suggestions applied. Review and adjust as needed.';
                    aiStatus.className = 'info-banner success';
                } else {
                    aiStatus.textContent = 'AI not available (no API key). Using keyword matching.';
                    aiStatus.className = 'info-banner warning';
                }

                columnMapping = aiMapping.mapping || {};
                renderMappingDropdowns(sourceColumns, columnMapping, aiMapping.confidence || {});
            } catch (error) {
                aiStatus.textContent = 'AI mapping failed. Please map columns manually.';
                aiStatus.className = 'info-banner warning';
                renderMappingDropdowns(sourceColumns, {}, {});
            }
        }

        goToStep(2);
    }

    function renderPreviewTable(columns, rows) {
        const header = document.getElementById('preview-header');
        const body = document.getElementById('preview-body');

        header.innerHTML = '<tr>' + columns.map(col =>
            `<th>${escapeHtml(col)}</th>`
        ).join('') + '</tr>';

        body.innerHTML = rows.map(row =>
            '<tr>' + row.map(cell =>
                `<td>${escapeHtml(cell || '')}</td>`
            ).join('') + '</tr>'
        ).join('');
    }

    function renderMappingDropdowns(columns, mapping, confidence) {
        const container = document.getElementById('mapping-dropdowns');
        const evtFields = [
            { value: 'skip', label: '-- Skip --' },
            { value: 'part_number', label: 'Part Number' },
            { value: 'description', label: 'Description' },
            { value: 'item_category', label: 'Category' },
            { value: 'unit_price', label: 'Unit Price (Cost)' },
            { value: 'quantity', label: 'Quantity' },
        ];

        container.innerHTML = columns.map((col, idx) => {
            // For empty column names, use index-based key
            const displayName = col.trim() || `(Column ${idx + 1})`;
            const mapKey = col.trim() ? col : `col_${idx}`;

            const mappedTo = mapping[col] || mapping[mapKey] || 'skip';
            const conf = confidence[col] || confidence[mapKey];
            const confClass = conf ? `confidence-${conf}` : '';
            const confLabel = conf ? `<span class="mapping-confidence ${confClass}">${conf}</span>` : '';

            const options = evtFields.map(f =>
                `<option value="${f.value}" ${f.value === mappedTo ? 'selected' : ''}>${f.label}</option>`
            ).join('');

            return `
                <div class="mapping-row" data-column="${escapeHtml(mapKey)}">
                    <span class="mapping-source">${escapeHtml(displayName)} ${confLabel}</span>
                    <span class="mapping-arrow">&rarr;</span>
                    <div class="mapping-target">
                        <select data-source="${escapeHtml(mapKey)}">${options}</select>
                    </div>
                </div>
            `;
        }).join('');
    }

    // --- Step 2: Apply Mapping ---

    async function handleApplyMapping() {
        // Collect mapping from dropdowns
        columnMapping = {};
        document.querySelectorAll('#mapping-dropdowns select').forEach(select => {
            const source = select.dataset.source;
            const target = select.value;
            if (target !== 'skip') {
                columnMapping[source] = target;
            }
        });

        if (Object.keys(columnMapping).length === 0) {
            alert('Please map at least one column.');
            return;
        }

        // Save mapping if checkbox is checked
        const saveCheckbox = document.getElementById('save-mapping-checkbox');
        const manufacturer = manufacturerInput.value.trim();
        if (saveCheckbox.checked && manufacturer) {
            try {
                await fetch('/api/import/mappings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        manufacturer_name: manufacturer,
                        column_map: columnMapping,
                    }),
                });
            } catch (e) {
                console.warn('Failed to save mapping:', e);
            }
        }

        // Process file with mapping
        applyMappingBtn.disabled = true;
        applyMappingBtn.textContent = 'Processing...';

        try {
            const payload = { column_map: columnMapping };

            if (pdfExtraction) {
                // Use AI-extracted PDF data
                payload.pdf_rows = pdfExtraction.rows;
                payload.pdf_columns = pdfExtraction.columns;
                payload.file_id = fileId;
            } else {
                payload.file_id = fileId;
            }

            const response = await fetch('/api/import/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            const result = await response.json();
            if (!response.ok) throw new Error(result.error || 'Processing failed');

            mappedItems = result.items;
            setupPricingStep();
            goToStep(3);
        } catch (error) {
            alert('Failed to process file: ' + error.message);
        } finally {
            applyMappingBtn.disabled = false;
            applyMappingBtn.textContent = 'Continue';
        }
    }

    // --- Step 3: Pricing ---

    function setupPricingStep() {
        // Discover unique categories
        const categories = [...new Set(
            mappedItems
                .map(item => item.item_category)
                .filter(c => c && c.trim())
        )];

        const container = document.getElementById('category-margins-container');
        if (categories.length > 0) {
            container.innerHTML = categories.map(cat => `
                <div class="category-margin-row">
                    <label>${escapeHtml(cat)}:</label>
                    <input type="number" class="category-margin" data-category="${escapeHtml(cat)}" value="15" min="0" max="100" step="0.5">
                    <span>%</span>
                </div>
            `).join('');
        } else {
            container.innerHTML = '<p class="helper-text">No categories detected. Items will use global margin.</p>';
        }
    }

    function handlePricingModeChange() {
        const mode = document.querySelector('input[name="pricing-mode"]:checked').value;
        document.getElementById('global-margin-input').style.display = mode === 'global' ? 'block' : 'none';
        document.getElementById('category-margin-inputs').style.display = mode === 'category' ? 'block' : 'none';
    }

    function handleApplyPricing() {
        const mode = document.querySelector('input[name="pricing-mode"]:checked').value;

        pricedItems = mappedItems.map(item => {
            const priced = { ...item };
            const cost = parseFloat(priced.unit_price) || 0;
            let margin = 0;

            if (mode === 'global') {
                margin = parseFloat(document.getElementById('global-margin').value) || 0;
            } else if (mode === 'category') {
                const catInput = document.querySelector(`.category-margin[data-category="${item.item_category}"]`);
                margin = catInput ? parseFloat(catInput.value) || 0 : 0;
            }
            // per-item mode: margin stays 0, sell = cost (user edits in review)

            priced.discounted_price = Math.round(cost * (1 + margin / 100) * 100) / 100;
            priced.quantity = parseInt(priced.quantity) || 1;
            priced.extended_price = Math.round(priced.discounted_price * priced.quantity * 100) / 100;

            return priced;
        });

        renderReviewTable();

        // Pre-fill quote metadata
        const manufacturer = manufacturerInput.value.trim();
        const today = new Date().toISOString().split('T')[0];
        document.getElementById('new-quote-name').value = manufacturer ? `${manufacturer} - ${today}` : `Import - ${today}`;
        document.getElementById('new-section-name').value = manufacturer || 'Imported Items';

        goToStep(4);
    }

    // --- Price History Search ---

    async function handlePriceSearch() {
        const query = document.getElementById('price-search').value.trim();
        if (!query) return;

        const resultsDiv = document.getElementById('price-search-results');
        resultsDiv.innerHTML = '<p class="helper-text">Searching...</p>';

        try {
            const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
            const result = await response.json();

            if (result.items.length === 0) {
                resultsDiv.innerHTML = '<p class="helper-text">No matching items found.</p>';
                return;
            }

            resultsDiv.innerHTML = result.items.slice(0, 10).map(item => `
                <div class="price-result">
                    <span><strong>${escapeHtml(item.part_number || '')}</strong> ${escapeHtml(item.description || '')}</span>
                    <span>Cost: $${(item.unit_price || 0).toFixed(2)} / Sell: $${(item.discounted_price || 0).toFixed(2)}</span>
                </div>
            `).join('');
        } catch (error) {
            resultsDiv.innerHTML = '<p class="helper-text" style="color: #dc3545;">Search failed.</p>';
        }
    }

    // --- Step 4: Review & Create ---

    function renderReviewTable() {
        const body = document.getElementById('review-body');

        body.innerHTML = pricedItems.map((item, idx) => `
            <tr data-index="${idx}">
                <td><input type="text" class="review-part" value="${escapeHtml(item.part_number || '')}"></td>
                <td><input type="text" class="review-desc" value="${escapeHtml(item.description || '')}"></td>
                <td><input type="number" class="review-qty" value="${item.quantity || 1}" min="1"></td>
                <td><input type="number" class="review-sell" value="${(item.discounted_price || 0).toFixed(2)}" step="0.01" min="0"></td>
                <td class="review-ext">$${(item.extended_price || 0).toFixed(2)}</td>
                <td><button type="button" class="remove-row-btn" data-index="${idx}" title="Remove">&times;</button></td>
                <input type="hidden" class="review-cost" value="${(parseFloat(item.unit_price) || 0).toFixed(2)}">
                <input type="hidden" class="review-category" value="${escapeHtml(item.item_category || '')}">
            </tr>
        `).join('');

        updateTotal();

        // Add event listeners for recalculation
        body.addEventListener('input', function (e) {
            if (e.target.classList.contains('review-qty') || e.target.classList.contains('review-sell')) {
                const row = e.target.closest('tr');
                recalculateRow(row);
            }
        });

        body.addEventListener('click', function (e) {
            if (e.target.classList.contains('remove-row-btn')) {
                const idx = parseInt(e.target.dataset.index);
                e.target.closest('tr').remove();
                pricedItems.splice(idx, 1);
                updateTotal();
            }
        });
    }

    function recalculateRow(row) {
        const qty = parseFloat(row.querySelector('.review-qty').value) || 0;
        const sell = parseFloat(row.querySelector('.review-sell').value) || 0;
        const ext = Math.round(qty * sell * 100) / 100;
        row.querySelector('.review-ext').textContent = '$' + ext.toFixed(2);
        updateTotal();
    }

    function updateTotal() {
        let total = 0;
        document.querySelectorAll('#review-body tr').forEach(row => {
            const extText = row.querySelector('.review-ext').textContent.replace('$', '');
            total += parseFloat(extText) || 0;
        });
        document.getElementById('review-total').innerHTML = `<strong>$${total.toFixed(2)}</strong>`;
    }

    async function handleCreateQuote() {
        const quoteName = document.getElementById('new-quote-name').value.trim();
        const sectionName = document.getElementById('new-section-name').value.trim();
        const notes = document.getElementById('new-quote-notes').value.trim();

        if (!quoteName) {
            alert('Please enter a quote name.');
            return;
        }

        // Collect items from review table
        const items = [];

        // Add section header
        if (sectionName) {
            items.push({ type: 'section', title: sectionName });
        }

        document.querySelectorAll('#review-body tr').forEach(row => {
            const partNumber = row.querySelector('.review-part').value;
            const description = row.querySelector('.review-desc').value;
            const category = row.querySelector('.review-category').value;
            const qty = parseInt(row.querySelector('.review-qty').value) || 1;
            const sellPrice = parseFloat(row.querySelector('.review-sell').value) || 0;

            // Get original cost from hidden input
            const cost = parseFloat(row.querySelector('.review-cost').value) || 0;

            items.push({
                type: 'item',
                part_number: partNumber,
                description: description,
                item_type: category,
                unit_price: cost,
                quantity: qty,
                discounted_price: sellPrice,
            });
        });

        const today = new Date().toISOString().split('T')[0];

        const customerName = document.getElementById('new-customer-name').value.trim();
        const supplierNumber = document.getElementById('new-supplier-number').value.trim();
        const cwNumber = document.getElementById('new-cw-number').value.trim();
        const maNumber = document.getElementById('new-ma-number').value.trim();
        const status = document.getElementById('new-status').value;

        const payload = {
            document_type: 'quote',
            quote_name: quoteName,
            quote_date: today,
            status: status,
            notes: notes || null,
            customer_name: customerName || null,
            supplier_number: supplierNumber || null,
            cw_number: cwNumber || null,
            ma_number: maNumber || null,
            items: items,
        };

        createQuoteBtn.disabled = true;
        createQuoteBtn.textContent = 'Creating...';
        const createStatus = document.getElementById('create-status');

        try {
            const response = await fetch('/api/quotes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            const result = await response.json();
            if (!response.ok) throw new Error(result.error || 'Failed to create quote');

            showStatus(createStatus, `Quote created! Doc #: ${result.doc_number}. Redirecting...`, 'success');

            // Redirect to manage documents view
            setTimeout(() => {
                window.location.href = '/quote?view=manage';
            }, 1000);
        } catch (error) {
            showStatus(createStatus, error.message, 'error');
        } finally {
            createQuoteBtn.disabled = false;
            createQuoteBtn.textContent = 'Create EVT Quote';
        }
    }

    // --- Helpers ---

    async function loadManufacturerList() {
        try {
            const response = await fetch('/api/import/mappings');
            const mappings = await response.json();
            const datalist = document.getElementById('manufacturer-list');
            datalist.innerHTML = mappings.map(m =>
                `<option value="${escapeHtml(m.manufacturer_name)}">`
            ).join('');
        } catch (e) {
            // Silently fail - autocomplete is optional
        }
    }

    async function checkSavedMapping() {
        const name = manufacturerInput.value.trim();
        if (!name) {
            savedMappingBanner.style.display = 'none';
            savedMappingLoaded = false;
            return;
        }

        try {
            const response = await fetch(`/api/import/mappings/${encodeURIComponent(name)}`);
            if (response.ok) {
                const mapping = await response.json();
                columnMapping = mapping.column_map;
                savedMappingLoaded = true;
                savedMappingBanner.style.display = 'block';
            } else {
                savedMappingLoaded = false;
                savedMappingBanner.style.display = 'none';
            }
        } catch (e) {
            savedMappingLoaded = false;
            savedMappingBanner.style.display = 'none';
        }
    }

    function showStatus(element, message, type) {
        element.textContent = message;
        element.className = 'status-message ' + type;
    }

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
});
