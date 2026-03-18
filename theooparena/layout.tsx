import type { Metadata, Viewport } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "CodeQuest — The OOP Arena",
  description:
    "Learn Object-Oriented Programming by fighting monsters. Every attack reveals the class hierarchy and method calls behind the action.",
  keywords: [
    "OOP",
    "object-oriented programming",
    "educational game",
    "inheritance",
    "polymorphism",
    "Python",
    "coding tutorial",
  ],
  authors: [{ name: "CodeQuest" }],
  openGraph: {
    title: "CodeQuest — The OOP Arena",
    description: "Learn OOP by fighting monsters. Interactive browser RPG.",
    type: "website",
  },
};

export const viewport: Viewport = {
  themeColor: "#0a0a0f",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="font-sans antialiased bg-gray-950 text-gray-100 min-h-screen">
        {children}
      </body>
    </html>
  );
}
