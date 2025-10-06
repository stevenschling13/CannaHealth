'use strict';

const isProduction = process.env.NODE_ENV === 'production';

function inject() {
  if (!isProduction) {
    return;
  }
  if (typeof document === 'undefined') {
    return;
  }
  if (document.getElementById('vercel-analytics')) {
    return;
  }
  const script = document.createElement('script');
  script.id = 'vercel-analytics';
  script.async = true;
  script.src = 'https://va.vercel-scripts.com/v1/script.js';
  document.head.appendChild(script);
}

function track(event, payload) {
  if (payload === void 0) {
    payload = {};
  }
  if (!isProduction && typeof console !== 'undefined') {
    console.debug('[analytics] track', event, payload);
  }
  return Promise.resolve();
}

function flush() {
  return Promise.resolve();
}

module.exports = {
  inject,
  track,
  flush,
  default: { inject, track, flush }
};
