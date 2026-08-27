import type { Metadata } from 'next';
import './globals.css';
import Navbar from '../components/Navbar';

export const metadata: Metadata = {
  title: 'Bison – Production Algorithmic Trading Platform (NSE / BSE)',
  description: 'Event-driven, zero look-ahead bias quantitative strategy builder and backtesting engine for Indian market traders.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-[#090D16] text-gray-100 flex flex-col">
        <Navbar />
        <main className="flex-1 container mx-auto px-4 pt-8 pb-16">
          {children}
        </main>
      </body>
    </html>
  );
}
