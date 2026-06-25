import os
import anthropic
from dotenv import load_dotenv

from data.market_data import get_full_market_data


def _zone(price: float, high: float, low: float) -> str:
    """Return 'premium', 'discount', or 'equilibrium' relative to a range."""
    if high == low:
        return "equilibrium"
    mid = (high + low) / 2
    if price > mid:
        return "premium"
    if price < mid:
        return "discount"
    return "equilibrium"


def _analyze_ticker(snapshot: dict) -> dict:
    price   = snapshot.get("current_price")
    prev    = snapshot.get("prev_day", {})
    week    = snapshot.get("week", {})
    sessions = snapshot.get("sessions", {})
    asia    = sessions.get("asia", {})
    london  = sessions.get("london", {})
    orb     = sessions.get("orb", {})

    result: dict = {}

    # ── Previous day context ──────────────────────────────────────────────────
    pdh = prev.get("high")
    pdl = prev.get("low")
    if price and pdh and pdl:
        result["prev_day_zone"]     = _zone(price, pdh, pdl)
        result["prev_day_midpoint"] = round((pdh + pdl) / 2, 2)
        result["prev_day_range"]    = round(pdh - pdl, 2)

    # ── Weekly context ────────────────────────────────────────────────────────
    cwh = week.get("current_week", {}).get("high")
    cwl = week.get("current_week", {}).get("low")
    pwh = week.get("prev_week", {}).get("high")
    pwl = week.get("prev_week", {}).get("low")
    if price and cwh and cwl:
        result["weekly_zone"] = _zone(price, cwh, cwl)

    # ── Session bias ──────────────────────────────────────────────────────────
    if price and asia.get("high") and asia.get("low"):
        if price > asia["high"]:
            result["asia_bias"] = "bullish"
        elif price < asia["low"]:
            result["asia_bias"] = "bearish"
        else:
            result["asia_bias"] = "inside_range"

    if price and london.get("high") and london.get("low"):
        if price > london["high"]:
            result["london_bias"] = "bullish"
        elif price < london["low"]:
            result["london_bias"] = "bearish"
        else:
            result["london_bias"] = "inside_range"

    # ── ORB position ──────────────────────────────────────────────────────────
    if price and orb.get("high") and orb.get("low"):
        if price > orb["high"]:
            result["orb_position"] = "above_orb"
        elif price < orb["low"]:
            result["orb_position"] = "below_orb"
        else:
            result["orb_position"] = "inside_orb"

    # ── Key liquidity levels ──────────────────────────────────────────────────
    liquidity = {}
    if pdh:  liquidity["prev_day_high"]  = pdh
    if pdl:  liquidity["prev_day_low"]   = pdl
    if pwh:  liquidity["prev_week_high"] = pwh
    if pwl:  liquidity["prev_week_low"]  = pwl
    if asia.get("high"): liquidity["asia_high"]   = asia["high"]
    if asia.get("low"):  liquidity["asia_low"]    = asia["low"]
    if orb.get("high"):  liquidity["orb_high"]    = orb["high"]
    if orb.get("low"):   liquidity["orb_low"]     = orb["low"]
    result["liquidity_levels"] = liquidity

    return result


def get_market_analysis(force_refresh: bool = False) -> dict:
    """Return raw snapshots plus ICT analysis for NQ and ES."""
    data = get_full_market_data(force_refresh=force_refresh)
    return {
        "timestamp": data["timestamp"],
        "NQ": {**data["NQ"], "analysis": _analyze_ticker(data["NQ"])},
        "ES": {**data["ES"], "analysis": _analyze_ticker(data["ES"])},
    }


_SYSTEM_PROMPT = """You are an expert ICT (Inner Circle Trader) market analyst specializing in NQ (Nasdaq futures) and ES (S&P 500 futures). You apply ICT concepts including:

- Premium/discount zones relative to session and daily ranges
- Asia, London, and New York session analysis
- Opening Range Breakout (ORB) context (8:00–8:15am ET)
- Previous Day High/Low (PDH/PDL) as liquidity targets
- Previous Week High/Low (PWH/PWL) as macro levels
- Fair Value Gaps (FVG), order blocks, and market structure shifts
- Liquidity sweeps and stop hunts
- Kill zones (Asia 8pm–2am ET, London 3am–8am ET, NY 8am–12pm ET)

Provide concise, actionable analysis. When levels are referenced, include the exact price. When discussing bias, explain the ICT reasoning behind it."""


def _format_market_context(analysis: dict) -> str:
    ts = analysis.get("timestamp", "N/A")
    lines = [f"=== LIVE MARKET DATA (as of {ts} ET) ===\n"]

    for ticker in ("NQ", "ES"):
        snap = analysis.get(ticker, {})
        price = snap.get("current_price")
        prev = snap.get("prev_day", {})
        week = snap.get("week", {})
        sessions = snap.get("sessions", {})
        asia = sessions.get("asia", {})
        london = sessions.get("london", {})
        orb = sessions.get("orb", {})
        ict = snap.get("analysis", {})
        liq = ict.get("liquidity_levels", {})

        lines.append(f"--- {ticker} ---")
        lines.append(f"Current Price: {price}")

        lines.append(f"Prev Day: O={prev.get('open')} H={prev.get('high')} L={prev.get('low')} C={prev.get('close')}")
        if "prev_day_midpoint" in ict:
            lines.append(f"  Midpoint: {ict['prev_day_midpoint']}  Range: {ict.get('prev_day_range')}  Zone: {ict.get('prev_day_zone')}")

        cw = week.get("current_week", {})
        pw = week.get("prev_week", {})
        lines.append(f"Current Week: H={cw.get('high')} L={cw.get('low')}  Weekly Zone: {ict.get('weekly_zone', 'N/A')}")
        lines.append(f"Prev Week: H={pw.get('high')} L={pw.get('low')}")

        lines.append(f"Asia Session: H={asia.get('high')} L={asia.get('low')} Mid={asia.get('mid')}  Bias: {ict.get('asia_bias', 'N/A')}")
        lines.append(f"London Session: H={london.get('high')} L={london.get('low')} Mid={london.get('mid')}  Bias: {ict.get('london_bias', 'N/A')}")
        lines.append(f"ORB (8:00–8:15 ET): H={orb.get('high')} L={orb.get('low')} Mid={orb.get('mid')}  Position: {ict.get('orb_position', 'N/A')}")

        lines.append("Key Liquidity Levels:")
        for label, val in liq.items():
            lines.append(f"  {label}: {val}")

        lines.append("")

    return "\n".join(lines)


def chat(message: str, history: list) -> str:
    load_dotenv()
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in environment or .env file")

    analysis = get_market_analysis()
    market_context = _format_market_context(analysis)

    system = f"{_SYSTEM_PROMPT}\n\n{market_context}"

    messages = list(history) + [{"role": "user", "content": message}]

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        system=system,
        messages=messages,
    )

    return next(b.text for b in response.content if b.type == "text")


if __name__ == "__main__":
    import json
    print(json.dumps(get_market_analysis(), indent=2))
