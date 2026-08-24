import "./globals.css";
import Navbar from "@/components/Navbar";

export const metadata = {
  title: "QuantEngine - Algorithmic Trading Platform",
  description: "Next-generation event-driven algorithmic trading and backtesting engine.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Navbar />
        <main style={{ padding: "32px 24px", maxWidth: "1280px", margin: "0 auto" }}>
          {children}
        </main>
      </body>
    </html>
  );
}
