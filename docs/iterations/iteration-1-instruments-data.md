# Iteration 1: Instruments & Market Data Layer

## Overview
Establishes reliable Indian market instrument models (NSE/BSE indices and equities), historical OHLCV data ingestion, data quality validation, and deterministic market fixtures.

---

## 🏛️ Components Implemented

### 1. Instrument Domain Model & Search API
- **SQLAlchemy Model**: [`InstrumentModel`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/db/models.py) (`id`, `symbol`, `name`, `exchange`, `asset_type`, `lot_size`, `tick_size`).
- **Supported Symbols**: NIFTY 50 (`NIFTY`), BANKNIFTY (`BANKNIFTY`), FINNIFTY, RELIANCE, TCS, INFY, HDFCBANK, ICICIBANK.
- **REST Endpoint**: `GET /api/v1/instruments` returning instrument metadata, lot sizes, tick sizes, and supported timeframes (`1m`, `5m`, `15m`, `1h`, `1d`).

### 2. Historical Data & Dataset Management
- **Dataset Model**: [`DatasetModel`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/db/models.py) tracking symbol, timeframe, row count, file path, and creation timestamp.
- **Data Ingestion**: [`MarketDataLoader`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/domains/market_data/loader.py) supporting CSV ingestion and column normalization.

### 3. Data Validation & Quality Reports
- **Hygiene Checks**:
  - **Duplicate Detection**: Identifies and drops duplicate timestamps.
  - **Chronological Sorting**: Sorts OHLCV rows by timestamp.
  - **OHLC Anomaly Validation**: Validates `High >= Low`, `High >= Open`, `High >= Close`, `Low <= Open`, `Low <= Close`, and positive prices.
- **Data Quality Report**: `DataQualityReport` dataclass returning `total_rows`, `missing_candles`, `duplicates`, `invalid_ohlc`, `status` (`PASSED`/`WARNING`/`FAILED`), and actionable diagnostic logs.

### 4. Deterministic Market Data Fixtures
Located in [`data/fixtures/`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/data/fixtures):
- `NIFTY_5M_FIXTURE`: [`nifty_5m.csv`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/data/fixtures/nifty_5m.csv)
- `BANKNIFTY_5M_FIXTURE`: [`banknifty_5m.csv`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/data/fixtures/banknifty_5m.csv)
- `EQUITY_5M_FIXTURE`: [`equity_5m.csv`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/data/fixtures/equity_5m.csv)

---

## 🚀 Deliverable Verification
Bison can ingest, validate, and report quality metrics on Indian market datasets. All test datasets pass validation cleanly.
