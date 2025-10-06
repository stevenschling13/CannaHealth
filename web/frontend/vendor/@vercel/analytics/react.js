import { useEffect } from 'react';
import { inject, track } from './index.js';

export function Analytics({ beforeSend } = {}) {
  useEffect(() => {
    inject();
    return () => {};
  }, []);

  Analytics.beforeSend = typeof beforeSend === 'function' ? beforeSend : undefined;
  return null;
}

Analytics.track = track;
Analytics.inject = inject;

export default Analytics;
