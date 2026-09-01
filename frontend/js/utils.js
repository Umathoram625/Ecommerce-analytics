const Utils = {
    formatCurrency(value) {
        if (value === null || value === undefined || isNaN(value)) return '$0.00';
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(value);
    },

    formatCompactCurrency(value) {
        if (value === null || value === undefined || isNaN(value)) return '$0';
        if (Math.abs(value) >= 1e6) {
            return '$' + (value / 1e6).toFixed(2) + 'M';
        }
        if (Math.abs(value) >= 1e3) {
            return '$' + (value / 1e3).toFixed(1) + 'K';
        }
        return Utils.formatCurrency(value);
    },

    formatNumber(value) {
        if (value === null || value === undefined || isNaN(value)) return '0';
        return new Intl.NumberFormat('en-US').format(value);
    },

    formatPercent(value) {
        if (value === null || value === undefined || isNaN(value)) return '0.00%';
        return value.toFixed(2) + '%';
    },

    showToast(message, type = 'info', duration = 3500) {
        const container = document.getElementById('toastContainer');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;

        const icons = {
            success: 'fa-solid fa-circle-check',
            error: 'fa-solid fa-circle-exclamation',
            info: 'fa-solid fa-circle-info'
        };

        toast.innerHTML = `
            <i class="${icons[type] || icons.info}"></i>
            <span>${message}</span>
        `;

        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    },

    debounce(func, wait = 300) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }
};
