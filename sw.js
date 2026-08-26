const CACHE_NAME = 'afaq-v1';
const urlsToCache = [
  '/-/index.html',
  '/-/css/ui-qwen.css',
  '/-/js/cards.js',
  '/-/images/logo.jpg'
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE_NAME).then(c => c.addAll(urlsToCache)));
});

self.addEventListener('fetch', e => {
  e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
});
