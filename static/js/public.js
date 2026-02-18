// Mobile nav toggle
const burger = document.querySelector('[data-burger]');
const mobileMenu = document.querySelector('[data-mobile-menu]');
if (burger && mobileMenu) {
    burger.addEventListener('click', () => {
        mobileMenu.classList.toggle('show');
    });
}

// Page intro reveal (home)
function setupReveal() {
    const body = document.body;
    body.classList.add('is-mounted');
    const items = document.querySelectorAll('[data-reveal]');
    if (!items.length) return;
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('is-visible');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.15 });
    items.forEach(el => observer.observe(el));
}
document.addEventListener('DOMContentLoaded', setupReveal);

// Dropdown user
document.querySelectorAll('[data-dropdown]').forEach(dd => {
    dd.addEventListener('click', (e) => {
        e.stopPropagation();
        dd.classList.toggle('open');
    });
});
document.addEventListener('click', () => {
    document.querySelectorAll('[data-dropdown].open').forEach(el => el.classList.remove('open'));
});

// Marquer badge panier lors d'un update
function markBadge() {
    const b = document.querySelector('.cart-badge');
    if (!b) return;
    b.classList.remove('updated');
    void b.offsetWidth; // reflow
    b.classList.add('updated');
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
const badgeNodes = document.querySelectorAll('[data-cart-count]');
function updateBadge(count) {
    badgeNodes.forEach(b => {
        b.textContent = count;
        b.dataset.cartCount = count;
    });
    markBadge();
}

function getCsrfFromForm(form) {
    const token = form?.querySelector('input[name=csrfmiddlewaretoken]');
    if (token) return token.value;
    const match = document.cookie.split(';').map(c=>c.trim()).find(c=>c.startsWith('csrftoken='));
    return match ? match.split('=')[1] : '';
}

// Ajout au panier en AJAX
document.querySelectorAll('.cart-add-form').forEach(form => {
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const url = form.dataset.ajaxUrl;
        if (!url) return form.submit();
        const qty = form.querySelector('input[name=qty]')?.value || 1;
        const csrf = getCsrfFromForm(form);
        const res = await fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrf,
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({qty}),
        });
        if (res.ok) {
            const data = await res.json();
            updateBadge(data.cart_count);
            showToast('Ajouté au panier');
        } else {
            form.submit(); // fallback
        }
    });
});

// Cart quantity controls
function recalcTotal() {
    const lines = document.querySelectorAll('[data-line]');
    let total = 0;
    lines.forEach(line => {
        const price = Number(line.dataset.price || 0);
        const qty = Number(line.querySelector('[data-qty]').textContent);
        total += price * qty;
        const lineTotal = line.querySelector('[data-line-total]');
        if (lineTotal) lineTotal.textContent = (price * qty).toFixed(2) + ' FCFA';
    });
    const totalEls = document.querySelectorAll('[data-total]');
    totalEls.forEach(totalEl => totalEl.textContent = total.toFixed(2) + ' FCFA');
}

document.querySelectorAll('[data-line]').forEach(line => {
    const form = line.closest('form');
    if (!form) return;
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const action = e.submitter?.value || 'plus';
        const url = form.dataset.ajaxUrl || form.action;
        const csrf = getCsrfFromForm(form);
        const id = form.querySelector('input[name=id]')?.value;
        const res = await fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrf,
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({id, action}),
        });
        if (!res.ok) {
            form.submit();
            return;
        }
        const data = await res.json();
        if (data.removed) {
            line.remove();
        } else if (data.item_qty !== undefined) {
            const qtyEl = line.querySelector('[data-qty]');
            qtyEl.textContent = data.item_qty;
        }
        updateBadge(data.cart_count);
        recalcTotal();
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
    const qtyInput = document.querySelector('[data-qty-input]');
    qtyBox.addEventListener('click', (e)=>{
        if (e.target.matches('[data-plus]')) qtyEl.textContent = Number(qtyEl.textContent)+1;
        if (e.target.matches('[data-minus]')) qtyEl.textContent = Math.max(1, Number(qtyEl.textContent)-1);
        if (qtyInput) qtyInput.value = qtyEl.textContent;
    });
}
