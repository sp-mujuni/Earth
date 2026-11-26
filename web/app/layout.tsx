import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "EARTH — Global Intelligence System",
  description: "A living intelligence platform for Earth's weather, hazards, geography and temporal systems.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
