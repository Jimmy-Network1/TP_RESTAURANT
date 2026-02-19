// show/hide password
document.querySelectorAll('[data-toggle]').forEach(btn => {
  btn.addEventListener('click', () => {
    const input = btn.closest('.input-group')?.querySelector('[data-password]');
    if (!input) return;
    input.type = input.type === 'password' ? 'text' : 'password';
  });
});
