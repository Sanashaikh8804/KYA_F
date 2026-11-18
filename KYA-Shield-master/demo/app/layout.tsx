import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import "./home/landing.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter", display: "swap" });

export const metadata: Metadata = {
  title: "KYA-Shield | Agent trust infrastructure",
  description: "Verify AI agent identity, customer authority, and transaction risk before money moves."
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={inter.variable}>
      <body>{children}</body>
    </html>
  );
}
