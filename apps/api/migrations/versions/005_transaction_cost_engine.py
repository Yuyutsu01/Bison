"""
Create cost_profiles, cost_profile_versions, and transaction_costs tables for Iteration 7.

Revision ID: 005_transaction_cost_engine
Revises: 004_portfolio_risk
Create Date: 2026-09-07
"""
from alembic import op
import sqlalchemy as sa

revision = '005_transaction_cost_engine'
down_revision = '004_portfolio_risk'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create cost_profiles table
    op.create_table(
        'cost_profiles',
        sa.Column('id', sa.String(length=36), nullable=False, primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('asset_class', sa.String(length=50), server_default='EQUITY_INTRADAY'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # Create cost_profile_versions table
    op.create_table(
        'cost_profile_versions',
        sa.Column('id', sa.String(length=36), nullable=False, primary_key=True),
        sa.Column('cost_profile_id', sa.String(length=36), sa.ForeignKey('cost_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('effective_from', sa.String(length=50), nullable=False),
        sa.Column('effective_to', sa.String(length=50), nullable=False),
        sa.Column('asset_class', sa.String(length=50), nullable=False),
        sa.Column('brokerage_model', sa.String(length=50), server_default='PERCENTAGE_WITH_CAP'),
        sa.Column('brokerage_rate', sa.Float(), server_default='0.0003'),
        sa.Column('brokerage_cap', sa.Float(), server_default='20.0'),
        sa.Column('brokerage_flat', sa.Float(), server_default='20.0'),
        sa.Column('stt_buy_rate', sa.Float(), server_default='0.0'),
        sa.Column('stt_sell_rate', sa.Float(), server_default='0.00025'),
        sa.Column('exchange_charge_rate', sa.Float(), server_default='0.0000345'),
        sa.Column('sebi_fee_rate', sa.Float(), server_default='0.000001'),
        sa.Column('stamp_duty_rate', sa.Float(), server_default='0.00003'),
        sa.Column('gst_rate', sa.Float(), server_default='0.18'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # Add cost_profile_version_id column to backtest_runs
    op.add_column(
        'backtest_runs',
        sa.Column('cost_profile_version_id', sa.String(length=36), sa.ForeignKey('cost_profile_versions.id'), nullable=True)
    )

    # Create transaction_costs table
    op.create_table(
        'transaction_costs',
        sa.Column('id', sa.String(length=36), nullable=False, primary_key=True),
        sa.Column('execution_id', sa.String(length=36), sa.ForeignKey('executions.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('backtest_run_id', sa.String(length=36), sa.ForeignKey('backtest_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('cost_profile_version_id', sa.String(length=36), sa.ForeignKey('cost_profile_versions.id'), nullable=False),
        sa.Column('turnover', sa.Float(), nullable=False),
        sa.Column('brokerage', sa.Float(), nullable=False),
        sa.Column('stt', sa.Float(), nullable=False),
        sa.Column('exchange_charges', sa.Float(), nullable=False),
        sa.Column('sebi_fees', sa.Float(), nullable=False),
        sa.Column('stamp_duty', sa.Float(), nullable=False),
        sa.Column('gst', sa.Float(), nullable=False),
        sa.Column('other_charges', sa.Float(), server_default='0.0'),
        sa.Column('total_cost', sa.Float(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('transaction_costs')
    op.drop_column('backtest_runs', 'cost_profile_version_id')
    op.drop_table('cost_profile_versions')
    op.drop_table('cost_profiles')
