"""
Transaction Cost Engine.

Orchestrates cost calculators to produce itemized, auditable TransactionCostBreakdown
records for simulated Executions.
"""

import uuid
from decimal import Decimal
from typing import Optional

from app.domains.execution.models import Execution
from app.domains.costs.models import (
    CostProfileVersion,
    TransactionCostBreakdown,
    AssetClass,
    BrokerageModel
)
from app.domains.costs.calculators import (
    TurnoverCalculator,
    BrokerageCalculator,
    StatutoryTaxCalculator,
    ExchangeChargeCalculator,
    SEBIFeeCalculator,
    StampDutyCalculator,
    GSTCalculator,
    FinancialRoundingPolicy
)


class TransactionCostEngine:
    """Pure domain service calculating auditable transaction costs."""

    @staticmethod
    def calculate_cost_breakdown(
        execution: Execution,
        profile_version: CostProfileVersion
    ) -> TransactionCostBreakdown:
        """
        Calculates itemized transaction charges for a simulated execution.

        Important Logic:
        1. Calculates gross turnover = price * quantity.
        2. Calculates brokerage, STT, exchange charges, SEBI fees, and stamp duty.
        3. Calculates GST on Taxable Base (Brokerage + Exchange Charges + SEBI Fees).
        4. Applies FinancialRoundingPolicy to individual itemized charges and total cost.
        """
        turnover = TurnoverCalculator.calculate_turnover(
            execution.execution_price,
            execution.quantity
        )

        brokerage_raw = BrokerageCalculator.calculate_brokerage(
            turnover=turnover,
            model_name=profile_version.brokerage_model.value,
            rate=profile_version.brokerage_rate,
            cap=profile_version.brokerage_cap,
            flat=profile_version.brokerage_flat
        )

        stt_raw = StatutoryTaxCalculator.calculate_stt(
            turnover=turnover,
            side=execution.side,
            buy_rate=profile_version.stt_buy_rate,
            sell_rate=profile_version.stt_sell_rate
        )

        exchange_raw = ExchangeChargeCalculator.calculate_exchange_charges(
            turnover=turnover,
            rate=profile_version.exchange_charge_rate
        )

        sebi_raw = SEBIFeeCalculator.calculate_sebi_fee(
            turnover=turnover,
            rate=profile_version.sebi_fee_rate
        )

        stamp_raw = StampDutyCalculator.calculate_stamp_duty(
            turnover=turnover,
            side=execution.side,
            rate=profile_version.stamp_duty_rate
        )

        # Taxable base for GST = Brokerage + Exchange Charges + SEBI Fees
        taxable_base = brokerage_raw + exchange_raw + sebi_raw
        gst_raw = GSTCalculator.calculate_gst(
            taxable_base=taxable_base,
            gst_rate=profile_version.gst_rate
        )

        # Apply financial currency rounding policy to each component
        brokerage = FinancialRoundingPolicy.round_currency(brokerage_raw)
        stt = FinancialRoundingPolicy.round_currency(stt_raw)
        exchange_charges = FinancialRoundingPolicy.round_currency(exchange_raw)
        sebi_fees = FinancialRoundingPolicy.round_currency(sebi_raw)
        stamp_duty = FinancialRoundingPolicy.round_currency(stamp_raw)
        gst = FinancialRoundingPolicy.round_currency(gst_raw)

        total_cost = brokerage + stt + exchange_charges + sebi_fees + stamp_duty + gst

        breakdown_id = f"COST_{uuid.uuid4().hex[:12]}"
        return TransactionCostBreakdown(
            id=breakdown_id,
            execution_id=execution.id,
            cost_profile_version_id=profile_version.id,
            turnover=FinancialRoundingPolicy.round_currency(turnover),
            brokerage=brokerage,
            stt=stt,
            exchange_charges=exchange_charges,
            sebi_fees=sebi_fees,
            stamp_duty=stamp_duty,
            gst=gst,
            total_cost=total_cost,
            metadata={
                "asset_class": profile_version.asset_class.value,
                "brokerage_model": profile_version.brokerage_model.value
            }
        )
