"""Fail-fast import health check for runtime-critical modules."""

MODULES = [
    "src.core.engine",
    "src.capital.aave_client",
    "src.predictive.garch",
    "src.predictive.market_intel",
    "src.predictive.pcftn",
    "src.monitoring.hud_server",
    "src.monitoring.platform_reporter",
    "src.monitoring.partykit_client",
]


def main() -> int:
    for m in MODULES:
        __import__(m)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
