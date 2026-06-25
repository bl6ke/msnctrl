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


if __name__ == "__main__":
    import json
    print(json.dumps(get_market_analysis(), indent=2))
