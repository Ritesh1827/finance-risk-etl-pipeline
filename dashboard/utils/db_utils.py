"""
db_utils.py

Database helper functions for the Financial Risk ETL Dashboard.
"""

import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine
from dotenv import load_dotenv

# ----------------------------------------------------------
# Database Connection
# ----------------------------------------------------------

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)


# ----------------------------------------------------------
# Generic Query Helper
# ----------------------------------------------------------

def run_query(query: str):
    """Execute SQL query and return a dataframe."""
    return pd.read_sql(query, engine)


# ----------------------------------------------------------
# Dashboard KPIs
# ----------------------------------------------------------

@st.cache_data(ttl=300)
def get_table_count(table_name):
    query = f"""
        SELECT COUNT(*) AS count
        FROM {table_name};
    """

    return int(run_query(query).iloc[0]["count"])


# ----------------------------------------------------------
# Pipeline Monitoring
# ----------------------------------------------------------

@st.cache_data(ttl=30)
def latest_pipeline_run():

    query = """
        SELECT *
        FROM pipeline_runs
        ORDER BY run_id DESC
        LIMIT 1;
    """

    return run_query(query)


@st.cache_data(ttl=30)
def pipeline_history(limit=20):

    query = f"""
        SELECT
            run_id,
            start_time,
            end_time,
            duration_seconds,
            status,
            extracted_rows,
            loaded_rows,
            validation_errors,
            reconciliation_status
        FROM pipeline_runs
        ORDER BY run_id DESC
        LIMIT {limit};
    """

    return run_query(query)


# ----------------------------------------------------------
# Raw Prices
# ----------------------------------------------------------

@st.cache_data(ttl=300)
def latest_prices():

    query = """
        SELECT
            trade_date,
            ticker,
            open_price,
            high_price,
            low_price,
            close_price,
            volume
        FROM raw_prices
        ORDER BY trade_date;
    """

    df = run_query(query)

    df["trade_date"] = pd.to_datetime(df["trade_date"])

    return df


# ----------------------------------------------------------
# Daily Returns
# ----------------------------------------------------------

@st.cache_data(ttl=300)
def latest_returns():

    query = """
        SELECT
            trade_date,
            ticker,
            pct_return
        FROM daily_returns
        ORDER BY trade_date;
    """

    df = run_query(query)

    df["trade_date"] = pd.to_datetime(df["trade_date"])

    return df


# ----------------------------------------------------------
# Risk Metrics
# ----------------------------------------------------------

@st.cache_data(ttl=300)
def latest_risk():

    query = """
        SELECT
            trade_date,
            ticker,
            ma_short,
            ma_long,
            volatility_30d,
            var_95
        FROM risk_metrics
        ORDER BY trade_date;
    """

    df = run_query(query)

    df["trade_date"] = pd.to_datetime(df["trade_date"])

    return df


# ----------------------------------------------------------
# Sidebar Filters
# ----------------------------------------------------------

@st.cache_data(ttl=300)
def get_tickers():

    query = """
        SELECT DISTINCT ticker
        FROM raw_prices
        ORDER BY ticker;
    """

    return run_query(query)["ticker"].tolist()


# ----------------------------------------------------------
# Dashboard Filters
# ----------------------------------------------------------

def filter_prices(df, ticker, start_date, end_date):

    if ticker != "All":
        df = df[df["ticker"] == ticker]

    df = df[
        (df["trade_date"] >= pd.to_datetime(start_date))
        &
        (df["trade_date"] <= pd.to_datetime(end_date))
    ]

    return df


def filter_returns(df, ticker, start_date, end_date):

    if ticker != "All":
        df = df[df["ticker"] == ticker]

    df = df[
        (df["trade_date"] >= pd.to_datetime(start_date))
        &
        (df["trade_date"] <= pd.to_datetime(end_date))
    ]

    return df


def filter_risk(df, ticker, start_date, end_date):

    if ticker != "All":
        df = df[df["ticker"] == ticker]

    df = df[
        (df["trade_date"] >= pd.to_datetime(start_date))
        &
        (df["trade_date"] <= pd.to_datetime(end_date))
    ]

    return df


# ----------------------------------------------------------
# Dashboard KPIs (Filtered)
# ----------------------------------------------------------

def latest_close_price(price_df):

    if len(price_df) == 0:
        return None

    return float(price_df.iloc[-1]["close_price"])


def latest_return(returns_df):

    if len(returns_df) == 0:
        return None

    return float(returns_df.iloc[-1]["pct_return"])


def latest_var(risk_df):

    if len(risk_df) == 0:
        return None

    return float(risk_df.iloc[-1]["var_95"])


def latest_volatility(risk_df):

    if len(risk_df) == 0:
        return None

    return float(risk_df.iloc[-1]["volatility_30d"])


# ----------------------------------------------------------
# Dashboard Totals
# ----------------------------------------------------------

def total_database_rows():

    return (
        get_table_count("raw_prices")
        + get_table_count("daily_returns")
        + get_table_count("risk_metrics")
    )