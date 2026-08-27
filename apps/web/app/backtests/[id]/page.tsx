'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import PerformanceDashboard from '../../../components/PerformanceDashboard';
import { apiClient, BacktestDetailDTO } from '../../../lib/api';

export default function BacktestResultsPage() {
  const params = useParams();
  const backtestId = params.id as string;

  const [data, setData] = useState<BacktestDetailDTO | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let timer: NodeJS.Timeout;

    async function fetchBacktest() {
      try {
        const res = await apiClient.get(`/backtests/${backtestId}`);
        setData(res.data);
        setLoading(false);

        // Auto-poll if job is still QUEUED or RUNNING
        if (res.data.status === 'QUEUED' || res.data.status === 'RUNNING') {
          timer = setTimeout(fetchBacktest, 2000);
        }
      } catch (err: any) {
        setLoading(false);
        setError(err.response?.data?.detail || 'Failed to load backtest results.');
      }
    }

    if (backtestId) {
      fetchBacktest();
    }

    return () => clearTimeout(timer);
  }, [backtestId]);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto py-24 text-center space-y-4">
        <div className="animate-spin w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full mx-auto" />
        <h2 className="text-xl font-bold text-white">Running Backtest Simulation...</h2>
        <p className="text-sm text-gray-400">
          Calculating technical indicators, zero look-ahead signals, and Indian market statutory fees.
        </p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="max-w-md mx-auto py-16 text-center space-y-4">
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm font-medium">
          {error || 'Backtest data unavailable.'}
        </div>
      </div>
    );
  }

  return <PerformanceDashboard data={data} />;
}
