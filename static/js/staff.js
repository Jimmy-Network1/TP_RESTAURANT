// Filter tabs for orders
const statusTabs = document.querySelectorAll('[data-filter]');
const orderRows = document.querySelectorAll('[data-status]');

statusTabs.forEach(tab => {
    tab.addEventListener('click', () => {
        statusTabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        const value = tab.dataset.filter;
        orderRows.forEach(row => {
            const match = value === 'all' || row.dataset.status === value;
            row.style.display = match ? '' : 'none';
        });
    });
});

// Print invoice
const printBtn = document.querySelector('[data-print]');
if (printBtn) {
    printBtn.addEventListener('click', () => window.print());
}
