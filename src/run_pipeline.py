"""
run_pipeline.py
Orchestrates the full ETL pipeline:
Extract -> Validate -> Transform -> Load
with pipeline execution metadata logging.
"""

import logging
import sys
import os
from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)

load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL"))


def log_pipeline_run(
    start_time,
    end_time,
    status,
    extracted_rows,
    loaded_rows,
    validation_errors,
    reconciliation_status,
):
    duration = (end_time - start_time).total_seconds()

    record = pd.DataFrame(
        [
            {
                "start_time": start_time,
                "end_time": end_time,
                "duration_seconds": duration,
                "status": status,
                "extracted_rows": extracted_rows,
                "loaded_rows": loaded_rows,
                "validation_errors": validation_errors,
                "reconciliation_status": reconciliation_status,
            }
        ]
    )

    record.to_sql(
        "pipeline_runs",
        engine,
        if_exists="append",
        index=False,
    )


def main():

    from extract import run_extraction, TICKERS
    from validate import validate, save_reports
    from transform import run_transformation
    from load import run_load

    start_time = datetime.now()

    extracted_rows = 0
    loaded_rows = 0
    validation_errors = 0
    reconciliation_status = "PASS"

    try:

        logger.info("=== STAGE 1: EXTRACT ===")
        raw = run_extraction()
        extracted_rows = len(raw)

        logger.info("=== STAGE 2: VALIDATE ===")
        result = validate(raw, TICKERS)
        save_reports(result)

        validation_errors = (
            len(result.quarantined)
            if result.quarantined is not None
            else 0
        )

        logger.info("=== STAGE 3: TRANSFORM ===")
        tables = run_transformation(result.trusted)

        logger.info("=== STAGE 4: LOAD ===")
        run_load(tables)

        loaded_rows = len(tables["risk_metrics"])

        logger.info("=== PIPELINE COMPLETE ===")

        logger.info(
            f"Summary: {len(result.trusted)} trusted rows, "
            f"{validation_errors} quarantined, "
            f"raw_prices={len(tables['raw_prices'])}, "
            f"daily_returns={len(tables['daily_returns'])}, "
            f"risk_metrics={loaded_rows}."
        )

        end_time = datetime.now()

        log_pipeline_run(
            start_time,
            end_time,
            "SUCCESS",
            extracted_rows,
            loaded_rows,
            validation_errors,
            reconciliation_status,
        )

    except Exception as e:

        logger.error(f"=== PIPELINE FAILED: {e} ===")

        end_time = datetime.now()

        log_pipeline_run(
            start_time,
            end_time,
            "FAILED",
            extracted_rows,
            loaded_rows,
            validation_errors,
            "FAILED",
        )

        sys.exit(1)


if __name__ == "__main__":
    main()