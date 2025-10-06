declare module "vitest" {
  export type TestFn = (name: string, fn: () => void | Promise<void>) => void;

  export const describe: TestFn;
  export const it: TestFn;
  export const test: TestFn;
  export const beforeEach: (fn: () => void | Promise<void>) => void;
  export const afterEach: (fn: () => void | Promise<void>) => void;
  export const expect: (value: unknown) => {
    toBe(value: unknown): void;
    toBeDefined(): void;
    toBeGreaterThan(value: number): void;
    toHaveLength(length: number): void;
    toContain(value: unknown): void;
    toBeTruthy(): void;
    toBeFalsy(): void;
    toEqual(value: unknown): void;
    [matcher: string]: (...args: unknown[]) => void;
  };
}
