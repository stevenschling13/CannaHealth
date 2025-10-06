export interface TrackPayload {
  [key: string]: unknown;
}

export interface TrackOptions {
  payload?: TrackPayload;
}

export declare function inject(): void;
export declare function track(event: string, payload?: TrackPayload): Promise<void>;
export declare function flush(): Promise<void>;

declare const Analytics: {
  inject: typeof inject;
  track: typeof track;
  flush: typeof flush;
};

export default Analytics;
