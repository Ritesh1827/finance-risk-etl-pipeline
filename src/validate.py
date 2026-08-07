"""
validate.py
Validation stage of the Financial Risk Data ETL Pipeline.

Runs schema, completeness, null, range, and duplicate checks on the raw
extracted data. Rows that fail hard checks are quarantined rather than
dropped silently, so nothing is lost without a trace. Also produces a
reconciliation summary comparing actual vs. expected row counts per
ticker, which is written to the audit trail.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

logger = logging.getLogger("validate")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "docs"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

EXPECTED_COLUMNS = {"Date", "Open", "High", "Low", "Close", "Volume", "ticker"}
MANDATORY_FIELDS = ["Date", "Close", "ticker"]

# Expected trading days for a ~2y daily pull. Real calendars vary slightly
# by ticker (holidays, listing date), so this is a tolerance band, not an
# exact match.
EXPECTED_ROWS_PER_TICKER = 502
ROW_COUNT_TOLERANCE = 10  # allow +/- this many rows before flagging


@dataclass
class ValidationResult:
    trusted: pd.DataFrame
    quarantined: pd.DataFrame
    reconciliation: pd.DataFrame
    issues: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """True if there were no schema-level or fatal issues."""
        return len(self.issues) == 0


# --------------------------------------------------------------------------
# Individual checks
# --------------------------------------------------------------------------

def check_schema(df: pd.DataFrame) -> list[str]:
    """Verify all expected columns are present. Missing columns are fatal."""
    issues = []
    missing = EXPECTED_COLUMNS - set(df.columns)
    if missing:
        issues.append(f"Missing expected columns: {sorted(missing)}")
    return issues


def check_completeness(df: pd.DataFrame, expected_tickers: list[str]) -> list[str]:
    """Verify every expected ticker actually made it into the extract."""
    issues = []
    present = set(df["ticker"].unique())
    missing = set(expected_tickers) - present
    if missing:
        issues.append(f"No rows at all for tickers: {sorted(missing)}")
    return issues


def flag_nulls(df: pd.DataFrame) -> pd.Series:
    """Return a boolean mask of rows with nulls in mandatory fields."""
    return df[MANDATORY_FIELDS].isnull().any(axis=1)


def flag_bad_ranges(df: pd.DataFrame) -> pd.Series:
    """
    Return a boolean mask of rows that fail basic price/volume sanity
    checks: negative values, or High/Low internally inconsistent.
    """
    negative_prices = (df[["Open", "High", "Low", "Close"]] < 0).any(axis=1)
    negative_volume = df["Volume"] < 0
    high_too_low = df["High"] < df[["Open", "Close", "Low"]].max(axis=1)
    low_too_high = df["Low"] > df[["Open", "Close", "High"]].min(axis=1)

    return negative_prices | negative_volume | high_too_low | low_too_high


def flag_duplicates(df: pd.DataFrame) -> pd.Series:
    """Return a boolean mask of duplicate (Date, ticker) rows, keeping the first."""
    return df.duplicated(subset=["Date", "ticker"], keep="first")


def build_reconciliation(df: pd.DataFrame, expected_tickers: list[str]) -> pd.DataFrame:
    """
    Compare actual row counts per ticker against the expected count,
    flagging any ticker outside the tolerance band.
    """
    actual_counts = df["ticker"].value_counts().to_dict()

    rows = []
    for ticker in expected_tickers:
        actual = actual_counts.get(ticker, 0)
        diff = actual - EXPECTED_ROWS_PER_TICKER
        status = "OK" if abs(diff) <= ROW_COUNT_TOLERANCE else "MISMATCH"
        rows.append({
            "ticker": ticker,
            "expected_rows": EXPECTED_ROWS_PER_TICKER,
            "actual_rows": actual,
            "difference": diff,
            "status": status,
        })

    recon_df = pd.DataFrame(rows)
    mismatches = recon_df[recon_df["status"] == "MISMATCH"]
    if not mismatches.empty:
        logger.warning(f"Reconciliation mismatches found:\n{mismatches}")
    else:
        logger.info("Reconciliation check passed for all tickers.")

    return recon_df


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------

def validate(df: pd.DataFrame, expected_tickers: list[str]) -> ValidationResult:
    """
    Run the full validation suite on the raw extract.

    Fatal issues (schema/completeness) are recorded but do not raise —
    the caller decides whether to abort the pipeline based on
    `result.passed`. Row-level issues (nulls, bad ranges, duplicates)
    result in those rows being split into `quarantined` rather than
    dropped outright.
    """
    issues = []
    issues += check_schema(df)
    issues += check_completeness(df, expected_tickers)

    if issues:
        logger.error(f"Fatal validation issues: {issues}")
        # Can't safely run row-level checks if schema itself is broken.
        empty = df.iloc[0:0]
        recon_df = pd.DataFrame()
        return ValidationResult(trusted=empty, quarantined=df, reconciliation=recon_df, issues=issues)

    null_mask = flag_nulls(df)
    range_mask = flag_bad_ranges(df)
    dup_mask = flag_duplicates(df)

    bad_mask = null_mask | range_mask | dup_mask

    quarantined = df[bad_mask].copy()
    trusted = df[~bad_mask].copy()

    if not quarantined.empty:
        logger.warning(
            f"Quarantined {len(quarantined)} rows "
            f"(nulls: {null_mask.sum()}, bad ranges: {range_mask.sum()}, "
            f"duplicates: {dup_mask.sum()})."
        )
    else:
        logger.info("No rows quarantined — all rows passed row-level checks.")

    reconciliation = build_reconciliation(trusted, expected_tickers)

    logger.info(
        f"Validation complete: {len(trusted)} trusted rows, "
        f"{len(quarantined)} quarantined rows."
    )

    return ValidationResult(
        trusted=trusted,
        quarantined=quarantined,
        reconciliation=reconciliation,
        issues=issues,
    )


def save_reports(result: ValidationResult) -> None:
    """Write quarantine and reconciliation reports to docs/ for the audit trail."""
    if not result.quarantined.empty:
        quarantine_path = REPORTS_DIR / "quarantined_rows.csv"
        result.quarantined.to_csv(quarantine_path, index=False)
        logger.info(f"Quarantined rows written to {quarantine_path}")

    if not result.reconciliation.empty:
        recon_path = REPORTS_DIR / "reconciliation_report.csv"
        result.reconciliation.to_csv(recon_path, index=False)
        logger.info(f"Reconciliation report written to {recon_path}")


# --------------------------------------------------------------------------
# Standalone test entry point
# --------------------------------------------------------------------------

if __name__ == "__main__":
    from extract import TICKERS, run_extraction

    raw_df = run_extraction()
    result = validate(raw_df, TICKERS)
    save_reports(result)

    if not result.passed:
        raise RuntimeError(f"Validation failed with fatal issues: {result.issues}")