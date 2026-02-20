(function(){
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
  });
})();
