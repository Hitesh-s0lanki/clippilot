import * as React from "react";

const MOBILE_BREAKPOINT = 768;
const MOBILE_QUERY = `(max-width: ${MOBILE_BREAKPOINT - 1}px)`;

function subscribe(onChange: () => void) {
  const query = window.matchMedia(MOBILE_QUERY);
  query.addEventListener("change", onChange);
  return () => query.removeEventListener("change", onChange);
}

/**
 * Whether the viewport is narrower than the sidebar's mobile breakpoint.
 *
 * `useSyncExternalStore` rather than the `useEffect` + `setState` pair shadcn
 * ships: a media query *is* an external store, and reading it through the
 * effect route means the first paint is always wrong and then corrected, which
 * React Compiler's lint rules reject as a cascading render. This subscribes
 * once and reads the real value during render instead.
 *
 * The server snapshot is `false` - there is no viewport to measure on the
 * server, so it assumes desktop, which is what the original hook's `undefined`
 * initial state also resolved to. The mobile sheet therefore never renders in
 * the server markup, it appears once the browser reports a narrow viewport.
 */
export function useIsMobile() {
  return React.useSyncExternalStore(
    subscribe,
    () => window.matchMedia(MOBILE_QUERY).matches,
    () => false,
  );
}
