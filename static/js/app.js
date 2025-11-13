/**
 * IMB Generator - Frontend JavaScript
 * Handles customer management, file upload, column mapping, processing, and results
 */

// Global state
let uploadedFileData = null;
let previewData = null;
let customers = [];
let currentJobId = null;

/**
 * Safely show a Bootstrap modal by clearing conflicting state
 */
function safeShowModal(elementId, options = {}) {
    const el = document.getElementById(elementId);
    if (!el) {
        console.error(`Modal element not found: ${elementId}`);
        return null;
    }

    // Clear any conflicting Bootstrap state
    el.removeAttribute('aria-hidden');
    el.style.display = '';

    // Destroy any existing instance
    const existingInstance = bootstrap.Modal.getInstance(el);
    if (existingInstance) {
        existingInstance.dispose();
    }

    // Create fresh instance
    const modal = new bootstrap.Modal(el, options);
    return modal;
}

/**
 * Safely hide a Bootstrap modal
 */
function safeHideModal(elementId) {
    const el = document.getElementById(elementId);
    if (!el) return;

    const instance = bootstrap.Modal.getInstance(el);
    if (instance) {
        instance.hide();
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Load customers
    loadCustomers();

    // Set up event listeners
    setupEventListeners();
});

/**
 * Set up all event listeners
 */
function setupEventListeners() {
    // File upload
    const fileInput = document.getElementById('file-input');
    const dropZone = document.getElementById('drop-zone');

    fileInput.addEventListener('change', handleFileSelect);

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('border-primary', 'bg-light');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('border-primary', 'bg-light');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('border-primary', 'bg-light');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            handleFileSelect();
        }
    });

    // Process button
    document.getElementById('process-btn').addEventListener('click', processFile);

    // Customer form - with error checking
    const customerForm = document.getElementById('customer-form');
    if (customerForm) {
        console.log('Customer form found, attaching submit listener');
        customerForm.addEventListener('submit', saveCustomer);
    } else {
        console.error('Customer form not found!');
    }

    // Customer selection - auto-load settings
    document.getElementById('customer-select').addEventListener('change', onCustomerSelected);

    // Mail mode toggle - update description and service type
    document.querySelectorAll('input[name="mail-mode"]').forEach(radio => {
        radio.addEventListener('change', onMailModeChange);
    });

    // Mailer ID change - update sequence suggestion
    document.getElementById('mailer-id').addEventListener('input', onMailerIdChange);

    // Download buttons
    document.getElementById('download-btn').addEventListener('click', () => downloadFile('output'));
    document.getElementById('download-errors-btn').addEventListener('click', () => downloadFile('errors'));
}

// ========================================
// Customer Management
// ========================================

/**
 * Load all customers from API
 */
async function loadCustomers() {
    try {
        const response = await fetch('/api/customers');
        const data = await response.json();

        if (response.ok) {
            customers = data.customers || [];
            populateCustomerDropdown();
            renderCustomersList();
        } else {
            showAlert('Failed to load customers', 'danger');
        }
    } catch (error) {
        console.error('Error loading customers:', error);
        showAlert('Error loading customers', 'danger');
    }
}

/**
 * Populate customer dropdown
 */
function populateCustomerDropdown() {
    const select = document.getElementById('customer-select');
    select.innerHTML = '<option value="">-- Select a customer --</option>';

    customers.forEach(customer => {
        const option = document.createElement('option');
        option.value = customer.id;
        option.textContent = customer.name + (customer.company_name ? ` (${customer.company_name})` : '');
        select.appendChild(option);
    });

    // Auto-select if only one customer exists (enables "old way" quick processing)
    if (customers.length === 1) {
        select.value = customers[0].id;
        // Trigger change event to load customer settings
        select.dispatchEvent(new Event('change'));
    }
}

/**
 * Render customers list in modal
 */
function renderCustomersList() {
    const container = document.getElementById('customers-list-container');

    if (customers.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-3">
                <i class="bi bi-inbox fs-2"></i>
                <p class="mt-2">No customers yet. Add your first customer above.</p>
            </div>
        `;
        return;
    }

    const table = `
        <table class="table table-sm table-hover">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Company</th>
                    <th>Email</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                ${customers.map(customer => `
                    <tr>
                        <td>${customer.name}</td>
                        <td>${customer.company_name || '-'}</td>
                        <td>${customer.email || '-'}</td>
                        <td>
                            <button class="btn btn-sm btn-outline-primary" onclick="editCustomer(${customer.id})">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="deleteCustomer(${customer.id})">
                                <i class="bi bi-trash"></i>
                            </button>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;

    container.innerHTML = table;
}

/**
 * Open customer modal
 */
function openCustomerModal() {
    resetCustomerForm();
    const customerModal = safeShowModal('customerModal');
    if (customerModal) customerModal.show();
}

/**
 * Save customer (create or update)
 */
async function saveCustomer(e) {
    console.log('saveCustomer function called');
    e.preventDefault();

    const customerId = document.getElementById('edit-customer-id').value;
    const customerData = {
        name: document.getElementById('customer-name').value,
        company_name: document.getElementById('customer-company').value,
        email: document.getElementById('customer-email').value,
        default_mailer_id: document.getElementById('customer-mailer-id').value,
        default_service_type: document.getElementById('customer-service-type').value,
        default_barcode_id: document.getElementById('customer-barcode-id').value,
        default_sequence_start: parseInt(document.getElementById('customer-sequence-start').value) || 1,
        api_provider: document.getElementById('customer-api-provider').value
    };

    console.log('Customer data:', customerData);

    // Validate name
    if (!customerData.name || customerData.name.trim() === '') {
        showAlert('Customer name is required', 'warning');
        return;
    }

    try {
        const url = customerId ? `/api/customers/${customerId}` : '/api/customers';
        const method = customerId ? 'PUT' : 'POST';

        console.log(`Sending ${method} request to ${url}`);

        const response = await fetch(url, {
            method: method,
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(customerData)
        });

        console.log('Response status:', response.status);

        const data = await response.json();
        console.log('Response data:', data);

        if (response.ok) {
            showAlert(customerId ? 'Customer updated successfully' : 'Customer created successfully', 'success');
            await loadCustomers();
            resetCustomerForm();
        } else {
            showAlert(data.error || 'Failed to save customer', 'danger');
        }
    } catch (error) {
        console.error('Error saving customer:', error);
        showAlert('Error saving customer: ' + error.message, 'danger');
    }
}

/**
 * Edit customer
 */
function editCustomer(customerId) {
    const customer = customers.find(c => c.id === customerId);
    if (!customer) return;

    document.getElementById('customer-form-title').textContent = 'Edit Customer';
    document.getElementById('edit-customer-id').value = customer.id;
    document.getElementById('customer-name').value = customer.name;
    document.getElementById('customer-company').value = customer.company_name || '';
    document.getElementById('customer-email').value = customer.email || '';
    document.getElementById('customer-mailer-id').value = customer.default_mailer_id || '';
    document.getElementById('customer-service-type').value = customer.default_service_type || '040';
    document.getElementById('customer-barcode-id').value = customer.default_barcode_id || '00';
    document.getElementById('customer-sequence-start').value = customer.default_sequence_start || 1;
    document.getElementById('customer-api-provider').value = customer.api_provider || 'usps';
}

/**
 * Handle customer selection - auto-load saved settings
 */
async function onCustomerSelected(event) {
    const customerId = parseInt(event.target.value);

    // Enable/disable history button based on customer selection
    const historyBtn = document.getElementById('view-history-btn');
    if (historyBtn) {
        historyBtn.disabled = !customerId;
    }

    if (!customerId) {
        // No customer selected, clear settings badge if any
        const settingsBadge = document.getElementById('settings-loaded-badge');
        if (settingsBadge) settingsBadge.remove();
        return;
    }

    try {
        // Fetch customer details
        const response = await fetch(`/api/customers/${customerId}`);
        if (!response.ok) {
            console.error('Failed to fetch customer details');
            return;
        }

        const data = await response.json();
        const customer = data.customer;

        // Auto-populate IMB configuration if customer has saved defaults
        if (customer.default_mailer_id) {
            document.getElementById('mailer-id').value = customer.default_mailer_id;
        }
        if (customer.default_service_type) {
            document.getElementById('service-type').value = customer.default_service_type;
        }
        if (customer.default_barcode_id) {
            document.getElementById('barcode-id').value = customer.default_barcode_id;
        }
        if (customer.default_sequence_start) {
            document.getElementById('starting-sequence').value = customer.default_sequence_start;
        }

        // Fetch and update sequence suggestion if customer has used this mailer ID before
        if (customer.default_mailer_id && customer.last_mailer_id_used) {
            const sequenceInfo = {
                last_sequence_number: customer.last_sequence_number,
                last_mailer_id_used: customer.last_mailer_id_used,
                next_suggested_sequence: customer.last_sequence_number + 1,
                can_auto_continue: customer.last_mailer_id_used === customer.default_mailer_id
            };
            updateSequenceSuggestion(sequenceInfo);
        }

        // Show badge indicating settings were loaded
        if (customer.default_mailer_id || customer.default_service_type) {
            showSettingsLoadedBadge(customer.name || customer.company_name);
        }

    } catch (error) {
        console.error('Error loading customer settings:', error);
    }
}

/**
 * Show badge indicating settings were loaded from customer
 */
function showSettingsLoadedBadge(customerName) {
    // Remove existing badge if any
    const existing = document.getElementById('settings-loaded-badge');
    if (existing) existing.remove();

    // Create new badge
    const badge = document.createElement('div');
    badge.id = 'settings-loaded-badge';
    badge.className = 'alert alert-info alert-dismissible fade show mt-2';
    badge.innerHTML = `
        <i class="bi bi-check-circle"></i>
        <strong>Settings Loaded:</strong> Using saved defaults for ${customerName}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    // Insert after customer select
    const customerSelect = document.getElementById('customer-select');
    customerSelect.parentElement.insertAdjacentElement('afterend', badge);
}

/**
 * Handle mail mode toggle change
 * Updates description text and auto-selects appropriate STID
 */
function onMailModeChange(event) {
    const mode = event.target.value;
    const descriptionEl = document.getElementById('mail-mode-description');
    const serviceTypeEl = document.getElementById('service-type');

    if (mode === 'basic') {
        descriptionEl.textContent = 'Basic (STID 240) - USPS Marketing Mail (Non-Full-Service)';
        serviceTypeEl.value = '240';
    } else if (mode === 'full_service') {
        descriptionEl.textContent = 'Full-Service (STID 271) - USPS Marketing Mail with enhanced tracking';
        serviceTypeEl.value = '271';
    }

    console.log(`Mail mode changed to: ${mode}, Service Type: ${serviceTypeEl.value}`);
}

/**
 * Handle mailer ID input change
 * Fetches sequence suggestion for customer/mailer ID combo
 */
async function onMailerIdChange(event) {
    const mailerId = event.target.value.trim();
    const customerId = parseInt(document.getElementById('customer-select').value);

    if (!customerId || !mailerId) {
        // Reset to default if no customer or mailer ID
        document.getElementById('sequence-helper-text').textContent = 'Auto-increments for each record';
        return;
    }

    try {
        // Fetch sequence info for this customer/mailer ID combo
        const response = await fetch(`/api/customers/${customerId}/sequence-info?mailer_id=${encodeURIComponent(mailerId)}`);

        if (response.ok) {
            const data = await response.json();
            updateSequenceSuggestion(data);
        }
    } catch (error) {
        console.error('Error fetching sequence info:', error);
    }
}

/**
 * Update sequence suggestion UI based on tracking data
 */
function updateSequenceSuggestion(sequenceInfo) {
    const sequenceInput = document.getElementById('starting-sequence');
    const helperText = document.getElementById('sequence-helper-text');

    if (sequenceInfo.can_auto_continue) {
        // Same mailer ID - suggest continuing sequence
        sequenceInput.value = sequenceInfo.next_suggested_sequence;
        helperText.innerHTML = `
            <i class="bi bi-check-circle text-success"></i>
            Auto-continuing from last job (ended at ${sequenceInfo.last_sequence_number})
        `;
    } else if (sequenceInfo.last_mailer_id_used && sequenceInfo.last_mailer_id_used !== sequenceInput.value) {
        // Different mailer ID - warn and suggest starting from 1
        sequenceInput.value = 1;
        helperText.innerHTML = `
            <i class="bi bi-exclamation-triangle text-warning"></i>
            Different Mailer ID detected. Starting fresh from 1
        `;
    } else {
        // No previous jobs
        sequenceInput.value = 1;
        helperText.textContent = 'Auto-increments for each record';
    }
}

// ========================================
// Job History Functions
// ========================================

/**
 * Open job history modal
 */
async function openJobHistoryModal() {
    const customerId = parseInt(document.getElementById('customer-select').value);
    if (!customerId) {
        showAlert('Please select a customer first', 'warning');
        return;
    }

    const modal = safeShowModal('jobHistoryModal');
    if (modal) {
        modal.show();
        await loadJobHistory(customerId);
    }
}

/**
 * Load and display job history
 */
async function loadJobHistory(customerId) {
    const container = document.getElementById('job-history-container');

    try {
        const response = await fetch(`/api/jobs?customer_id=${customerId}`);
        if (!response.ok) {
            throw new Error('Failed to fetch job history');
        }

        const data = await response.json();
        const jobs = data.jobs || [];

        if (jobs.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted py-5">
                    <i class="bi bi-inbox fs-1"></i>
                    <p class="mt-3">No jobs found for this customer</p>
                </div>
            `;
            return;
        }

        // Build table
        const table = `
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead class="table-light">
                        <tr>
                            <th>Date</th>
                            <th>Filename</th>
                            <th>Records</th>
                            <th>Success Rate</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${jobs.map(job => {
                            const date = new Date(job.created_at);
                            const successRate = job.total_records > 0
                                ? ((job.successful_records / job.total_records) * 100).toFixed(1)
                                : '0.0';
                            const statusBadge = getStatusBadge(job.status);

                            return `
                                <tr>
                                    <td>${date.toLocaleDateString()} ${date.toLocaleTimeString()}</td>
                                    <td>${job.filename}</td>
                                    <td>${job.successful_records}/${job.total_records}</td>
                                    <td>
                                        <span class="badge ${successRate >= 95 ? 'bg-success' : successRate >= 80 ? 'bg-warning' : 'bg-danger'}">
                                            ${successRate}%
                                        </span>
                                    </td>
                                    <td>${statusBadge}</td>
                                    <td>
                                        ${job.status === 'complete' ? `
                                            <button class="btn btn-sm btn-primary" onclick="downloadJobFile(${job.id}, 'output')">
                                                <i class="bi bi-download"></i> Results
                                            </button>
                                            ${job.failed_records > 0 ? `
                                                <button class="btn btn-sm btn-warning" onclick="downloadJobFile(${job.id}, 'errors')">
                                                    <i class="bi bi-exclamation-triangle"></i> Errors
                                                </button>
                                            ` : ''}
                                        ` : `
                                            <span class="text-muted">N/A</span>
                                        `}
                                    </td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            </div>
        `;

        container.innerHTML = table;

    } catch (error) {
        console.error('Error loading job history:', error);
        container.innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle"></i>
                Failed to load job history: ${error.message}
            </div>
        `;
    }
}

/**
 * Get status badge HTML
 */
function getStatusBadge(status) {
    const badges = {
        'complete': '<span class="badge bg-success">Complete</span>',
        'processing': '<span class="badge bg-primary">Processing</span>',
        'failed': '<span class="badge bg-danger">Failed</span>',
        'pending': '<span class="badge bg-secondary">Pending</span>'
    };
    return badges[status] || '<span class="badge bg-secondary">Unknown</span>';
}

/**
 * Download file from job
 */
async function downloadJobFile(jobId, fileType) {
    try {
        const response = await fetch(`/api/jobs/${jobId}/download/${fileType}`);
        if (!response.ok) {
            throw new Error('File not found or no longer available');
        }

        // Get filename from Content-Disposition header
        const disposition = response.headers.get('Content-Disposition');
        let filename = `job_${jobId}_${fileType}.csv`;
        if (disposition && disposition.includes('filename=')) {
            filename = disposition.split('filename=')[1].replace(/"/g, '');
        }

        // Download file
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        showAlert('File downloaded successfully', 'success');
    } catch (error) {
        console.error('Error downloading file:', error);
        showAlert(error.message || 'Failed to download file', 'danger');
    }
}

/**
 * Delete customer
 */
async function deleteCustomer(customerId) {
    if (!confirm('Are you sure you want to delete this customer?')) return;

    try {
        const response = await fetch(`/api/customers/${customerId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showAlert('Customer deleted successfully', 'success');
            await loadCustomers();
        } else {
            const data = await response.json();
            showAlert(data.error || 'Failed to delete customer', 'danger');
        }
    } catch (error) {
        console.error('Error deleting customer:', error);
        showAlert('Error deleting customer', 'danger');
    }
}

/**
 * Reset customer form
 */
function resetCustomerForm() {
    document.getElementById('customer-form-title').textContent = 'Add New Customer';
    document.getElementById('customer-form').reset();
    document.getElementById('edit-customer-id').value = '';
    // Reset to default values
    document.getElementById('customer-service-type').value = '040';
    document.getElementById('customer-barcode-id').value = '00';
    document.getElementById('customer-sequence-start').value = '1';
    document.getElementById('customer-api-provider').value = 'usps';
}

// ========================================
// File Upload & Validation
// ========================================

/**
 * Handle file selection
 */
async function handleFileSelect() {
    // Validate form before allowing upload
    if (!validateForm()) {
        document.getElementById('file-input').value = '';
        return;
    }

    const fileInput = document.getElementById('file-input');
    const file = fileInput.files[0];

    if (!file) return;

    // Validate file type
    const validTypes = ['.csv', '.xlsx', '.xls'];
    const fileExt = '.' + file.name.split('.').pop().toLowerCase();

    if (!validTypes.includes(fileExt)) {
        showAlert('Invalid file type. Please upload CSV or Excel file.', 'danger');
        fileInput.value = '';
        return;
    }

    // Show upload status
    showUploadStatus('Uploading file...', 'info');

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            uploadedFileData = data;
            previewData = data.preview;
            showUploadStatus('File uploaded successfully!', 'success');
            showColumnMapping(data);
        } else {
            showAlert(data.error || 'Upload failed', 'danger');
            fileInput.value = '';
        }
    } catch (error) {
        console.error('Upload error:', error);
        showAlert('Error uploading file', 'danger');
        fileInput.value = '';
    }
}

/**
 * Validate form before upload
 */
function validateForm() {
    const customerId = document.getElementById('customer-select').value;
    const mailerId = document.getElementById('mailer-id').value;
    const sequence = document.getElementById('starting-sequence').value;

    if (!customerId) {
        showAlert('Please select a customer before uploading a file', 'warning');
        return false;
    }

    if (!mailerId || mailerId.length < 6) {
        showAlert('Please enter a valid Mailer ID (6 or 9 digits)', 'warning');
        return false;
    }

    if (!sequence || sequence < 1) {
        showAlert('Please enter a valid starting sequence number', 'warning');
        return false;
    }

    return true;
}

/**
 * Show upload status message
 */
function showUploadStatus(message, type) {
    const statusDiv = document.getElementById('upload-status');
    statusDiv.innerHTML = `
        <div class="alert alert-${type} alert-dismissible fade show">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
}

// ========================================
// Column Mapping
// ========================================

/**
 * Show column mapping section
 */
function showColumnMapping(data) {
    const section = document.getElementById('mapping-section');
    section.style.display = 'block';

    // Populate column dropdowns
    const columns = data.columns;
    const mapping = data.detected_mapping || {};

    populateColumnDropdown('map-street', columns, mapping.street);
    populateColumnDropdown('map-city', columns, mapping.city);
    populateColumnDropdown('map-state', columns, mapping.state);
    populateColumnDropdown('map-zip', columns, mapping.zip);
    populateColumnDropdown('map-zip4', columns, mapping.zip4, true); // true = optional field

    // Show preview table
    displayPreviewTable(data.preview, columns);

    // Show file info
    document.getElementById('file-info').textContent =
        `${data.row_count} rows, ${data.column_count} columns`;

    // Scroll to mapping section
    section.scrollIntoView({ behavior: 'smooth' });
}

/**
 * Populate a column mapping dropdown
 */
function populateColumnDropdown(elementId, columns, selectedColumn, isOptional = false) {
    const select = document.getElementById(elementId);

    // For optional fields, keep the default "None" option
    if (!isOptional) {
        select.innerHTML = '<option value="">-- Select column --</option>';
    } else {
        // Optional field already has "None" option in HTML
        // Just clear any dynamically added options
        while (select.options.length > 1) {
            select.remove(1);
        }
    }

    columns.forEach(column => {
        const option = document.createElement('option');
        option.value = column;
        option.textContent = column;
        if (column === selectedColumn) {
            option.selected = true;
        }
        select.appendChild(option);
    });
}

/**
 * Display preview table
 */
function displayPreviewTable(rows, columns) {
    const table = document.getElementById('preview-table');
    const thead = table.querySelector('thead');
    const tbody = table.querySelector('tbody');

    // Create header
    thead.innerHTML = `
        <tr>
            ${columns.map(col => `<th>${col}</th>`).join('')}
        </tr>
    `;

    // Create rows
    tbody.innerHTML = rows.map(row => `
        <tr>
            ${columns.map(col => `<td>${row[col] || ''}</td>`).join('')}
        </tr>
    `).join('');
}

// ========================================
// Processing
// ========================================

/**
 * Process file with IMB generation
 */
async function processFile() {
    // Get column mapping
    const mapping = {
        street: document.getElementById('map-street').value,
        city: document.getElementById('map-city').value,
        state: document.getElementById('map-state').value,
        zip: document.getElementById('map-zip').value,
        zip4: document.getElementById('map-zip4').value || null  // Optional field
    };

    // Validate mapping (only required fields)
    if (!mapping.street || !mapping.city || !mapping.state || !mapping.zip) {
        showAlert('Please map all required columns', 'warning');
        return;
    }

    // Get customer ID
    const customerId = parseInt(document.getElementById('customer-select').value);

    // Fetch customer to get their API provider preference
    let apiProvider = 'usps';  // default
    try {
        const customerResponse = await fetch(`/api/customers/${customerId}`);
        if (customerResponse.ok) {
            const customerData = await customerResponse.json();
            apiProvider = customerData.customer.api_provider || 'usps';
        }
    } catch (error) {
        console.warn('Could not fetch customer API provider, using default:', error);
    }

    // Get mail service mode
    const mailModeEl = document.querySelector('input[name="mail-mode"]:checked');
    const mailServiceMode = mailModeEl ? mailModeEl.value : null;

    // Get configuration
    const config = {
        customer_id: customerId,
        mailer_id: document.getElementById('mailer-id').value,
        starting_sequence: parseInt(document.getElementById('starting-sequence').value),
        service_type: document.getElementById('service-type').value,
        barcode_id: document.getElementById('barcode-id').value,
        mail_service_mode: mailServiceMode,
        api_provider: apiProvider
    };

    // Show progress modal
    const progressModal = safeShowModal('progressModal', {
        backdrop: 'static',
        keyboard: false
    });
    if (progressModal) progressModal.show();
    updateProgress(0, 'Starting processing...');

    try {
        const response = await fetch('/api/process', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({mapping, config})
        });

        const data = await response.json();

        if (response.ok) {
            // Processing complete
            safeHideModal('progressModal');
            displayResults(data, config);
        } else {
            safeHideModal('progressModal');
            showAlert(data.error || 'Processing failed', 'danger');
        }
    } catch (error) {
        console.error('Processing error:', error);
        safeHideModal('progressModal');
        showAlert('Error processing file', 'danger');
    }
}

/**
 * Update progress bar and status
 */
function updateProgress(percentage, statusText) {
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const progressStatus = document.getElementById('progress-status');

    progressBar.style.width = percentage + '%';
    progressText.textContent = Math.round(percentage) + '%';
    if (statusText) {
        progressStatus.textContent = statusText;
    }
}

// ========================================
// Results
// ========================================

/**
 * Display processing results
 */
function displayResults(data, config) {
    const summary = data.summary;
    const results = data.results;

    // Get customer name
    const customer = customers.find(c => c.id === config.customer_id);
    const customerName = customer ? customer.name : 'Unknown';

    // Update result info
    document.getElementById('result-customer-name').textContent = customerName;
    document.getElementById('result-filename').textContent = uploadedFileData.filename || 'file.csv';
    document.getElementById('result-timestamp').textContent = new Date().toLocaleString();

    // Update stats
    document.getElementById('stat-total').textContent = summary.total_records || 0;
    document.getElementById('stat-success').textContent = summary.successful || 0;
    document.getElementById('stat-failed').textContent = summary.failed || 0;
    document.getElementById('stat-api-calls').textContent = summary.api_calls || 0;

    // Show/hide error download button
    const errorsBtn = document.getElementById('download-errors-btn');
    if (summary.failed > 0) {
        errorsBtn.style.display = 'inline-block';
    } else {
        errorsBtn.style.display = 'none';
    }

    // Display results table
    displayResultsTable(results);

    // Show results modal
    const resultsModal = safeShowModal('resultsModal');
    if (resultsModal) resultsModal.show();
}

/**
 * Display results preview table
 */
function displayResultsTable(results) {
    if (!results || results.length === 0) {
        document.getElementById('results-table').innerHTML =
            '<p class="text-muted text-center">No results to display</p>';
        return;
    }

    const table = document.getElementById('results-table');
    const thead = table.querySelector('thead');
    const tbody = table.querySelector('tbody');

    // Get columns (first 50 results max)
    const displayResults = results.slice(0, 50);
    const columns = Object.keys(displayResults[0]);

    // Create header
    thead.innerHTML = `
        <tr>
            ${columns.map(col => `<th>${col}</th>`).join('')}
        </tr>
    `;

    // Create rows
    tbody.innerHTML = displayResults.map(row => `
        <tr>
            ${columns.map(col => {
                let value = row[col] || '';
                // Add badge for validation status
                if (col === 'validation_status') {
                    const badgeClass = value === 'SUCCESS' ? 'success' : 'danger';
                    value = `<span class="badge bg-${badgeClass}">${value}</span>`;
                }
                return `<td>${value}</td>`;
            }).join('')}
        </tr>
    `).join('');
}

// ========================================
// Download
// ========================================

/**
 * Download file
 */
function downloadFile(fileType) {
    window.location.href = `/api/download/${fileType}`;
}

// ========================================
// Utilities
// ========================================

/**
 * Show alert message
 */
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
    alertDiv.style.zIndex = '9999';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}
