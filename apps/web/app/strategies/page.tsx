'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { Layers, Plus, Cpu, ArrowRight } from 'lucide-react';
import { apiClient, StrategySummary } from '../../lib/api';

export default function StrategiesPage() {
  const [strategies, setStrategies] = useState<StrategySummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchStrategies() {
      try {
        const res = await apiClient.get('/strategies');
        setStrategies(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchStrategies();
  }, []);

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-16">
      <div className="glass-panel p-8 rounded-3xl flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Layers className="w-6 h-6 text-blue-500" />
            Strategy Library & Versions
          </h1>
          <p className="text-sm text-gray-400 mt-1">Manage and edit saved visual strategies.</p>
        </div>
        <Link
          href="/builder"
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-emerald-600 hover:from-blue-500 text-white font-semibold text-sm shadow-lg shadow-blue-500/20"
        >
          <Plus className="w-4 h-4" />
          Create Strategy
        </Link>
      </div>

      {loading ? (
        <div className="text-center py-16 text-gray-500">Loading strategy library...</div>
      ) : strategies.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {strategies.map((s) => (
            <div key={s.id} className="glass-panel glass-panel-hover p-6 rounded-2xl space-y-4">
              <div className="flex items-center justify-between border-b border-gray-800 pb-3">
                <h3 className="text-lg font-bold text-white">{s.name}</h3>
                <span className="text-xs font-mono font-bold bg-blue-500/10 text-blue-400 px-2.5 py-1 rounded-full border border-blue-500/20">
                  Version v{s.current_version}
                </span>
              </div>
              <p className="text-xs text-gray-400">
                Created: {new Date(s.created_at).toLocaleDateString()}
              </p>
              <div className="flex items-center justify-between pt-2">
                <Link
                  href={`/builder?id=${s.id}`}
                  className="flex items-center gap-2 text-xs font-semibold text-blue-400 hover:text-blue-300"
                >
                  <Cpu className="w-4 h-4" />
                  Edit in Visual Builder
                </Link>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="glass-panel p-12 rounded-3xl text-center space-y-4">
          <p className="text-gray-400">No saved strategies found in your library yet.</p>
          <Link
            href="/builder"
            className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold shadow-md"
          >
            Build First Strategy
          </Link>
        </div>
      )}
    </div>
  );
}
