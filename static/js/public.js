(function(){
  function getCookie(name){
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return '';
  }

  function updateBadge(){
    document.querySelectorAll('.js-cart-count').forEach(el => {
      const count = el.dataset.count || el.textContent || '0';
      el.textContent = count;
    });
  }

  function checkoutBehavior(){
    const typeRadios = document.querySelectorAll('input[name="order_type"]');
    const addressBlock = document.querySelector('#address-block');
    const paymentLabel = document.querySelector('#payment-label');
    function toggle(){
      const type = document.querySelector('input[name="order_type"]:checked')?.value;
      if(!addressBlock) return;
      addressBlock.style.display = (type === 'delivery') ? 'block' : 'none';
      if(paymentLabel){
        paymentLabel.textContent = (type === 'delivery') ? 'Paiement a la livraison' : 'Paiement au retrait';
      }
    }
    typeRadios.forEach(r => r.addEventListener('change', toggle));
    toggle();
  }

  document.addEventListener('DOMContentLoaded', () => {
    updateBadge();
    checkoutBehavior();
    fetch('/cart/summary/', { credentials: 'same-origin' })
      .then(r => r.ok ? r.json() : null)
      .then(json => {
        if (!json) return;
        document.querySelectorAll('.js-cart-count').forEach(el => {
          el.dataset.count = json.count;
          el.textContent = json.count;
        });
      })
      .catch(() => {});
    document.addEventListener('click', (e) => {
      const btn = e.target.closest('[data-qty-action]');
      if (!btn) return;
      const form = btn.closest('form');
      if (!form) return;
      const qtyInput = form.querySelector('input[name="qty"]');
      if (!qtyInput) return;
      e.preventDefault();
      e.stopPropagation();
      if (btn.dataset.busy === '1') return;
      btn.dataset.busy = '1';
      setTimeout(() => { btn.dataset.busy = '0'; }, 200);
      const current = parseInt(qtyInput.value || '0', 10) || 0;
      const next = btn.dataset.qtyAction === 'inc' ? current + 1 : Math.max(0, current - 1);
      qtyInput.value = String(next);
      if (typeof form.requestSubmit === 'function') {
        form.requestSubmit(btn);
      } else {
        form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
      }
    });
    document.querySelectorAll('form[data-ajax="1"]').forEach(form => {
      const qtyInput = form.querySelector('input[name="qty"]');
      if (qtyInput) {
        let timer = null;
        const submitNow = () => form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
        qtyInput.addEventListener('change', submitNow);
        qtyInput.addEventListener('input', () => {
          if (timer) clearTimeout(timer);
          timer = setTimeout(submitNow, 350);
        });
      }
      // handled by global click handler
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = e.submitter ? new FormData(form, e.submitter) : new FormData(form);
        const res = await fetch(form.action, {
          method: form.method || 'POST',
          headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCookie('csrftoken'),
          },
          body: data,
        });
        if (res.ok) {
          const json = await res.json();
          document.querySelectorAll('.js-cart-count').forEach(el => {
            el.dataset.count = json.count;
            el.textContent = json.count;
          });
          const totalEl = document.getElementById('cart-total');
          if (totalEl && json.total !== undefined) {
            totalEl.dataset.total = json.total;
            totalEl.textContent = `${json.total} FCFA`;
          }
          const itemsWrap = document.getElementById('cart-items');
          if (itemsWrap && json.items) {
            const keep = new Set(Object.keys(json.items));
            itemsWrap.querySelectorAll('[data-item-id]').forEach(row => {
              const id = row.getAttribute('data-item-id');
              if (!keep.has(id)) {
                row.remove();
              } else {
                const info = json.items[id];
                const line = row.querySelector('.js-line-total');
                const qtyInput = row.querySelector('input[name="qty"]');
                if (line && info.line_total !== undefined) {
                  line.dataset.lineTotal = info.line_total;
                  line.textContent = `${info.line_total} FCFA`;
                }
                if (qtyInput && info.qty !== undefined) {
                  qtyInput.value = info.qty;
                }
              }
            });
          }
          const emptyEl = document.getElementById('cart-empty');
          const checkoutBtn = document.getElementById('checkout-btn');
          if (emptyEl) {
            emptyEl.style.display = json.empty ? 'block' : 'none';
          }
          if (checkoutBtn) {
            checkoutBtn.style.display = json.empty ? 'none' : 'inline-flex';
          }
        } else {
          form.submit();
        }
      });
    });
  });
})();
