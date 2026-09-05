"""
Create orders and executions tables for Iteration 5.

Revision ID: 003_orders_executions
Revises: 002_fixtures
Create Date: 2026-09-05
"""
from alembic import op
import sqlalchemy as sa

revision = '003_orders_executions'
down_revision = '002_fixtures'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create orders table
    op.create_table(
        'orders',
        sa.Column('id', sa.String(length=36), nullable=False, primary_key=True),
        sa.Column('backtest_run_id', sa.String(length=36), sa.ForeignKey('backtest_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('strategy_version_id', sa.String(length=36), sa.ForeignKey('strategy_versions.id'), nullable=False),
        sa.Column('signal_id', sa.String(length=64), nullable=False),
        sa.Column('instrument_id', sa.String(length=64), nullable=False),
        sa.Column('symbol', sa.String(length=50), nullable=False),
        sa.Column('side', sa.String(length=20), nullable=False),
        sa.Column('order_type', sa.String(length=20), nullable=False, server_default='MARKET'),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='CREATED'),
        sa.Column('execution_policy', sa.String(length=30), nullable=False, server_default='NEXT_BAR_OPEN'),
        sa.Column('created_at', sa.String(length=50), nullable=False),
        sa.Column('eligible_at', sa.String(length=50), nullable=False),
        sa.Column('idempotency_key', sa.String(length=64), nullable=False, index=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
    )

    # Create executions table
    op.create_table(
        'executions',
        sa.Column('id', sa.String(length=36), nullable=False, primary_key=True),
        sa.Column('order_id', sa.String(length=36), sa.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('backtest_run_id', sa.String(length=36), sa.ForeignKey('backtest_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('instrument_id', sa.String(length=64), nullable=False),
        sa.Column('symbol', sa.String(length=50), nullable=False),
        sa.Column('timestamp', sa.String(length=50), nullable=False),
        sa.Column('side', sa.String(length=20), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('reference_price', sa.Float(), nullable=False),
        sa.Column('execution_price', sa.Float(), nullable=False),
        sa.Column('slippage', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='SUCCESS'),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('executions')
    op.drop_table('orders')
