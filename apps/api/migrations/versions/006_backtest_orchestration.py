"""
Add orchestration and execution tracking columns to backtest_runs.

Revision ID: 006_backtest_orchestration
Revises: 005_transaction_cost_engine
Create Date: 2026-09-08
"""
from alembic import op
import sqlalchemy as sa

revision = '006_backtest_orchestration'
down_revision = '005_transaction_cost_engine'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('backtest_runs', sa.Column('configuration_json', sa.JSON(), nullable=True))
    op.add_column('backtest_runs', sa.Column('run_identity', sa.String(length=64), nullable=True))
    op.add_column('backtest_runs', sa.Column('engine_version', sa.String(length=50), server_default='bison-backtest-engine-v0.8.0'))
    op.add_column('backtest_runs', sa.Column('progress', sa.Float(), server_default='0.0'))
    op.add_column('backtest_runs', sa.Column('processed_bars', sa.Integer(), server_default='0'))
    op.add_column('backtest_runs', sa.Column('total_bars', sa.Integer(), server_default='0'))
    op.add_column('backtest_runs', sa.Column('started_at', sa.DateTime(), nullable=True))
    op.add_column('backtest_runs', sa.Column('failed_at', sa.DateTime(), nullable=True))
    op.add_column('backtest_runs', sa.Column('cancelled_at', sa.DateTime(), nullable=True))
    op.add_column('backtest_runs', sa.Column('error_code', sa.String(length=50), nullable=True))
    op.add_column('backtest_runs', sa.Column('attempt_number', sa.Integer(), server_default='1'))
    op.add_column('backtest_runs', sa.Column('max_attempts', sa.Integer(), server_default='3'))
    op.add_column('backtest_runs', sa.Column('execution_metrics_json', sa.JSON(), nullable=True))
    op.add_column('backtest_runs', sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')))

    op.create_index('ix_backtest_runs_run_identity', 'backtest_runs', ['run_identity'])
    op.create_index('ix_backtest_runs_status', 'backtest_runs', ['status'])


def downgrade() -> None:
    op.drop_index('ix_backtest_runs_status', table_name='backtest_runs')
    op.drop_index('ix_backtest_runs_run_identity', table_name='backtest_runs')
    op.drop_column('backtest_runs', 'updated_at')
    op.drop_column('backtest_runs', 'execution_metrics_json')
    op.drop_column('backtest_runs', 'max_attempts')
    op.drop_column('backtest_runs', 'attempt_number')
    op.drop_column('backtest_runs', 'error_code')
    op.drop_column('backtest_runs', 'cancelled_at')
    op.drop_column('backtest_runs', 'failed_at')
    op.drop_column('backtest_runs', 'started_at')
    op.drop_column('backtest_runs', 'total_bars')
    op.drop_column('backtest_runs', 'processed_bars')
    op.drop_column('backtest_runs', 'progress')
    op.drop_column('backtest_runs', 'engine_version')
    op.drop_column('backtest_runs', 'run_identity')
    op.drop_column('backtest_runs', 'configuration_json')
