import type { FunctionComponent } from 'react';
import type AnalyticsCore from './index.js';

declare namespace AnalyticsComponent {
  export type BeforeSend = (event: string, payload: Record<string, unknown>) => Record<string, unknown> | void;
}

export interface AnalyticsProps {
  beforeSend?: AnalyticsComponent.BeforeSend;
}

export declare const Analytics: FunctionComponent<AnalyticsProps> & typeof AnalyticsCore;

export default Analytics;
