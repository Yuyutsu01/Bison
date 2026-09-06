"""
Create portfolios, positions, portfolio_snapshots, and risk_events tables for Iteration 6.

Revision ID: 004_portfolio_risk
Revises: 003_orders_executions
Create Date: 2026-09-06
"""
from alembic import op
import sqlalchemy as sa

revision = '004_portfolio_risk'
down_revision = '003_orders_executions'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create portfolios table
    op.create_table(
        'portfolios',
        sa.Column('id', sa.String(length=36), nullable=False, primary_key=True),
        sa.Column('backtest_run_id', sa.String(length=36), sa.ForeignKey('backtest_runs.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('initial_capital', sa.Float(), nullable=False),
        sa.Column('cash', sa.Float(), nullable=False),
        sa.Column('equity', sa.Float(), nullable=False),
        sa.Column('realized_pnl', sa.Float(), server_default='0.0'),
        sa.Column('unrealized_pnl', sa.Float(), server_default='0.0'),
        sa.Column('total_pnl', sa.Float(), server_default='0.0'),
        sa.Column('gross_exposure', sa.Float(), server_default='0.0'),
        sa.Column('net_exposure', sa.Float(), server_default='0.0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # Create positions table
    op.create_table(
        'positions',
        sa.Column('id', sa.String(length=36), nullable=False, primary_key=True),
        sa.Column('portfolio_id', sa.String(length=36), sa.ForeignKey('portfolios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('instrument_id', sa.String(length=64), nullable=False),
        sa.Column('symbol', sa.String(length=50), nullable=False),
        sa.Column('side', sa.String(length=20), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('average_entry_price', sa.Float(), nullable=False),
        sa.Column('current_price', sa.Float(), nullable=False),
        sa.Column('realized_pnl', sa.Float(), server_default='0.0'),
        sa.Column('unrealized_pnl', sa.Float(), server_default='0.0'),
        sa.Column('status', sa.String(length=20), server_default='OPEN'),
        sa.Column('opened_at', sa.String(length=50), nullable=False),
        sa.Column('last_updated_at', sa.String(length=50), nullable=False),
        sa.Column('holding_bars', sa.Integer(), server_default='0'),
    )

    # Create portfolio_snapshots table
    op.create_table(
        'portfolio_snapshots',
        sa.Column('id', sa.String(length=36), nullable=False, primary_key=True),
        sa.Column('backtest_run_id', sa.String(length=36), sa.ForeignKey('backtest_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('timestamp', sa.String(length=50), nullable=False),
        sa.Column('cash', sa.Float(), nullable=False),
        sa.Column('equity', sa.Float(), nullable=False),
        sa.Column('gross_exposure', sa.Float(), server_default='0.0'),
        sa.Column('net_exposure', sa.Float(), server_default='0.0'),
        sa.Column('realized_pnl', sa.Float(), server_default='0.0'),
        sa.Column('unrealized_pnl', sa.Float(), server_default='0.0'),
        sa.Column('total_pnl', sa.Float(), server_default='0.0'),
        sa.Column('open_position_count', sa.Integer(), server_default='0'),
    )

    # Create risk_events table
    op.create_table(
        'risk_events',
        sa.Column('id', sa.String(length=36), nullable=False, primary_key=True),
        sa.Column('backtest_run_id', sa.String(length=36), sa.ForeignKey('backtest_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('position_id', sa.String(length=36), nullable=True),
        sa.Column('symbol', sa.String(length=50), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('timestamp', sa.String(length=50), nullable=False),
        sa.Column('trigger_price', sa.Float(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('risk_events')
    op.drop_table('portfolio_snapshots')
    op.drop_table('positions')
    op.drop_table('portfolios')
