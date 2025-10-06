declare module "react" {
  export type FC<P = Record<string, unknown>> = (props: P) => any;
  export const useState: <T>(initial: T) => [T, (value: T) => void];
  export const useEffect: (fn: () => void | (() => void), deps?: unknown[]) => void;
  export const useCallback: <T extends (...args: unknown[]) => unknown>(fn: T, deps: unknown[]) => T;
  const React: { FC: FC };
  export default React;
}

declare module "react-dom" {
  const ReactDOM: Record<string, unknown>;
  export default ReactDOM;
}

declare module "next" {
  export interface NextApiRequest {
    method?: string;
    query: Record<string, string | string[]>;
    body?: unknown;
  }

  export interface NextApiResponse<T = unknown> {
    status(code: number): NextApiResponse<T>;
    json(data: T): void;
    setHeader(name: string, value: string): void;
    end(data?: unknown): void;
  }
}

declare module "next/head" {
  const Head: any;
  export default Head;
}

declare module "next/dynamic" {
  const dynamic: (...args: unknown[]) => any;
  export default dynamic;
}

declare module "crypto" {
  export function randomUUID(): string;
}

declare const fetch: (input: RequestInfo, init?: RequestInit) => Promise<Response>;

declare var process: {
  env: Record<string, string | undefined>;
};

declare namespace JSX {
  interface IntrinsicElements {
    [elemName: string]: any;
  }
}
