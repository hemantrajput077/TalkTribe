import { useEffect, useState } from "react";

// Runs an async loader and exposes { data, loading }. Re-runs when deps change.
export function useAsync(loader, deps = []) {
  const [state, setState] = useState({ data: null, loading: true });
  useEffect(() => {
    let alive = true;
    setState((s) => ({ ...s, loading: true }));
    loader().then((data) => alive && setState({ data, loading: false }));
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  return state;
}
