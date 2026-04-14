import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ScoreboardListener } from "../components/ScoreboardListener";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "SaaS Dashboard",
  description: "Modern SaaS Application",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <ScoreboardListener />
        {children}
      </body>
    </html>
  );
}
