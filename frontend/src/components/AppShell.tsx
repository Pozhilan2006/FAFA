import type { ReactNode } from "react";
import { Navigation } from "./Navigation";

export function AppShell({ children }: { children: ReactNode }) {
  return <div className="app-shell"><Navigation /><main>{children}</main></div>;
}
