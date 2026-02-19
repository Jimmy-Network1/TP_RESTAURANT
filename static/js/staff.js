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

// Dynamic option rows on dish form (front-only helper)
const optionsContainer = document.querySelector('[data-options-list]');
const addOptionBtn = document.querySelector('[data-add-option]');

function createOptionRow() {
    const row = document.createElement('div');
    row.className = 'option-row';
    row.innerHTML = `
        <input type="text" name="variant_name_dummy" placeholder="Nom de l'option" />
        <input type="number" step="0.01" name="variant_price_dummy" placeholder="Prix + FCFA" />
        <button type="button" class="ghost-btn" data-remove-option aria-label="Supprimer">✕</button>
    `;
    row.querySelector('[data-remove-option]').addEventListener('click', () => row.remove());
    return row;
}

if (optionsContainer && addOptionBtn) {
    addOptionBtn.addEventListener('click', () => {
        optionsContainer.appendChild(createOptionRow());
    });
}
