"use client";

import Navbar from "../../components/Navbar";
import RequireAuth from "../../components/RequireAuth";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <RequireAuth>
      <Navbar />
      <main className="container">{children}</main>
    </RequireAuth>
  );
}
