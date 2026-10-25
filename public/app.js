'use strict';
const $ = id => document.getElementById(id);
const form = $('calculator');
const presets = [...document.querySelectorAll('.preset')];
let selection = '40';
let hasResult = false;

function saveCalculation() {
  window.dispatchEvent(new CustomEvent('calculation-save', { detail: {
    price: $('price').value,
    percentage: selection === 'custom' ? $('percentage').value : selection
  } }));
}

function clearResults() {
  for (const id of ['total', 'original', 'profit']) $(id).textContent = '—';
  $('result-note').textContent = 'Your next sale, with the numbers figured out.';
}
function render(showErrors = false) {
  $('price-error').textContent = '';
  $('percentage-error').textContent = '';
  const percentage = selection === 'custom' ? $('percentage').value : selection;
  let valid = true;
  for (const [id, value, isPercent] of [['price', $('price').value, false], ['percentage', percentage, true]]) {
    try { PriceCalculator.parse(value, isPercent); }
    catch (error) {
      valid = false;
      if (showErrors) $(id + '-error').textContent = error.message;
    }
  }
  $('badge').textContent = selection === 'custom' ? 'Custom markup' : '+' + selection + '% markup';
  if (!valid) { clearResults(); return false; }
  if (!hasResult && !showErrors) return true;
  const result = PriceCalculator.calculate($('price').value, percentage);
  for (const id of ['total', 'original', 'profit']) $(id).textContent = PriceCalculator.format(result[id]);
  $('badge').textContent = '+' + result.percentage + '% markup';
  $('result-note').textContent = 'Profit = original price × ' + result.percentage + '%';
  return true;
}
presets.forEach(button => button.addEventListener('click', () => {
  selection = button.dataset.percent;
  presets.forEach(item => {
    item.classList.toggle('active', item === button);
    item.setAttribute('aria-pressed', String(item === button));
  });
  $('custom-field').hidden = selection !== 'custom';
  const valid = render();
  if (valid && hasResult && selection !== 'custom') saveCalculation();
  if (selection === 'custom') $('percentage').focus();
}));
form.addEventListener('submit', event => {
  event.preventDefault();
  hasResult = true;
  if (!render(true)) {
    if ($('price-error').textContent) $('price').focus();
    else $('percentage').focus();
  } else {
    saveCalculation();
    document.activeElement.blur();
    if (matchMedia('(max-width: 800px)').matches) {
      document.querySelector('.results').scrollIntoView({ block: 'nearest', behavior: 'auto' });
    }
  }
});

// Installation guidance stays out of the installed app.
const standalone = matchMedia('(display-mode: standalone)').matches || navigator.standalone;
const isIOS = /iPhone|iPad|iPod/.test(navigator.userAgent) ||
  (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
let dismissed = false;
try { dismissed = localStorage.getItem('install-tip-dismissed') === 'yes'; } catch {}
if (isIOS && !standalone && !dismissed) $('install-tip').hidden = false;
$('dismiss-install').addEventListener('click', () => {
  $('install-tip').hidden = true;
  try { localStorage.setItem('install-tip-dismissed', 'yes'); } catch {}
});
if ('serviceWorker' in navigator) {
  window.addEventListener('load', async () => {
    try {
      await navigator.serviceWorker.register('/sw.js');
      await navigator.serviceWorker.ready;
      $('app-status').textContent = 'Ready to use offline';
    } catch {
      $('app-status').textContent = 'Offline setup unavailable. You can still calculate here.';
    }
  });
}
for (const id of ['price', 'percentage']) $(id).addEventListener('input', () => render());
form.addEventListener('reset', () => {
  hasResult = false;
  selection = '40';
  $('custom-field').hidden = true;
  presets.forEach(button => {
    const active = button.dataset.percent === '40';
    button.classList.toggle('active', active);
    button.setAttribute('aria-pressed', String(active));
  });
  clearResults();
  $('price-error').textContent = $('percentage-error').textContent = '';
  $('badge').textContent = '+40% markup';
  $('price').focus();
});
