document.addEventListener('DOMContentLoaded', function() {
    // --- State Management ---
    let currentQuoteId = null;
    let currentView = 'form';

    // --- Form and Control Initialization ---
    const form = document.getElementById('quote-form') || document.getElementById('po-form');
    const itemsContainer = document.getElementById('items-container');
    const addSectionBtn = document.getElementById('add-section-btn');
    const docTypeQuote = document.getElementById('doc_type_quote');
    const docTypePo = document.getElementById('doc_type_po');
    const quoteListContainer = document.getElementById('quote-list-container');
    const generatePdfBtn = document.getElementById('generate-pdf-btn');
    
    // View management elements
    const formView = document.getElementById('form-view');
    const manageView = document.getElementById('manage-view');
    const newQuoteBtn = document.getElementById('new-quote-btn');
    const manageDocsBtn = document.getElementById('manage-docs-btn');

    // --- Initial Load ---
    loadQuotes();
    updateViewButtons();

    // --- Event Listeners ---

    // Logic for Quote form (with line items)
    if (form.id === 'quote-form') {
        if (!itemsContainer || !addSectionBtn) {
            console.error('Required quote form elements not found.');
            return;
        }
        if (itemsContainer.children.length === 0) {
            addSection();
            ensureAllSectionsEditable();
        }
        addSectionBtn.addEventListener('click', () => {
            addSection();
            ensureAllSectionsEditable();
        });

        itemsContainer.addEventListener('click', function(e) {
            if (e.target.classList.contains('remove-item-btn')) {
                if (confirm('Are you sure you want to delete this item?')) {
                    e.target.closest('.item-wrapper').remove();
                }
            } else if (e.target.classList.contains('remove-section-btn')) {
                if (confirm('Are you sure you want to delete this entire section and all its items?')) {
                    e.target.closest('.section-block').remove();
                }
            } else if (e.target.classList.contains('copy-section-btn')) {
                const sectionBlock = e.target.closest('.section-block');
                showCopySectionModal(sectionBlock);
            } else if (e.target.classList.contains('add-item-to-section-btn')) {
                // Find the section-items container within this section
                const sectionBlock = e.target.closest('.section-block');
                const sectionItems = sectionBlock.querySelector('.section-items');
                addItem({}, sectionItems);
                ensureAllSectionsEditable();
            } else if (e.target.classList.contains('subcomponent-toggle-btn')) {
                // Toggle subcomponents visibility
                const itemRow = e.target.closest('.line-item');
                const itemId = itemRow.id;
                toggleSubcomponents(itemId);
            } else if (e.target.classList.contains('add-subcomponent-btn')) {
                // Add subcomponent to specific item
                const itemId = e.target.getAttribute('data-item-id');
                addSubcomponent(itemId);
            } else if (e.target.classList.contains('remove-subcomponent-btn')) {
                // Remove subcomponent
                if (confirm('Are you sure you want to delete this subcomponent?')) {
                    const subcomponentId = e.target.getAttribute('data-subcomponent-id');
                    const subcomponentRow = document.getElementById(subcomponentId);
                    if (subcomponentRow) {
                        subcomponentRow.remove();
                    }
                }
            }
        });
    }

    // Document type switching
    docTypeQuote.addEventListener('change', () => {
        if (docTypeQuote.checked) window.location.href = '/quote';
    });
    docTypePo.addEventListener('change', () => {
        if (docTypePo.checked) window.location.href = '/po';
    });

    // Form submission
    form.addEventListener('submit', handleFormSubmit);

    // Quote list actions
    quoteListContainer.addEventListener('click', handleQuoteListActions);

    // View switching
    newQuoteBtn.addEventListener('click', () => switchView('form'));
    manageDocsBtn.addEventListener('click', () => switchView('manage'));

    // --- Core Functions ---

    async function handleFormSubmit(e) {
        e.preventDefault();
        generatePdfBtn.textContent = 'Saving...';
        generatePdfBtn.disabled = true;

        const quoteData = await collectFormData();
        const method = currentQuoteId ? 'PUT' : 'POST';
        const url = currentQuoteId ? `/api/quote/${currentQuoteId}` : '/api/quotes';

        try {
            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(quoteData),
            });

            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            resetForm();
            loadQuotes();
            alert(`Quote ${currentQuoteId ? 'updated' : 'created'} successfully!`);
            switchView('manage');

        } catch (error) {
            console.error('Error:', error);
            alert('Failed to save quote. Check console for details.');
        } finally {
            generatePdfBtn.textContent = 'Save Document';
            generatePdfBtn.disabled = false;
        }
    }

    function handleQuoteListActions(e) {
        const target = e.target;
        const quoteItem = target.closest('.quote-list-item');
        if (!quoteItem) return;

        const quoteId = quoteItem.dataset.id;

        if (target.classList.contains('edit-btn')) {
            editQuote(quoteId);
        } else if (target.classList.contains('delete-btn')) {
            deleteQuote(quoteId);
        } else if (target.classList.contains('pdf-btn')) {
            window.open(`/quote/${quoteId}/pdf`, '_blank');
        } else if (target.classList.contains('copy-btn')) {
            copyQuote(quoteId);
        }
    }

    async function loadQuotes() {
        try {
            const response = await fetch('/api/quotes');
            if (!response.ok) throw new Error('Failed to load quotes.');
            const quotes = await response.json();
            renderQuoteList(quotes);
        } catch (error) {
            console.error('Error loading quotes:', error);
            quoteListContainer.innerHTML = '<p>Error loading documents.</p>';
        }
    }

    function renderQuoteList(quotes) {
        if (quotes.length === 0) {
            quoteListContainer.innerHTML = '<p>No documents found.</p>';
            return;
        }
        quoteListContainer.innerHTML = quotes.map(quote => `
            <div class="quote-list-item" data-id="${quote.id}">
                <div class="info">
                    <strong>${quote.doc_number}</strong><br>
                    <small>${quote.document_type === 'po' ? quote.po_name : quote.quote_name || 'Untitled'} - ${new Date(quote.created_at).toLocaleDateString()}</small>
                </div>
                <div class="actions">
                    <button class="btn-sm pdf-btn">PDF</button>
                    <button class="btn-sm edit-btn">Edit</button>
                    <button class="btn-sm copy-btn">Copy</button>
                    <button class="btn-sm delete-btn">Del</button>
                </div>
            </div>
        `).join('');
    }

    async function editQuote(id) {
        try {
            const response = await fetch(`/api/quote/${id}`);
            if (!response.ok) throw new Error('Failed to fetch quote data.');
            const quote = await response.json();
            populateForm(quote);
            currentQuoteId = id;
            generatePdfBtn.textContent = 'Update Document';
            switchView('form');
            window.scrollTo(0, 0);
        } catch (error) {
            console.error('Error fetching quote for edit:', error);
            alert('Could not load quote for editing.');
        }
    }

    async function deleteQuote(id) {
        if (!confirm('Are you sure you want to delete this document?')) return;

        try {
            const response = await fetch(`/api/quote/${id}`, { method: 'DELETE' });
            if (!response.ok) throw new Error('Failed to delete quote.');
            loadQuotes();
            if (currentQuoteId === id) resetForm();
        } catch (error) {
            console.error('Error deleting quote:', error);
            alert('Could not delete quote.');
        }
    }

    async function copyQuote(id) {
        try {
            const response = await fetch(`/api/quote/${id}/copy`, { method: 'POST' });
            if (!response.ok) throw new Error('Failed to copy quote.');
            
            const result = await response.json();
            alert(`Quote copied successfully! New document number: ${result.doc_number}`);
            loadQuotes(); // Refresh the quote list
        } catch (error) {
            console.error('Error copying quote:', error);
            alert('Could not copy quote. Please try again.');
        }
    }

    function populateForm(quote) {
        // Reset form first
        resetForm();

        // Set document type and redirect if needed
        if (quote.document_type === 'po') {
            if (form.id === 'quote-form') {
                // We're on the quote page but need PO form - redirect
                window.location.href = '/po';
                return;
            }
            docTypePo.checked = true;
        } else {
            if (form.id === 'po-form') {
                // We're on the PO page but need quote form - redirect
                window.location.href = '/quote';
                return;
            }
            docTypeQuote.checked = true;
        }

        // Populate fields based on document type
        if (quote.document_type === 'quote') {
            document.getElementById('quote_name').value = quote.quote_name || '';
            document.getElementById('quote_date').value = quote.quote_date || '';
            
            // Clear and populate line items for quotes
            if (itemsContainer) {
                itemsContainer.innerHTML = '';
                quote.items.forEach(item => {
                    if (item.type === 'section') {
                        addSection(item.title);
                    } else if (item.type === 'item') {
                        addItem(item);
                        // Add subcomponents if they exist
                        if (item.subcomponents && item.subcomponents.length > 0) {
                            const itemElements = itemsContainer.querySelectorAll('.line-item');
                            const lastItemElement = itemElements[itemElements.length - 1];
                            const itemId = lastItemElement.id;
                            
                            item.subcomponents.forEach(subcomponent => {
                                addSubcomponent(itemId, subcomponent);
                            });
                        }
                    }
                });
                // Ensure all sections remain editable after population
                ensureAllSectionsEditable();
                
                // Add drag and drop listeners to all loaded sections
                document.querySelectorAll('.section-block').forEach(section => {
                    addDragAndDropListeners(section);
                });
                
                // Add drag and drop listeners to all loaded items
                document.querySelectorAll('.item-wrapper').forEach(item => {
                    addItemDragAndDropListeners(item);
                });
            }
        } else if (quote.document_type === 'po') {
            // Populate PO-specific fields
            const setValue = (id, value) => {
                const el = document.getElementById(id);
                if (el) el.value = value || '';
            };
            
            setValue('po_name', quote.po_name);
            setValue('po_date', quote.po_date);
            setValue('payment_terms', quote.payment_terms);
            setValue('shipping_name', quote.shipping_name);
            setValue('shipping_address', quote.shipping_address);
            setValue('shipping_city_state_zip', quote.shipping_city_state_zip);
            setValue('billing_name', quote.billing_name);
            setValue('billing_address', quote.billing_address);
            setValue('billing_city_state_zip', quote.billing_city_state_zip);
            setValue('supplier_name', quote.supplier_name);
            setValue('supplier_quote', quote.supplier_quote);
            setValue('supplier_contact', quote.supplier_contact);
            setValue('end_user_name', quote.end_user_name);
            setValue('end_user_po', quote.end_user_po);
            setValue('end_user_contact', quote.end_user_contact);
            setValue('po_amount', quote.po_amount);
        }

        // Common fields
        document.getElementById('notes').value = quote.notes || '';
    }

    function resetForm() {
        form.reset();
        if (itemsContainer) {
            itemsContainer.innerHTML = '';
            addSection(); // Add one empty section for quotes only
        }
        currentQuoteId = null;
        generatePdfBtn.textContent = 'Save Document';
    }

    function addSection(title = '') {
        const sectionId = `section-${Date.now()}`;
        const sectionWrapper = document.createElement('div');
        sectionWrapper.className = 'section-block';
        sectionWrapper.id = sectionId;
        sectionWrapper.draggable = true;
        sectionWrapper.innerHTML = `
            <div class="section-header">
                <div class="section-drag-handle" title="Drag to reorder">⋮⋮</div>
                <input type="text" placeholder="Section Header" class="section-title" data-type="section" value="${title}">
                <div class="section-actions">
                    <button type="button" class="copy-btn copy-section-btn" title="Copy Section">📋</button>
                    <button type="button" class="remove-btn remove-section-btn">Remove</button>
                </div>
            </div>
            <div class="section-items">
                <div class="item-row item-header">
                    <span>Part #</span>
                    <span>Description</span>
                    <span>Type</span>
                    <span>Unit Price</span>
                    <span>Qty</span>
                    <span>Discounted Unit</span>
                    <span></span>
                </div>
            </div>
            <div class="section-controls">
                <button type="button" class="add-item-to-section-btn">Add Item to This Section</button>
            </div>
        `;
        itemsContainer.appendChild(sectionWrapper);
        
        // Add drag and drop event listeners
        addDragAndDropListeners(sectionWrapper);
        
        // Ensure the section input is editable
        const sectionInput = sectionWrapper.querySelector('.section-title');
        if (sectionInput) {
            sectionInput.removeAttribute('readonly');
            sectionInput.removeAttribute('disabled');
            sectionInput.style.pointerEvents = 'auto';
            sectionInput.tabIndex = 0;
        }
    }

    // Function to ensure all section inputs remain editable
    function ensureAllSectionsEditable() {
        document.querySelectorAll('.section-title').forEach(input => {
            input.removeAttribute('readonly');
            input.removeAttribute('disabled');
            input.style.pointerEvents = 'auto';
            input.tabIndex = 0;
        });
    }

    function addItem(item = {}, targetSectionElement = null) {
        // If no specific section provided, use the last section (for backward compatibility)
        const targetSection = targetSectionElement || itemsContainer.querySelector('.section-block:last-child .section-items');
        if (!targetSection) {
            alert('Please add a section first.');
            return;
        }
        const itemId = `item-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        targetSection.insertAdjacentHTML('beforeend', `
            <div class="item-wrapper" id="wrapper-${itemId}" draggable="true">
                <div class="item-row line-item" id="${itemId}" data-type="item">
                    <div class="item-drag-handle" title="Drag to move item">⋮⋮</div>
                    <input type="text" name="part_number[]" placeholder="Part #" value="${item.part_number || ''}">
                    <input type="text" name="description[]" placeholder="Description" value="${item.description || ''}">
                    <input type="text" name="item_type[]" placeholder="Type" value="${item.item_type || ''}">
                    <input type="number" class="unit-price" placeholder="Unit Price" step="0.01" value="${item.unit_price || ''}">
                    <input type="number" class="quantity" placeholder="Qty" value="${item.quantity || ''}">
                    <input type="number" class="discounted-price" placeholder="Discounted" step="0.01" value="${item.discounted_price || ''}">
                    <div class="item-actions">
                        <button type="button" class="subcomponent-toggle-btn" title="Manage Subcomponents">📋</button>
                        <button type="button" class="remove-btn remove-item-btn">Remove</button>
                    </div>
                </div>
                <div class="subcomponents-container" id="subcomponents-${itemId}" style="display: none;">
                    <div class="subcomponents-header">
                        <h4>Subcomponents</h4>
                        <button type="button" class="add-subcomponent-btn" data-item-id="${itemId}">Add Subcomponent</button>
                    </div>
                    <div class="subcomponents-list" id="subcomponents-list-${itemId}">
                        <!-- Subcomponents will be added here -->
                    </div>
                </div>
            </div>
        `);
        
        // Add drag and drop event listeners to the new item
        const newItemWrapper = document.getElementById(`wrapper-${itemId}`);
        addItemDragAndDropListeners(newItemWrapper);
    }

    function addSubcomponent(itemId, subcomponent = {}) {
        const subcomponentsList = document.getElementById(`subcomponents-list-${itemId}`);
        if (!subcomponentsList) {
            console.error('Could not find subcomponents list for item:', itemId);
            return;
        }

        const subcomponentId = `subcomponent-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const subcomponentHTML = `
            <div class="subcomponent-row" id="${subcomponentId}">
                <input type="text" class="subcomponent-description" placeholder="Subcomponent description" value="${subcomponent.description || ''}" data-item-id="${itemId}">
                <input type="number" class="subcomponent-quantity" placeholder="Qty" min="1" value="${subcomponent.quantity || 1}" data-item-id="${itemId}">
                <button type="button" class="remove-subcomponent-btn" data-subcomponent-id="${subcomponentId}">Remove</button>
            </div>
        `;
        subcomponentsList.insertAdjacentHTML('beforeend', subcomponentHTML);
    }

    function toggleSubcomponents(itemId) {
        const container = document.getElementById(`subcomponents-${itemId}`);
        if (container) {
            container.style.display = container.style.display === 'none' ? 'block' : 'none';
        }
    }

    async function collectFormData() {
        const data = {};
        const docTypeInput = document.querySelector('input[name="document_type"]:checked');
        data.document_type = docTypeInput ? docTypeInput.value : 'quote';

        const getValue = id => document.getElementById(id)?.value || null;

        if (data.document_type === 'quote') {
            data.quote_name = getValue('quote_name');
            data.quote_date = getValue('quote_date');
        } else { // PO
            data.po_name = getValue('po_name');
            data.po_date = getValue('po_date');
            data.payment_terms = getValue('payment_terms');
            data.shipping_name = getValue('shipping_name');
            data.shipping_address = getValue('shipping_address');
            data.shipping_city_state_zip = getValue('shipping_city_state_zip');
            data.billing_name = getValue('billing_name');
            data.billing_address = getValue('billing_address');
            data.billing_city_state_zip = getValue('billing_city_state_zip');
            data.supplier_name = getValue('supplier_name');
            data.supplier_quote = getValue('supplier_quote');
            data.supplier_contact = getValue('supplier_contact');
            data.end_user_name = getValue('end_user_name');
            data.end_user_po = getValue('end_user_po');
            data.end_user_contact = getValue('end_user_contact');
            data.po_amount = getValue('po_amount');
        }
        data.notes = getValue('notes');

        // Collect line items
        data.items = [];
        document.querySelectorAll('.section-block').forEach(sectionBlock => {
            const sectionTitleInput = sectionBlock.querySelector('.section-title');
            if (sectionTitleInput && sectionTitleInput.value) {
                data.items.push({ type: 'section', title: sectionTitleInput.value });
            }

            sectionBlock.querySelectorAll('.line-item').forEach(itemRow => {
                const itemData = {
                    type: 'item',
                    part_number: itemRow.querySelector('[name="part_number[]"]').value,
                    description: itemRow.querySelector('[name="description[]"]').value,
                    item_type: itemRow.querySelector('[name="item_type[]"]').value,
                    unit_price: itemRow.querySelector('.unit-price').value,
                    quantity: itemRow.querySelector('.quantity').value,
                    discounted_price: itemRow.querySelector('.discounted-price').value,
                    subcomponents: []
                };

                // Collect subcomponents for this item
                const itemId = itemRow.id;
                const subcomponentsList = document.getElementById(`subcomponents-list-${itemId}`);
                if (subcomponentsList) {
                    subcomponentsList.querySelectorAll('.subcomponent-row').forEach(subRow => {
                        const description = subRow.querySelector('.subcomponent-description').value;
                        const quantity = subRow.querySelector('.subcomponent-quantity').value;
                        if (description.trim()) {
                            itemData.subcomponents.push({
                                description: description,
                                quantity: parseInt(quantity) || 1
                            });
                        }
                    });
                }

                data.items.push(itemData);
            });
        });

        return data;
    }

    // --- View Management Functions ---
    
    function switchView(view) {
        currentView = view;
        if (view === 'form') {
            formView.style.display = 'block';
            manageView.style.display = 'none';
        } else if (view === 'manage') {
            formView.style.display = 'none';
            manageView.style.display = 'block';
        }
        updateViewButtons();
    }
    
    function updateViewButtons() {
        newQuoteBtn.classList.toggle('active', currentView === 'form');
        manageDocsBtn.classList.toggle('active', currentView === 'manage');
    }

    // --- Copy and Reorder Functions ---
    
    function copySection(sectionBlock) {
        const sectionTitle = sectionBlock.querySelector('.section-title').value;
        const sectionItems = sectionBlock.querySelectorAll('.line-item');
        
        // Create new section with copied title
        const copiedTitle = sectionTitle ? `${sectionTitle} (Copy)` : '';
        addSection(copiedTitle);
        
        // Get the newly created section
        const newSection = itemsContainer.querySelector('.section-block:last-child');
        const newSectionItems = newSection.querySelector('.section-items');
        
        // Copy all items from the original section
        sectionItems.forEach(itemRow => {
            const itemData = {
                part_number: itemRow.querySelector('[name="part_number[]"]').value,
                description: itemRow.querySelector('[name="description[]"]').value,
                item_type: itemRow.querySelector('[name="item_type[]"]').value,
                unit_price: itemRow.querySelector('.unit-price').value,
                quantity: itemRow.querySelector('.quantity').value,
                discounted_price: itemRow.querySelector('.discounted-price').value
            };
            
            addItem(itemData, newSectionItems);
            
            // Copy subcomponents if they exist
            const itemId = itemRow.id;
            const subcomponentsList = document.getElementById(`subcomponents-list-${itemId}`);
            if (subcomponentsList) {
                const subcomponents = subcomponentsList.querySelectorAll('.subcomponent-row');
                if (subcomponents.length > 0) {
                    const newItemElements = newSectionItems.querySelectorAll('.line-item');
                    const newItemElement = newItemElements[newItemElements.length - 1];
                    const newItemId = newItemElement.id;
                    
                    subcomponents.forEach(subRow => {
                        const subcomponentData = {
                            description: subRow.querySelector('.subcomponent-description').value,
                            quantity: subRow.querySelector('.subcomponent-quantity').value
                        };
                        addSubcomponent(newItemId, subcomponentData);
                    });
                }
            }
        });
        
        ensureAllSectionsEditable();
    }

    // Section copying to other quotes functionality
    let currentSectionToCopy = null;
    let selectedTargetQuoteId = null;

    function showCopySectionModal(sectionBlock) {
        currentSectionToCopy = sectionBlock;
        const modal = document.getElementById('copy-section-modal');
        
        // Load available quotes
        loadTargetQuotes();
        
        if (modal) {
            modal.style.display = 'flex';
        }
    }

    async function loadTargetQuotes() {
        try {
            const response = await fetch('/api/quotes');
            const quotes = await response.json();
            
            const targetQuotesList = document.getElementById('target-quotes-list');
            targetQuotesList.innerHTML = '';
            
            // Filter out current quote if we're editing one
            const availableQuotes = quotes.filter(quote => quote.id !== currentQuoteId);
            
            if (availableQuotes.length === 0) {
                targetQuotesList.innerHTML = '<p>No other quotes available. Create another quote first.</p>';
                return;
            }
            
            availableQuotes.forEach(quote => {
                const quoteOption = document.createElement('div');
                quoteOption.className = 'quote-option';
                quoteOption.innerHTML = `
                    <input type="radio" name="target-quote" value="${quote.id}" id="quote-${quote.id}">
                    <div class="quote-info">
                        <div class="quote-name">${quote.quote_name || quote.po_name || quote.doc_number}</div>
                        <div class="quote-details">${quote.doc_number} • ${quote.quote_date || quote.po_date || 'No date'}</div>
                    </div>
                `;
                
                quoteOption.addEventListener('click', () => {
                    const radio = quoteOption.querySelector('input[type="radio"]');
                    radio.checked = true;
                    selectedTargetQuoteId = quote.id;
                    
                    // Update visual selection
                    document.querySelectorAll('.quote-option').forEach(opt => opt.classList.remove('selected'));
                    quoteOption.classList.add('selected');
                    
                    // Enable copy button
                    document.getElementById('confirm-copy-btn').disabled = false;
                });
                
                targetQuotesList.appendChild(quoteOption);
            });
        } catch (error) {
            console.error('Error loading quotes:', error);
            document.getElementById('target-quotes-list').innerHTML = '<p>Error loading quotes. Please try again.</p>';
        }
    }

    async function copySectionToQuote() {
        if (!currentSectionToCopy || !selectedTargetQuoteId) {
            alert('Please select a target quote.');
            return;
        }

        const sectionTitle = currentSectionToCopy.querySelector('.section-title').value;
        const sectionItems = currentSectionToCopy.querySelectorAll('.line-item');
        
        // Collect section data
        const sectionData = {
            section_title: sectionTitle,
            section_items: []
        };

        sectionItems.forEach(itemRow => {
            const itemData = {
                part_number: itemRow.querySelector('[name="part_number[]"]').value,
                description: itemRow.querySelector('[name="description[]"]').value,
                item_type: itemRow.querySelector('[name="item_type[]"]').value,
                unit_price: itemRow.querySelector('.unit-price').value,
                quantity: itemRow.querySelector('.quantity').value,
                discounted_price: itemRow.querySelector('.discounted-price').value,
                subcomponents: []
            };
            
            // Collect subcomponents
            const itemId = itemRow.id;
            const subcomponentsList = document.getElementById(`subcomponents-list-${itemId}`);
            if (subcomponentsList) {
                const subcomponents = subcomponentsList.querySelectorAll('.subcomponent-row');
                subcomponents.forEach(subRow => {
                    itemData.subcomponents.push({
                        description: subRow.querySelector('.subcomponent-description').value,
                        quantity: subRow.querySelector('.subcomponent-quantity').value
                    });
                });
            }
            
            sectionData.section_items.push(itemData);
        });

        try {
            const response = await fetch(`/api/quote/${currentQuoteId}/copy-section/${selectedTargetQuoteId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(sectionData)
            });

            const result = await response.json();
            
            if (response.ok) {
                alert(result.message);
                closeCopySectionModal();
            } else {
                alert('Error copying section: ' + result.message);
            }
        } catch (error) {
            console.error('Error copying section:', error);
            alert('Error copying section. Please try again.');
        }
    }

    function closeCopySectionModal() {
        const modal = document.getElementById('copy-section-modal');
        modal.style.display = 'none';
        currentSectionToCopy = null;
        selectedTargetQuoteId = null;
        document.getElementById('confirm-copy-btn').disabled = true;
    }

    // Modal event listeners - initialize immediately since we're already in DOMContentLoaded
    const modal = document.getElementById('copy-section-modal');
    if (modal) {
        const closeBtn = modal.querySelector('.close-modal');
        const cancelBtn = document.getElementById('cancel-copy-btn');
        const confirmBtn = document.getElementById('confirm-copy-btn');

        if (closeBtn) closeBtn.addEventListener('click', closeCopySectionModal);
        if (cancelBtn) cancelBtn.addEventListener('click', closeCopySectionModal);
        if (confirmBtn) confirmBtn.addEventListener('click', copySectionToQuote);

        // Close modal when clicking outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeCopySectionModal();
            }
        });
    }

    function addDragAndDropListeners(sectionElement) {
        sectionElement.addEventListener('dragstart', handleDragStart);
        sectionElement.addEventListener('dragover', handleDragOver);
        sectionElement.addEventListener('drop', handleDrop);
        sectionElement.addEventListener('dragend', handleDragEnd);
    }
    
    let draggedElement = null;
    
    function handleDragStart(e) {
        draggedElement = this;
        this.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/html', this.outerHTML);
    }
    
    function handleDragOver(e) {
        if (e.preventDefault) {
            e.preventDefault();
        }
        e.dataTransfer.dropEffect = 'move';
        return false;
    }
    
    function handleDrop(e) {
        if (e.stopPropagation) {
            e.stopPropagation();
        }
        
        if (draggedElement !== this) {
            const rect = this.getBoundingClientRect();
            const midpoint = rect.top + rect.height / 2;
            
            if (e.clientY < midpoint) {
                // Insert before this element
                this.parentNode.insertBefore(draggedElement, this);
            } else {
                // Insert after this element
                this.parentNode.insertBefore(draggedElement, this.nextSibling);
            }
        }
        
        return false;
    }
    
    function handleDragEnd(e) {
        this.classList.remove('dragging');
        draggedElement = null;
        
        // Re-add event listeners to all sections after reordering
        document.querySelectorAll('.section-block').forEach(section => {
            // Remove existing listeners to avoid duplicates
            section.removeEventListener('dragstart', handleDragStart);
            section.removeEventListener('dragover', handleDragOver);
            section.removeEventListener('drop', handleDrop);
            section.removeEventListener('dragend', handleDragEnd);
            
            // Re-add listeners
            addDragAndDropListeners(section);
        });
    }

    // Item drag and drop functionality
    function addItemDragAndDropListeners(itemElement) {
        itemElement.addEventListener('dragstart', handleItemDragStart);
        itemElement.addEventListener('dragover', handleItemDragOver);
        itemElement.addEventListener('drop', handleItemDrop);
        itemElement.addEventListener('dragend', handleItemDragEnd);
        
        // Also add drop listeners to section containers to allow dropping between sections
        document.querySelectorAll('.section-items').forEach(sectionItems => {
            sectionItems.addEventListener('dragover', handleSectionDragOver);
            sectionItems.addEventListener('drop', handleSectionDrop);
        });
    }
    
    let draggedItem = null;
    
    function handleItemDragStart(e) {
        draggedItem = this;
        this.classList.add('dragging-item');
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/html', this.outerHTML);
        e.stopPropagation(); // Prevent section drag from triggering
    }
    
    function handleItemDragOver(e) {
        if (e.preventDefault) {
            e.preventDefault();
        }
        e.dataTransfer.dropEffect = 'move';
        e.stopPropagation(); // Prevent section drag over from triggering
        return false;
    }
    
    function handleItemDrop(e) {
        if (e.stopPropagation) {
            e.stopPropagation();
        }
        
        if (draggedItem && draggedItem !== this) {
            const rect = this.getBoundingClientRect();
            const midpoint = rect.top + rect.height / 2;
            
            if (e.clientY < midpoint) {
                // Insert before this element
                this.parentNode.insertBefore(draggedItem, this);
            } else {
                // Insert after this element
                this.parentNode.insertBefore(draggedItem, this.nextSibling);
            }
        }
        
        return false;
    }
    
    function handleSectionDragOver(e) {
        if (e.preventDefault) {
            e.preventDefault();
        }
        if (draggedItem) { // Only handle if we're dragging an item
            e.dataTransfer.dropEffect = 'move';
            this.classList.add('drag-over');
        }
        return false;
    }
    
    function handleSectionDrop(e) {
        if (e.stopPropagation) {
            e.stopPropagation();
        }
        
        this.classList.remove('drag-over');
        
        if (draggedItem) {
            // Find the last item in this section (excluding the header)
            const items = this.querySelectorAll('.item-wrapper');
            if (items.length > 0) {
                // Insert after the last item
                this.appendChild(draggedItem);
            } else {
                // If no items, insert after the header
                const header = this.querySelector('.item-header');
                if (header) {
                    this.insertBefore(draggedItem, header.nextSibling);
                } else {
                    this.appendChild(draggedItem);
                }
            }
        }
        
        return false;
    }
    
    function handleItemDragEnd(e) {
        this.classList.remove('dragging-item');
        document.querySelectorAll('.section-items').forEach(section => {
            section.classList.remove('drag-over');
        });
        draggedItem = null;
        
        // Re-add event listeners to all items after reordering
        document.querySelectorAll('.item-wrapper').forEach(item => {
            // Remove existing listeners to avoid duplicates
            item.removeEventListener('dragstart', handleItemDragStart);
            item.removeEventListener('dragover', handleItemDragOver);
            item.removeEventListener('drop', handleItemDrop);
            item.removeEventListener('dragend', handleItemDragEnd);
            
            // Re-add listeners
            addItemDragAndDropListeners(item);
        });
    }

});
