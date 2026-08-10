import {
  createContext,
  useCallback,
  useContext,
  useLayoutEffect,
  useMemo,
  useState,
} from "react";

const STORAGE_KEY = "firefusion.sidebarCollapsed";

const SidebarCollapseContext = createContext(null);

export function SidebarCollapseProvider({ children }) {
  const [collapsed, setCollapsedState] = useState(() => {
    if (typeof window === "undefined") return false;
    try {
      return window.localStorage.getItem(STORAGE_KEY) === "1";
    } catch {
      return false;
    }
  });

  useLayoutEffect(() => {
    const w = collapsed ? "72px" : "305px";
    document.documentElement.style.setProperty("--sidebar-width", w);
    try {
      window.localStorage.setItem(STORAGE_KEY, collapsed ? "1" : "0");
    } catch {
      // ignore
    }
  }, [collapsed]);

  const setCollapsed = useCallback((value) => {
    setCollapsedState(Boolean(value));
  }, []);

  const toggle = useCallback(() => {
    setCollapsedState((c) => !c);
  }, []);

  const value = useMemo(
    () => ({ collapsed, setCollapsed, toggle }),
    [collapsed, setCollapsed, toggle]
  );

  return (
    <SidebarCollapseContext.Provider value={value}>
      {children}
    </SidebarCollapseContext.Provider>
  );
}

export function useSidebarCollapse() {
  const ctx = useContext(SidebarCollapseContext);
  if (!ctx) {
    return {
      collapsed: false,
      setCollapsed: () => {},
      toggle: () => {},
    };
  }
  return ctx;
}
