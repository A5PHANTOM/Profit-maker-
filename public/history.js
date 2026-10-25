'use strict';
(() => {
  const status = document.getElementById('history-status');
  const list = document.getElementById('history-list');
  let deviceKey;
  let version = 0;
  let operations = Promise.resolve();
  try {
    deviceKey = localStorage.getItem('profit-history-key');
    if (!/^[a-f0-9]{64}$/.test(deviceKey || '')) {
      deviceKey = Array.from(crypto.getRandomValues(new Uint8Array(32)), byte => byte.toString(16).padStart(2, '0')).join('');
      localStorage.setItem('profit-history-key', deviceKey);
    }
  } catch {
    status.textContent = 'Enable browser storage to save and access your private history.';
    return;
  }
  async function request(method, data) {
    const response = await fetch('/api/history', {
      method, cache: 'no-store', headers: {
        Authorization: 'Bearer ' + deviceKey, 'Content-Type': 'application/json'
      }, ...(data ? { body: JSON.stringify(data) } : {})
    });
    let body;
    try { body = await response.json(); } catch { throw new Error('History requires the Vercel API. Use a deployed app to save calculations.'); }
    if (!response.ok) throw new Error(body.error || 'History unavailable. Try again.');
    return body;
  }
  function amount(value) {
    // Format server decimal strings without converting large amounts to floating point.
    const [whole, fraction = ''] = String(value).split('.');
    return BigInt(whole).toLocaleString('en-US') + '.' + fraction.padEnd(2, '0').slice(0, 2);
  }
  async function refresh() {
    const current = ++version;
    status.textContent = 'Loading history…';
    try {
      const data = await request('GET');
      if (current !== version) return;
      list.replaceChildren();
      for (const row of data.history) {
        const item = document.createElement('li');
        const heading = document.createElement('strong');
        heading.textContent = `${amount(row.original)} + ${row.percentage}% → ${amount(row.total)}`;
        const details = document.createElement('span');
        details.textContent = `Profit ${amount(row.profit)} · ${new Date(row.created_at).toLocaleString()}`;
        item.append(heading, details);
        list.append(item);
      }
      status.textContent = data.history.length ? `${data.history.length} saved calculation${data.history.length === 1 ? '' : 's'}` : 'No calculations yet. Tap Calculate to save your first one.';
    } catch (error) {
      if (current === version) status.textContent = navigator.onLine ? error.message : 'You’re offline. Calculations work, but history needs an internet connection.';
    }
  }
  window.addEventListener('calculation-save', event => {
    ++version;
    const data = { ...event.detail, id: crypto.randomUUID() };
    operations = operations.then(async () => {
      status.textContent = 'Saving calculation…';
      try {
        await request('POST', data);
        await refresh();
      } catch (error) {
        status.textContent = 'Calculation not saved. ' + (navigator.onLine ? error.message : 'Reconnect and tap Calculate again.');
      }
    });
  });
  document.getElementById('refresh-history').addEventListener('click', refresh);
  document.getElementById('clear-history').addEventListener('click', () => {
    if (!confirm('Delete all saved calculations for this browser?')) return;
    operations = operations.then(async () => {
      try { await request('DELETE'); await refresh(); }
      catch (error) { status.textContent = error.message; }
    });
  });
  window.addEventListener('online', refresh);
  refresh();
})();
