import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, date

import pandas as pd
import pytz
import yfinance as yf

ET = pytz.timezone("America/New_York")

NQ = "NQ=F"
ES = "ES=F"

_CACHE_TTL = 300  # seconds
_cache: dict = {}
_cache_ts: float = 0.0


def _flatten(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """Drop ticker level from MultiIndex columns if yfinance returned one."""
    if isinstance(df.columns, pd.MultiIndex):
        df = df.xs(ticker, axis=1, level=1)
    return df


def _localize(df: pd.DataFrame) -> pd.DataFrame:
    """Convert index to ET, handling both naive and tz-aware indexes."""
    if df.index.tzinfo is None:
        df.index = df.index.tz_localize("UTC").tz_convert(ET)
    else:
        df.index = df.index.tz_convert(ET)
    return df


def get_previous_day_ohlc(ticker: str) -> dict:
    data = yf.download(ticker, period="5d", interval="1d", progress=False)
    if data.empty or len(data) < 2:
        return {}
    data = _flatten(data, ticker)
    prev = data.iloc[-2]
    return {
        "open":  round(float(prev["Open"]),  2),
        "high":  round(float(prev["High"]),  2),
        "low":   round(float(prev["Low"]),   2),
        "close": round(float(prev["Close"]), 2),
    }


def get_session_levels(ticker: str) -> dict:
    data = yf.download(ticker, period="2d", interval="1h", progress=False)
    if data.empty:
        return {}
    data = _flatten(data, ticker)
    data = _localize(data)  # guard: handles both naive and tz-aware indexes

    now = datetime.now(ET)
    today = now.date()

    asia_highs, asia_lows     = [], []
    london_highs, london_lows = [], []

    for ts, row in data.iterrows():
        hour = ts.hour
        d = ts.date()
        is_asia = (d == today - timedelta(days=1) and hour >= 20) or \
                  (d == today and hour < 2)
        is_london = d == today and 3 <= hour < 8
        if is_asia:
            asia_highs.append(float(row["High"]))
            asia_lows.append(float(row["Low"]))
        if is_london:
            london_highs.append(float(row["High"]))
            london_lows.append(float(row["Low"]))

    orb_data = yf.download(ticker, period="1d", interval="15m", progress=False)
    orb_high = orb_low = None
    if not orb_data.empty:
        orb_data = _flatten(orb_data, ticker)
        orb_data = _localize(orb_data)
        orb_candles = orb_data[
            (orb_data.index.date == today) &
            (orb_data.index.hour == 8) &
            (orb_data.index.minute < 15)
        ]
        if not orb_candles.empty:
            orb_high = round(float(orb_candles["High"].max()), 2)
            orb_low  = round(float(orb_candles["Low"].min()),  2)

    return {
        "asia": {
            "high": round(max(asia_highs), 2) if asia_highs else None,
            "low":  round(min(asia_lows),  2) if asia_lows  else None,
        },
        "london": {
            "high": round(max(london_highs), 2) if london_highs else None,
            "low":  round(min(london_lows),  2) if london_lows  else None,
        },
        "orb": {
            "high": orb_high,
            "low":  orb_low,
            "mid":  round((orb_high + orb_low) / 2, 2) if orb_high and orb_low else None,
        },
    }


def get_current_price(ticker: str) -> float | None:
    data = yf.download(ticker, period="1d", interval="1m", progress=False)
    if data.empty:
        return None
    data = _flatten(data, ticker)
    return round(float(data["Close"].iloc[-1]), 2)


def get_week_levels(ticker: str) -> dict:
    data = yf.download(ticker, period="1mo", interval="1d", progress=False)
    if data.empty:
        return {}
    data = _flatten(data, ticker)
    data = _localize(data)

    now = datetime.now(ET)
    week = now.isocalendar()[1]
    year = now.year

    # Week 1 of a new year: previous week is the last ISO week of the prior year.
    # Dec 28 is always in the final ISO week, so its week number is authoritative.
    if week == 1:
        dec_28 = date(year - 1, 12, 28)
        prev_week_num = dec_28.isocalendar()[1]
        prev_year = year - 1
    else:
        prev_week_num = week - 1
        prev_year = year

    current_week = data[data.index.map(
        lambda x: x.isocalendar()[1] == week and x.year == year
    )]
    prev_week = data[data.index.map(
        lambda x: x.isocalendar()[1] == prev_week_num and x.year == prev_year
    )]

    return {
        "current_week": {
            "high": round(float(current_week["High"].max()), 2) if not current_week.empty else None,
            "low":  round(float(current_week["Low"].min()),  2) if not current_week.empty else None,
        },
        "prev_week": {
            "high": round(float(prev_week["High"].max()), 2) if not prev_week.empty else None,
            "low":  round(float(prev_week["Low"].min()),  2) if not prev_week.empty else None,
        },
    }


def _build_snapshot(ticker: str) -> dict:
    return {
        "ticker":        ticker,
        "current_price": get_current_price(ticker),
        "prev_day":      get_previous_day_ohlc(ticker),
        "week":          get_week_levels(ticker),
        "sessions":      get_session_levels(ticker),
    }


def get_full_market_data(force_refresh: bool = False) -> dict:
    """Fetch NQ and ES snapshots in parallel, with a 5-minute cache."""
    global _cache, _cache_ts
    if not force_refresh and _cache and (time.time() - _cache_ts) < _CACHE_TTL:
        return _cache

    with ThreadPoolExecutor(max_workers=2) as pool:
        nq_future = pool.submit(_build_snapshot, NQ)
        es_future = pool.submit(_build_snapshot, ES)
        result = {
            "timestamp": datetime.now(ET).strftime("%Y-%m-%d %H:%M ET"),
            "NQ": nq_future.result(),
            "ES": es_future.result(),
        }

    _cache = result
    _cache_ts = time.time()
    return _cache


if __name__ == "__main__":
    import json
    print(json.dumps(get_full_market_data(), indent=2))
