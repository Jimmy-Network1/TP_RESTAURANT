// Mobile nav toggle
const burger = document.querySelector('[data-burger]');
const mobileMenu = document.querySelector('[data-mobile-menu]');
if (burger && mobileMenu) {
    burger.addEventListener('click', () => {
        mobileMenu.classList.toggle('show');
    });
}

// Toast helper
function showToast(message) {
    const toast = document.querySelector('[data-toast]');
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 1800);
}

// Cart add buttons
const cartBadge = document.querySelector('[data-cart-count]');
const addButtons = document.querySelectorAll('[data-add]');
addButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        const current = Number(cartBadge?.textContent || 0);
        if (cartBadge) cartBadge.textContent = current + 1;
        showToast('Ajouté au panier');
    });
});

// Cart quantity controls
const cartLines = document.querySelectorAll('[data-line]');
function recalcTotal() {
    let total = 0;
    cartLines.forEach(line => {
        const price = Number(line.dataset.price || 0);
        const qty = Number(line.querySelector('[data-qty]').textContent);
        total += price * qty;
    });
    const totalEl = document.querySelector('[data-total]');
    if (totalEl) totalEl.textContent = total.toFixed(2) + ' FCFA';
}

cartLines.forEach(line => {
    line.addEventListener('click', (e) => {
        const target = e.target;
        if (target.matches('[data-plus]')) {
            const qtyEl = line.querySelector('[data-qty]');
            qtyEl.textContent = Number(qtyEl.textContent) + 1;
            recalcTotal();
        }
        if (target.matches('[data-minus]')) {
            const qtyEl = line.querySelector('[data-qty]');
            const next = Math.max(1, Number(qtyEl.textContent) - 1);
            qtyEl.textContent = next;
            recalcTotal();
        }
        if (target.matches('[data-remove]')) {
            line.remove();
            recalcTotal();
        }
    });
});

// Checkout delivery toggle
const deliveryRadios = document.querySelectorAll('[name="mode"]');
const addressBlock = document.querySelector('[data-address-block]');
deliveryRadios.forEach(r => {
    r.addEventListener('change', () => {
        if (r.value === 'delivery') {
            addressBlock?.classList.remove('hidden');
        } else {
            addressBlock?.classList.add('hidden');
        }
    });
});

// Quantity widget on dish detail
const qtyBox = document.querySelector('.quantity');
if (qtyBox) {
    const qtyEl = qtyBox.querySelector('[data-qty]');
    qtyBox.addEventListener('click', (e)=>{
        if (e.target.matches('[data-plus]')) qtyEl.textContent = Number(qtyEl.textContent)+1;
        if (e.target.matches('[data-minus]')) qtyEl.textContent = Math.max(1, Number(qtyEl.textContent)-1);
    });
}
