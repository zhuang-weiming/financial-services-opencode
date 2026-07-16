"""
vibe-trading-quanta — Multi-market quantitative research engine.

Vendored from HKUDS Vibe-Trading v0.1.11 (MIT).
Provides backtest engines, data loaders, alpha zoo, factor analysis,
portfolio optimizers, and swarm presets for financial research.
"""

from . import backtest
from . import loaders
from . import factors
from . import swarm

__version__ = "0.1.0"
__source__ = "Vibe-Trading v0.1.11 (https://github.com/HKUDS/Vibe-Trading)"
