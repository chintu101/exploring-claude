import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CodeQuest — The OOP Arena",
  description: "Learn Object-Oriented Programming by fighting monsters. Every attack reveals the class hierarchy behind it.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ margin: 0, background: "#080810", color: "#e2e8f0" }}>
        {children}
      </body>
    </html>
  );
}
