"""
run_pipeline.py
Orchestrates the full ETL pipeline: extract -> validate -> transform -> load.
Single entry point with stage-level logging and fail-fast error handling.
"""

import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    from extract import run_extraction, TICKERS
    from validate import validate, save_reports
    from transform import run_transformation
    from load import run_load

    try:
        logger.info("=== STAGE 1: EXTRACT ===")
        raw = run_extraction()

        logger.info("=== STAGE 2: VALIDATE ===")
        result = validate(raw, TICKERS)
        save_reports(result)

        logger.info("=== STAGE 3: TRANSFORM ===")
        tables = run_transformation(result.trusted)

        logger.info("=== STAGE 4: LOAD ===")
        run_load(tables)

        logger.info("=== PIPELINE COMPLETE ===")
        logger.info(
            f"Summary: {len(result.trusted)} trusted rows, "
            f"{len(result.quarantined) if result.quarantined is not None else 0} quarantined, "
            f"raw_prices={len(tables['raw_prices'])}, "
            f"daily_returns={len(tables['daily_returns'])}, "
            f"risk_metrics={len(tables['risk_metrics'])}."
        )

    except Exception as e:
        logger.error(f"=== PIPELINE FAILED: {e} ===")
        sys.exit(1)


if __name__ == "__main__":
    main()