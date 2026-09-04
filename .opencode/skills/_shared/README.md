# Technical Analysis Skills — Shared Resources

本目录存放所有技术分析 skill 共用的资源，以及**任意股票通用的 8 框架分析入口**。

| 文件 | 用途 |
|:--|:--|
| `run_technical_analysis.py` | **通用入口** — 任意 ticker → 8 框架一键分析 |
| `data_loader.py` | **统一数据加载器** — US/A股/港股/Crypto/CSV |
| `sample_data.py` | SPCX 55 日 OHLCV 示例数据 |
| `fix_czsc.py` | **修复 czsc 库**（rs_czsc stub 导致的 ImportError） |
| `setup_requirements.sh` | 一键安装依赖 + 验证 8 skill + 修复 czsc |
| `requirements.txt` | Python 依赖清单 |
| `README.md` | 本文件 |

## 快速上手 — 分析任意股票

```bash
# 1. 安装依赖 + 修复 czsc + 验证 (首次)
bash .opencode/skills/_shared/setup_requirements.sh

# 2. 分析任何股票 (8 框架一键)
python3 .opencode/skills/_shared/run_technical_analysis.py AAPL          # 美股
python3 .opencode/skills/_shared/run_technical_analysis.py 600519        # A股 (自动推断)
python3 .opencode/skills/_shared/run_technical_analysis.py BTC-USD       # Crypto
python3 .opencode/skills/_shared/run_technical_analysis.py 600519 --market cn
python3 .opencode/skills/_shared/run_technical_analysis.py AAPL --skills elliott,gann
python3 .opencode/skills/_shared/run_technical_analysis.py AAPL --json out.json
python3 .opencode/skills/_shared/run_technical_analysis.py data.csv      # 本地 CSV
```

## 8 个技术分析框架 (全部通用，任意股票)

| Skill | 函数 | 算法来源 | 数据要求 |
|:--|:--|:--|:--|
| candlestick | `detect_candles(df)` | 15 种经典蜡烛形态 | ≥ 10 日 |
| elliott-wave | `analyze_elliott(df)` | Zigzag + 斐波那契波浪关系 | ≥ 60 日 |
| ichimoku | `analyze_ichimoku(df)` | 一目均衡表五线系统 | 78 日完整 warm-up |
| harmonic | `analyze_harmonic(df)` | XABCD 五点多形 | ≥ 30 日 |
| technical-basic | `analyze_tech_basic(df)` | EMA/ADX/BB/RSI/OBV | ≥ 30 日 |
| chanlun | `analyze_chanlun(df)` | 缠论 (分型→笔→中枢) | ≥ 100 日 |
| smc | `analyze_smc(df)` | BOS/ChoCH/FVG/OB | ≥ 30 日 |
| gann | `analyze_gann(df)` | 江恩角度/Sq9/Rule of 7/50% | 任意 |

所有函数接受 `[date, open, high, low, close, volume]` 标准化 DataFrame，
**无硬编码价格**（参考点自动从数据推断）。

## 已验证的多市场测试

| 市场 | 标的 | 数据源 | 结果 |
|:--|:--|:--|:--|
| 美股 | SPCX (55d) | llmquant-data MCP | ✅ 8/8 |
| 美股 | AAPL (200d) | llmquant-data MCP → CSV | ✅ 8/8 |
| A股 | 600519 茅台 (300d) | akshare | ✅ 8/8 (Chanlun 39分型/30笔/17中枢) |
| Crypto | BTC-USD | MCP 代表性点 | ✅ 8/8 |

## 关键说明

1. **所有算法均为真实实现**（pandas/numpy/math），**无 mock/fake**。
2. **czsc 库修复**：`fix_czsc.py` 检测 rs_czsc stub 并 patch `check_rs_czsc()`
   返回 False → 强制 czsc 走 `czsc/py/` 纯 Python 路径（功能完整）。
   幂等、自动备份。`setup_requirements.sh` 每次自动检查并修复。
3. **ta-lib 可选**：candlestick / technical-basic 已用 pandas 实现。
4. **数据不足时诚实标注**：Ichimoku 无 78 根 → "indeterminate"；Chanlun 无 100+
   根 → 明确警告，不做虚假输出。
5. **yfinance 限流**：优先用 llmquant-data MCP / akshare / mootdx。

## 数据加载优先级 (per data-priority.md)

```
US/Crypto: llmquant-data MCP → yfinance
A股:       mootdx (TCP 不封IP) → akshare → tushare
港股:      akshare
本地:      CSV (date/open/high/low/close/volume)
```

## 关联文档

- 完整 SPCX 报告: `.opencode/memory/personal-system/reports/SPCX-technical-analysis-2026-09-01.md`
- 原始实现: `/tmp/spcx_tech/analyze.py` (885 行)
- 各 skill example: `.opencode/skills/{skill}/examples/spcx_analysis.py`

