"""Signal engine for CLI-driven backtest."""
import numpy as np


class SignalEngine:
    """Momentum-on-close signal engine (sign of 20-day close change)."""

    def generate(self, df):
        df = df.copy()
        close = df["close"].astype(float)
        df["signal"] = np.sign(close.pct_change(20).fillna(0.0))
        return df
