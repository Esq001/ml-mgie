// General application JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, 5000);
    });

    // Confirm dialogs for dangerous actions
    document.querySelectorAll('[data-confirm]').forEach(function(el) {
        el.addEventListener('click', function(e) {
            if (!confirm(this.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });

    // Tooltips
    const tooltipTriggers = document.querySelectorAll('[title]');
    tooltipTriggers.forEach(function(el) {
        if (el.closest('.engagement-table') || el.closest('.tree-node')) {
            new bootstrap.Tooltip(el, { trigger: 'hover', delay: { show: 500 } });
        }
    });
});
