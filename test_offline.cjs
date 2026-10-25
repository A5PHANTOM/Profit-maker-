const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const handlers = {};
const stored = new Map();
const deleted = [];
const cache = {
  async addAll(paths) {
    for (const path of paths) {
      const file = 'public' + (path === '/' ? '/index.html' : path);
      stored.set(path, fs.readFileSync(file));
    }
  },
  async match(request) { return stored.get(new URL(request.url).pathname); }
};
vm.runInNewContext(fs.readFileSync('public/sw.js', 'utf8'), {
  URL,
  self: { addEventListener: (name, handler) => handlers[name] = handler,
    location: { origin: 'https://example.test' }, clients: { claim: async () => {} } },
  caches: { open: async () => cache, keys: async () => ['price-profit-v0', 'price-profit-v2', 'other-app'],
    delete: async key => deleted.push(key) },
  fetch: async () => { throw Error('Offline'); }
});
(async () => {
  let completion;
  handlers.install({ waitUntil: promise => completion = promise });
  await completion;
  handlers.activate({ waitUntil: promise => completion = promise });
  await completion;
  assert.deepEqual(deleted, ['price-profit-v0']);
  for (const path of ['/', '/index.html', '/style.css', '/app.js', '/calculator.js', '/icons/apple-touch-icon.png']) {
    handlers.fetch({ request: { method: 'GET', url: 'https://example.test' + path },
      respondWith: promise => completion = promise });
    assert.ok((await completion).length > 0, path + ' loads offline');
  }
  handlers.fetch({ request: { method: 'GET', url: 'https://external.test/' },
    respondWith: () => assert.fail('External requests must not be intercepted') });
  const manifest = JSON.parse(fs.readFileSync('public/manifest.webmanifest'));
  for (const icon of manifest.icons) {
    const data = fs.readFileSync('public/' + icon.src);
    const size = Number(icon.sizes.split('x')[0]);
    assert.equal(data.readUInt32BE(16), size);
    assert.equal(data.readUInt32BE(20), size);
  }
  console.log('Offline shell, cache cleanup, and app icon checks passed.');
})().catch(error => { console.error(error); process.exitCode = 1; });
