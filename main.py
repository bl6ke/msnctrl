import json
from agents.market_agent import get_market_analysis


def main():
    print("Fetching market data...\n")
    analysis = get_market_analysis()
    print(json.dumps(analysis, indent=2))


if __name__ == "__main__":
    main()
