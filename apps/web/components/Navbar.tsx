'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { TrendingUp, Cpu, BarChart2, Layers, LogOut, User } from 'lucide-react';

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      setToken(localStorage.getItem('bison_token'));
    }
  }, [pathname]);

  const handleLogout = () => {
    localStorage.removeItem('bison_token');
    setToken(null);
    router.push('/login');
  };

  return (
    <nav className="sticky top-0 z-50 glass-panel border-b border-gray-800 px-6 py-4 flex items-center justify-between">
      <Link href="/" className="flex items-center gap-3 group">
        <div className="p-2 rounded-xl bg-gradient-to-tr from-blue-600 to-emerald-500 text-white shadow-lg shadow-blue-500/20 group-hover:scale-105 transition-transform">
          <TrendingUp className="w-6 h-6" />
        </div>
        <div>
          <span className="text-xl font-bold bg-gradient-to-r from-white via-gray-200 to-gray-400 bg-clip-text text-transparent">
            Bison
          </span>
          <span className="ml-2 text-xs font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
            NSE / BSE Quant
          </span>
        </div>
      </Link>

      <div className="flex items-center gap-1 bg-gray-900/60 p-1.5 rounded-xl border border-gray-800">
        <Link
          href="/"
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            pathname === '/' ? 'bg-blue-600 text-white shadow-md' : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
          }`}
        >
          <BarChart2 className="w-4 h-4" />
          Dashboard
        </Link>
        <Link
          href="/strategies"
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            pathname.startsWith('/strategies') && pathname !== '/builder'
              ? 'bg-blue-600 text-white shadow-md'
              : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
          }`}
        >
          <Layers className="w-4 h-4" />
          Strategies
        </Link>
        <Link
          href="/builder"
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            pathname === '/builder' ? 'bg-blue-600 text-white shadow-md' : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
          }`}
        >
          <Cpu className="w-4 h-4" />
          Visual Builder
        </Link>
      </div>

      <div className="flex items-center gap-3">
        {token ? (
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 text-sm text-gray-400 hover:text-red-400 px-3 py-1.5 rounded-lg border border-gray-800 hover:border-red-500/30 transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Logout
          </button>
        ) : (
          <Link
            href="/login"
            className="flex items-center gap-2 text-sm bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg shadow-md transition-colors"
          >
            <User className="w-4 h-4" />
            Sign In
          </Link>
        )}
      </div>
    </nav>
  );
}
