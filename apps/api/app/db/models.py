"""
SQLAlchemy Relational ORM Models.

Defines persistence schema for Users, Strategies, Strategy Versions, Instruments, Datasets,
Backtest Runs, and Executed Trades.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from app.db.base import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class UserModel(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    strategies = relationship("StrategyModel", back_populates="user", cascade="all, delete-orphan")
    backtests = relationship("BacktestRunModel", back_populates="user", cascade="all, delete-orphan")


class StrategyModel(Base):
    __tablename__ = "strategies"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    current_version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("UserModel", back_populates="strategies")
    versions = relationship("StrategyVersionModel", back_populates="strategy", cascade="all, delete-orphan")


class StrategyVersionModel(Base):
    __tablename__ = "strategy_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    strategy_id = Column(String(36), ForeignKey("strategies.id"), nullable=False)
    version = Column(Integer, nullable=False)
    dsl_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    strategy = relationship("StrategyModel", back_populates="versions")
    backtest_runs = relationship("BacktestRunModel", back_populates="strategy_version")


class InstrumentModel(Base):
    __tablename__ = "instruments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    symbol = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    exchange = Column(String(20), default="NSE")
    asset_type = Column(String(50), default="EQUITY")
    lot_size = Column(Integer, default=1)
    tick_size = Column(Float, default=0.05)


class DatasetModel(Base):
    __tablename__ = "datasets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    symbol = Column(String(50), nullable=False)
    timeframe = Column(String(20), nullable=False)
    file_path = Column(String(512), nullable=False)
    row_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class BacktestRunModel(Base):
    __tablename__ = "backtest_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    strategy_version_id = Column(String(36), ForeignKey("strategy_versions.id"), nullable=False)
    dataset_id = Column(String(36), ForeignKey("datasets.id"), nullable=True)
    status = Column(String(50), default="QUEUED")  # QUEUED, RUNNING, COMPLETED, FAILED
    error_message = Column(Text, nullable=True)
    initial_capital = Column(Float, default=100000.0)
    final_capital = Column(Float, nullable=True)
    total_net_pnl = Column(Float, nullable=True)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, nullable=True)
    profit_factor = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    max_drawdown_percent = Column(Float, nullable=True)
    equity_curve_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("UserModel", back_populates="backtests")
    strategy_version = relationship("StrategyVersionModel", back_populates="backtest_runs")
    trades = relationship("TradeModel", back_populates="backtest_run", cascade="all, delete-orphan")


class TradeModel(Base):
    __tablename__ = "trades"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    backtest_run_id = Column(String(36), ForeignKey("backtest_runs.id"), nullable=False)
    trade_identifier = Column(String(50), nullable=False)
    symbol = Column(String(50), nullable=False)
    side = Column(String(20), nullable=False)
    entry_time = Column(String(50), nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_time = Column(String(50), nullable=True)
    exit_price = Column(Float, nullable=True)
    quantity = Column(Float, nullable=False)
    gross_pnl = Column(Float, default=0.0)
    net_pnl = Column(Float, default=0.0)
    total_costs = Column(Float, default=0.0)
    exit_reason = Column(String(100), nullable=True)
    entry_indicators_json = Column(JSON, nullable=True)
    exit_indicators_json = Column(JSON, nullable=True)

    backtest_run = relationship("BacktestRunModel", back_populates="trades")
