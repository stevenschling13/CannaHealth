const isProduction = process.env.NODE_ENV === 'production';

export function inject() {
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

export function track(event, payload = {}) {
  if (!isProduction && typeof console !== 'undefined') {
    console.debug('[analytics] track', event, payload);
  }
  return Promise.resolve();
}

export function flush() {
  return Promise.resolve();
}

const Analytics = { inject, track, flush };

export default Analytics;
