"""Signal engine for CLI-driven backtest."""
import numpy as np
import pandas as pd


class SignalEngine:
    """Momentum-on-close signal engine (sign of 20-day close change).

    ``generate`` receives a symbol -> OHLCV DataFrame map and returns a
    symbol -> signal Series map (1=long, -1=short, 0=flat).
    """

    def generate(self, data_map):
        result = {}
        for symbol, df in data_map.items():
            close = df["close"].astype(float)
            result[symbol] = np.sign(close.pct_change(20).fillna(0.0))
        return result
