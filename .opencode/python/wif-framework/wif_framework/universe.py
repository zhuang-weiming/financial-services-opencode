ETF_UNIVERSE = [
    "SPY", "VTI", "QQQ", "IWM", "VB",
    "MTUM", "QUAL", "MOAT", "USMV", "SPLV", "VIG", "NOBL", "HDV", "SCHD", "VYM",
    "VGT", "XLE", "XLF", "XLB", "XLP", "XLU", "XLV", "XLRE",
    "EFA", "VEA", "EEM", "VWO",
    "BND", "TLT", "IEF", "SHV", "AGG", "LQD", "HYG",
    "GLD", "SLV", "PDBC", "VNQ",
    "IJH", "IJR",
]

ETF_CATEGORIES = {
    "US_Equity_Core": ["VTI", "SPY", "QQQ", "IWM", "VB"],
    "US_Equity_Factor": ["MTUM", "QUAL", "MOAT", "USMV", "SPLV", "VIG", "NOBL", "HDV", "SCHD", "VYM"],
    "US_Equity_Sector": ["VGT", "XLE", "XLF", "XLB", "XLP", "XLU", "XLV", "XLRE"],
    "International_Equity": ["EFA", "VEA", "EEM", "VWO"],
    "Fixed_Income": ["BND", "TLT", "IEF", "SHV", "AGG", "LQD", "HYG"],
    "Real_Assets_Commodities": ["GLD", "SLV", "PDBC", "VNQ"],
    "US_Equity_Size": ["IJH", "IJR"],
}

FACTOR_LIST = ["MTUM", "QUAL", "MOAT", "USMV", "SPLV", "VIG", "NOBL", "HDV", "SCHD", "VYM",
               "VGT", "XLE", "XLF", "XLB", "XLP", "XLU", "XLV", "XLRE",
               "EFA", "VEA", "EEM", "VWO",
               "IJH", "IJR", "IWM", "VB"]

DEFENSIVE_ETFS = ["SHV", "GLD", "TLT", "BND"]
