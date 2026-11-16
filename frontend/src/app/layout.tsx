import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "../lib/auth";
import { LangProvider } from "../lib/i18n";

export const metadata: Metadata = {
  title: "CareerCoach",
  description: "Agentic AI career coach",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <LangProvider>
          <AuthProvider>{children}</AuthProvider>
        </LangProvider>
      </body>
    </html>
  );
}
