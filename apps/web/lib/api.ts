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

export interface PortfolioDTO {
  id: string;
  initial_capital: number;
  cash: number;
  equity: number;
  realized_pnl: number;
  unrealized_pnl: number;
  total_pnl: number;
  gross_exposure: number;
  net_exposure: number;
}

export interface PositionDTO {
  id: string;
  symbol: string;
  side: string;
  quantity: number;
  average_entry_price: number;
  current_price: number;
  realized_pnl: number;
  unrealized_pnl: number;
  status: string;
  opened_at: string;
  last_updated_at: string;
  holding_bars: number;
}

export interface RiskEventDTO {
  id: string;
  position_id?: string;
  symbol: string;
  event_type: string;
  timestamp: string;
  trigger_price: number;
  reason: string;
}

export interface EquityPointDTO {
  timestamp: string;
  equity: number;
  cash: number;
  drawdown: number;
  drawdown_percent: number;
}

export interface CostProfileVersionDTO {
  id: string;
  version: number;
  name: string;
  effective_from: string;
  effective_to: string;
  asset_class: string;
  brokerage_model: string;
  brokerage_rate: number;
  brokerage_cap: number;
  brokerage_flat: number;
  stt_buy_rate: number;
  stt_sell_rate: number;
  exchange_charge_rate: number;
  sebi_fee_rate: number;
  stamp_duty_rate: number;
  gst_rate: number;
}

export interface CostProfileDTO {
  id: string;
  name: string;
  description?: string;
  asset_class: string;
  versions: CostProfileVersionDTO[];
}

export interface TransactionCostBreakdownDTO {
  id: string;
  execution_id: string;
  turnover: number;
  brokerage: number;
  stt: number;
  exchange_charges: number;
  sebi_fees: number;
  stamp_duty: number;
  gst: number;
  other_charges: number;
  total_cost: number;
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
  portfolio?: PortfolioDTO;
  positions?: PositionDTO[];
  risk_events?: RiskEventDTO[];
  costs?: TransactionCostBreakdownDTO[];
  created_at: string;
}

export async function getCostProfiles(): Promise<CostProfileDTO[]> {
  const response = await apiClient.get<CostProfileDTO[]>('/cost-profiles');
  return response.data;
}

export async function getBacktestCosts(backtestId: string): Promise<TransactionCostBreakdownDTO[]> {
  const response = await apiClient.get<TransactionCostBreakdownDTO[]>(`/backtests/${backtestId}/costs`);
  return response.data;
}

