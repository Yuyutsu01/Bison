import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('bison_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

export interface Instrument {
  symbol: string;
  name: string;
  exchange: string;
  lot_size: number;
  tick_size: number;
  timeframes: string[];
}

export interface StrategyDSL {
  name: string;
  description?: string;
  version?: number;
  instrument: {
    symbol: string;
    exchange: string;
    timeframe: string;
  };
  entry: {
    operator: string;
    conditions: any[];
  };
  exit: {
    operator: string;
    conditions: any[];
  };
  risk: {
    stop_loss_percent?: number;
    target_percent?: number;
    trailing_stop_percent?: number;
    max_holding_bars?: number;
    end_of_day_exit: boolean;
  };
  position_sizing: {
    type: string;
    value: number;
  };
}

export interface StrategySummary {
  id: string;
  name: string;
  description?: string;
  current_version: number;
  created_at: string;
}

export interface TradeDTO {
  id: string;
  trade_identifier: string;
  symbol: string;
  side: string;
  entry_time: string;
  entry_price: number;
  exit_time?: string;
  exit_price?: number;
  quantity: number;
  gross_pnl: number;
  net_pnl: number;
  total_costs: number;
  exit_reason?: string;
  entry_indicators?: Record<string, number>;
  exit_indicators?: Record<string, number>;
}

export interface EquityPointDTO {
  timestamp: string;
  equity: number;
  cash: number;
  drawdown: number;
  drawdown_percent: number;
}

export interface BacktestDetailDTO {
  id: string;
  strategy_id: string;
  strategy_name: string;
  status: string;
  error_message?: string;
  initial_capital: number;
  final_capital?: number;
  total_net_pnl?: number;
  total_trades: number;
  win_rate?: number;
  profit_factor?: number;
  sharpe_ratio?: number;
  max_drawdown_percent?: number;
  equity_curve?: EquityPointDTO[];
  trades: TradeDTO[];
  created_at: string;
}
