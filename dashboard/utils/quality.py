"""
quality.py

Data Quality checks for the Financial Risk ETL Platform.
"""

import pandas as pd


# ----------------------------------------------------------
# Duplicate Rows
# ----------------------------------------------------------

def duplicate_rows(df):

    return int(df.duplicated().sum())


# ----------------------------------------------------------
# Null Values
# ----------------------------------------------------------

def null_values(df):

    return int(df.isnull().sum().sum())


# ----------------------------------------------------------
# Missing Trading Days
# ----------------------------------------------------------

def missing_business_days(price_df):

    if price_df.empty:
        return 0

    dates = (
        pd.to_datetime(price_df["trade_date"])
        .sort_values()
        .drop_duplicates()
    )

    expected = pd.date_range(
        start=dates.min(),
        end=dates.max(),
        freq="B",
    )

    return len(expected.difference(dates))


# ----------------------------------------------------------
# Freshness
# ----------------------------------------------------------

def freshness(price_df):

    if price_df.empty:
        return None

    latest = pd.to_datetime(
        price_df["trade_date"]
    ).max()

    today = pd.Timestamp.today().normalize()

    return int((today - latest).days)


# ----------------------------------------------------------
# Quality Score
# ----------------------------------------------------------

def quality_score(price_df):

    score = 100

    score -= duplicate_rows(price_df) * 5

    score -= null_values(price_df)

    score -= missing_business_days(price_df)

    score = max(score, 0)

    return score


# ----------------------------------------------------------
# Overall Status
# ----------------------------------------------------------

def quality_status(score):

    if score >= 95:
        return "Excellent"

    if score >= 80:
        return "Good"

    if score >= 60:
        return "Warning"

    return "Poor"


# ----------------------------------------------------------
# Main Dashboard Function
# ----------------------------------------------------------

def calculate_quality(price_df):

    score = quality_score(price_df)

    return {

        "duplicates": duplicate_rows(price_df),

        "nulls": null_values(price_df),

        "missing_days": missing_business_days(price_df),

        "freshness": freshness(price_df),

        "score": score,

        "status": quality_status(score)

    }