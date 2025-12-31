// Main JavaScript for Admin Panel

// Format numbers with Persian locale
function formatNumber(num) {
    return parseFloat(num).toLocaleString('fa-IR');
}

// Format dates
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('fa-IR');
}

// Show toast notification
function showToast(message, type = 'info') {
    // Simple alert for now, can be replaced with a toast library
    const alertClass = type === 'error' ? 'alert-danger' : 
                      type === 'success' ? 'alert-success' : 'alert-info';
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert ${alertClass} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
    alertDiv.style.zIndex = '9999';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Confirm dialog with Persian text
function confirmAction(message) {
    return confirm(message);
}
