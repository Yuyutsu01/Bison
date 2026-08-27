'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { TrendingUp, User, Lock, ArrowRight } from 'lucide-react';
import { apiClient } from '../../lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await apiClient.post('/auth/login', { email, password });
      localStorage.setItem('bison_token', res.data.access_token);
      router.push('/');
    } catch (err: any) {
      setLoading(false);
      setError(err.response?.data?.detail || 'Login failed. Please check credentials.');
    }
  };

  return (
    <div className="max-w-md mx-auto pt-12 pb-16">
      <div className="glass-panel p-8 rounded-3xl space-y-6 border border-gray-800">
        <div className="text-center space-y-2">
          <div className="inline-flex p-3 rounded-2xl bg-gradient-to-tr from-blue-600 to-emerald-500 text-white shadow-lg shadow-blue-500/20 mb-2">
            <TrendingUp className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-bold text-white">Sign In to Bison</h1>
          <p className="text-xs text-gray-400">Access your quantitative trading dashboard</p>
        </div>

        {error && (
          <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-xs font-medium">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-xs text-gray-400 uppercase font-bold tracking-wider">Email Address</label>
            <div className="relative mt-1">
              <User className="w-4 h-4 text-gray-500 absolute left-3.5 top-3" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="trader@bison.com"
                className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-gray-900 border border-gray-800 text-white text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="text-xs text-gray-400 uppercase font-bold tracking-wider">Password</label>
            <div className="relative mt-1">
              <Lock className="w-4 h-4 text-gray-500 absolute left-3.5 top-3" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-gray-900 border border-gray-800 text-white text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-blue-600 to-emerald-600 hover:from-blue-500 hover:to-emerald-500 text-white font-semibold text-sm shadow-lg shadow-blue-500/25 transition-all flex items-center justify-center gap-2"
          >
            {loading ? 'Signing in...' : 'Sign In'}
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        <div className="text-center text-xs text-gray-400 pt-2 border-t border-gray-800">
          Don't have an account?{' '}
          <Link href="/register" className="text-blue-400 hover:underline font-semibold">
            Register Trader Account
          </Link>
        </div>
      </div>
    </div>
  );
}
