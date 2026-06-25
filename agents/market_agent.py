import yfinance as yf
from datetime import datetime, timedelta
import pytz

ET = pytz.timezone("America/New_York")

NQ = "/NQ=F"
ES = "/ES=F"


def get_previous_day_ohlc(ticker: str) -> dict:
    """Fetch previous trading day OHLC for a futures ticker."""
    data = yf.download(ticker, period="5d", interval="1d", progress=False)
    if data.empty or len(data) < 2:
        return {}

    prev = data.iloc[-2]
    return {
        "open":  round(float(prev["Open"]),  2),
        "high":  round(float(prev["High"]),  2),
        "low":   round(float(prev["Low"]),   2),
        "close": round(float(prev["Close"]), 2),
    }


def get_session_levels(ticker: str) -> dict:
    """
    Fetch hourly candles for the past 2 days and calculate:
    - Asia session high/low  (8 PM – 2 AM ET)
    - London session high/low (3 AM – 8 AM ET)
    - ORB range              (8 AM – 8:15 AM ET, using 15m data)
    """
    data = yf.download(ticker, period="2d", interval="1h", progress=False)
    if data.empty:
        return {}

    data.index = data.index.tz_convert(ET)
    now = datetime.now(ET)
    today = now.date()

    asia_highs, asia_lows     = [], []
    london_highs, london_lows = [], []

    for ts, row in data.iterrows():
        hour = ts.hour
        date = ts.date()

        # Asia: 8 PM previous day to 2 AM today
        is_asia = (date == today - timedelta(days=1) and hour >= 20) or \
                  (date == today and hour < 2)
        # London: 3 AM to 8 AM today
        is_london = date == today and 3 <= hour < 8

        if is_asia:
            asia_highs.append(float(row["High"]))
            asia_lows.append(float(row["Low"]))
        if is_london:
            london_highs.append(float(row["High"]))
            london_lows.append(float(row["Low"]))

    # ORB: 8:00–8:15 AM using 15m candles
    orb_data = yf.download(ticker, period="1d", interval="15m", progress=False)
    orb_high, orb_low = None, None

    if not orb_data.empty:
        orb_data.index = orb_data.index.tz_convert(ET)
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
    """Fetch the most recent price."""
    data = yf.download(ticker, period="1d", interval="1m", progress=False)
    if data.empty:
        return None
    return round(float(data["Close"].iloc[-1]), 2)


def get_week_levels(ticker: str) -> dict:
    """Fetch current week high/low and previous week high/low."""
    data = yf.download(ticker, period="1mo", interval="1d", progress=False)
    if data.empty:
        return {}

    data.index = data.index.tz_localize("UTC").tz_convert(ET) \
        if data.index.tzinfo is None else data.index.tz_convert(ET)

    now  = datetime.now(ET)
    week = now.isocalendar()[1]
    year = now.year

    current_week = data[
        data.index.map(lambda x: x.isocalendar()[1] == week and x.year == year)
    ]
    prev_week = data[
        data.index.map(lambda x: x.isocalendar()[1] == week - 1 and x.year == year)
    ]

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


def build_market_snapshot(ticker: str) -> dict:
    """Assemble the full market snapshot for one ticker."""
    print(f"Fetching data for {ticker}...")
    return {
        "ticker":        ticker,
        "current_price": get_current_price(ticker),
        "prev_day":      get_previous_day_ohlc(ticker),
        "week":          get_week_levels(ticker),
        "sessions":      get_session_levels(ticker),
    }


def get_full_market_data() -> dict:
    """Fetch full snapshot for both NQ and ES."""
    return {
        "timestamp": datetime.now(ET).strftime("%Y-%m-%d %H:%M ET"),
        "NQ": build_market_snapshot(NQ),
        "ES": build_market_snapshot(ES),
    }


# ─── QUICK TEST ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import json
    data = get_full_market_data()
    print(json.dumps(data, indent=2))