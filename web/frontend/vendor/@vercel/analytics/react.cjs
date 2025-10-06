'use strict';

const React = require('react');
const core = require('./index.cjs');

function Analytics(props) {
  if (props === void 0) {
    props = {};
  }

  React.useEffect(() => {
    core.inject();
    return function () {};
  }, []);

  Analytics.beforeSend = typeof props.beforeSend === 'function' ? props.beforeSend : undefined;
  return null;
}

Analytics.track = core.track;
Analytics.inject = core.inject;

module.exports = {
  Analytics,
  default: Analytics
};
