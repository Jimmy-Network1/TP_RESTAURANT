(function(){
  const cartKey = "saveur237_cart";

  function loadCart(){
    try { return JSON.parse(localStorage.getItem(cartKey)) || []; } catch(e){ return []; }
  }
  function saveCart(cart){ localStorage.setItem(cartKey, JSON.stringify(cart)); }
  function updateBadge(){
    const cart = loadCart();
    const count = cart.reduce((sum, item) => sum + item.qty, 0);
    document.querySelectorAll('.js-cart-count').forEach(el => { el.textContent = count; });
  }
  function showToast(msg){
    const toast = document.querySelector('.toast');
    if(!toast) return;
    toast.textContent = msg;
    toast.style.display = 'block';
    setTimeout(() => { toast.style.display = 'none'; }, 1400);
  }

  function addToCart(item){
    const cart = loadCart();
    const existing = cart.find(i => i.id === item.id && JSON.stringify(i.options || []) === JSON.stringify(item.options || []) && (i.note || "") === (item.note || ""));
    if(existing){ existing.qty += item.qty; }
    else { cart.push(item); }
    saveCart(cart);
    updateBadge();
    showToast(`${item.name} ajoute au panier`);
  }

  document.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-add-to-cart]');
    if(btn){
      const id = btn.dataset.id;
      const name = btn.dataset.name;
      const price = parseFloat(btn.dataset.price || '0');
      addToCart({id, name, price, qty: 1, options: [], note: ""});
      return;
    }
  });

  function renderCart(){
    const container = document.querySelector('#cart-items');
    if(!container) return;
    const cart = loadCart();
    if(cart.length === 0){
      container.innerHTML = '<div class="card">Votre panier est vide.</div>';
      const totalEl = document.querySelector('#cart-total');
      if(totalEl) totalEl.textContent = '0';
      return;
    }
    container.innerHTML = cart.map(item => `
      <div class="cart-item">
        <div>
          <strong>${item.name}</strong>
          ${item.options && item.options.length ? `<div class="muted">${item.options.join(', ')}</div>` : ''}
          ${item.note ? `<div class="muted">Note: ${item.note}</div>` : ''}
          <div class="muted">${item.price} FCFA</div>
        </div>
        <div class="qty">
          <button data-qty="dec" data-id="${item.id}" data-key="${encodeURIComponent(JSON.stringify(item.options||[]))}">-</button>
          <strong>${item.qty}</strong>
          <button data-qty="inc" data-id="${item.id}" data-key="${encodeURIComponent(JSON.stringify(item.options||[]))}">+</button>
          <button data-qty="remove" data-id="${item.id}" data-key="${encodeURIComponent(JSON.stringify(item.options||[]))}">x</button>
        </div>
      </div>
    `).join('');
    updateTotal();
  }

  function updateTotal(){
    const cart = loadCart();
    const total = cart.reduce((sum, item) => sum + (item.price * item.qty), 0);
    const totalEl = document.querySelector('#cart-total');
    if(totalEl) totalEl.textContent = total.toFixed(0);
    const summaryTotal = document.querySelector('#summary-total');
    if(summaryTotal) summaryTotal.textContent = total.toFixed(0);
  }

  document.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-qty]');
    if(!btn) return;
    const id = btn.dataset.id;
    const key = btn.dataset.key || "";
    const action = btn.dataset.qty;
    const cart = loadCart();
    const item = cart.find(i => i.id === id && encodeURIComponent(JSON.stringify(i.options||[])) === key);
    if(!item) return;
    if(action === 'inc') item.qty += 1;
    if(action === 'dec') item.qty = Math.max(1, item.qty - 1);
    if(action === 'remove'){
      const idx = cart.findIndex(i => i.id === id && encodeURIComponent(JSON.stringify(i.options||[])) === key);
      if(idx >= 0) cart.splice(idx, 1);
    }
    saveCart(cart);
    renderCart();
    updateBadge();
  });

  function checkoutBehavior(){
    const typeRadios = document.querySelectorAll('input[name="order_type"]');
    const addressBlock = document.querySelector('#address-block');
    function toggle(){
      const type = document.querySelector('input[name="order_type"]:checked')?.value;
      if(!addressBlock) return;
      addressBlock.style.display = (type === 'delivery') ? 'block' : 'none';
    }
    typeRadios.forEach(r => r.addEventListener('change', toggle));
    toggle();
  }

  function detailBehavior(){
    const baseEl = document.querySelector('#base-price');
    const totalEl = document.querySelector('#total-price');
    const qtyEl = document.querySelector('#qty');
    const noteEl = document.querySelector('#note');
    const noteCount = document.querySelector('#note-count');
    if(!baseEl || !totalEl || !qtyEl) return;

    let qty = 1;
    const base = parseFloat(baseEl.dataset.base || '0');
    let lastExtras = 0;

    function calc(){
      let extras = 0;
      document.querySelectorAll('input[data-extra]:checked').forEach(i => { extras += parseFloat(i.dataset.extra || '0'); });
      lastExtras = extras;
      const total = (base + extras) * qty;
      totalEl.textContent = total.toFixed(0);
    }

    document.addEventListener('click', (e) => {
      const btn = e.target.closest('[data-qty]');
      if(!btn) return;
      const action = btn.dataset.qty;
      if(action === 'inc') qty += 1;
      if(action === 'dec') qty = Math.max(1, qty - 1);
      qtyEl.textContent = qty;
      calc();
    });

    document.querySelectorAll('input[data-extra]').forEach(i => i.addEventListener('change', calc));

    if(noteEl && noteCount){
      noteEl.addEventListener('input', () => { noteCount.textContent = `${noteEl.value.length}/200`; });
    }

    const addBtn = document.querySelector('[data-add-detail]');
    if(addBtn){
      addBtn.addEventListener('click', () => {
        const requiredGroups = new Set();
        document.querySelectorAll('input[data-required="1"]').forEach(i => requiredGroups.add(i.dataset.group));
        let valid = true;
        requiredGroups.forEach(group => {
          if(!document.querySelector(`input[data-group="${group}"]:checked`)) valid = false;
        });
        const error = document.querySelector('#option-error');
        if(!valid){
          if(error) error.style.display = 'block';
          return;
        }
        if(error) error.style.display = 'none';

        const options = [];
        document.querySelectorAll('input[data-extra]:checked').forEach(i => {
          const label = i.parentElement.textContent.trim();
          options.push(label);
        });
        addToCart({
          id: addBtn.dataset.id,
          name: addBtn.dataset.name,
          price: base + lastExtras,
          qty,
          options,
          note: noteEl ? noteEl.value.trim() : ""
        });
      });
    }

    calc();
  }

  document.addEventListener('DOMContentLoaded', () => {
    updateBadge();
    renderCart();
    checkoutBehavior();
    detailBehavior();
  });
})();
