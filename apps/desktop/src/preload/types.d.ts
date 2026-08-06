export {};

declare global {
  interface Window {
    gestorWeb?: {
      getAppVersion: () => Promise<string>;
    };
  }
}
