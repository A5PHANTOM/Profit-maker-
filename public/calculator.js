(function (root) {
  'use strict';
  function parse(value, percentage = false) {
    let text = String(value).trim();
    if (percentage) text = text.replace(/%$/, '').trim();
    const pattern = percentage ? /^\d+(?:\.\d{1,4})?$/ : /^(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d{1,2})?$/;
    if (text.length > 32 || !pattern.test(text)) throw new Error(percentage ? 'Enter a percentage with up to 4 decimal places.' : 'Enter a price, such as 1000 or 1,250.50 (up to 2 decimals).');
    const numeric = Number(text.replace(/,/g, ''));
    if (percentage ? numeric > 1000000 : numeric <= 0 || numeric > 1000000000000) throw new Error(percentage ? 'Enter a percentage from 0 to 1,000,000.' : 'Price must be greater than 0 and at most 1,000,000,000,000.');
    return text.replace(/,/g, '');
  }
  function scaled(value, digits) {
    const [whole, fraction = ''] = value.split('.');
    return BigInt(whole) * 10n ** BigInt(digits) + BigInt(fraction.padEnd(digits, '0'));
  }
  function calculate(price, percentage) {
    const original = scaled(parse(price), 2);
    const percentText = parse(percentage, true);
    const percent = scaled(percentText, 4);
    // Exact integer arithmetic and half-up rounding to cents.
    const profit = (original * percent + 500000n) / 1000000n;
    return { original, profit, total: original + profit, percentage: Number(percentText) };
  }
  function format(cents) {
    return (cents / 100n).toLocaleString('en-US') + '.' + String(cents % 100n).padStart(2, '0');
  }
  const api = { parse, calculate, format };
  if (typeof module !== 'undefined') module.exports = api;
  else root.PriceCalculator = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
