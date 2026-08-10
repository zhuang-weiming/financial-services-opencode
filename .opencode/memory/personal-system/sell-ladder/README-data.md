# SELL_LADDER data/ 来源说明

> **位置:** `.opencode/memory/personal-system/sell-ladder/data/`
> **最后更新:** 2026-08-10

---

## 一、300725 药石科技

| 文件 | 来源 | 时段 | 大小 |
|:---|:---|:---|:---:|
| `raw_daily_300725.csv` | akshare `stock_zh_a_hist` (qfq) | 2017-11-10 → 2026-08-10 | 171KB (2118 bars) |
| `wt_daily_300725.csv` | V21 `wave_trend.py` 计算 (本地) | 同上 | 233KB |
| `wt_daily_300725_last60.csv` | V21 (近 60 日) | 同上 | 6.7KB |

**更新方法:**
```python
import akshare as ak
df = ak.stock_zh_a_hist(symbol='300725', period='daily', adjust='qfq',
                       start_date='20171110', end_date='20260810')
df.to_csv('.opencode/memory/personal-system/sell-ladder/data/raw_daily_300725.csv', index=False)
```

**WT 重算方法:**
```bash
# 用 V21 wave_trend.py 计算
python3 .opencode/skills/alpha-engine-v21/scripts/wave_trend.py \
    --ticker 300725 --csv .opencode/memory/personal-system/sell-ladder/data/raw_daily_300725.csv
```

---

## 二、CDMO 同业 (cross-data/)

| 代码 | 名称 | 来源 | 时段 | 大小 |
|:---:|:---|:---|:---|:---:|
| 002821 | 凯莱英 | Sina API | 2022-11-23 → 2026-08-10 | 44KB (900 bars) |
| 603259 | 药明康德 | Sina API | 同上 | 43KB |
| 300759 | 康龙化成 | Sina API | 同上 | 43KB |
| 300363 | 博腾股份 | Sina API | 同上 | 42KB |

**更新方法 (Sina API, 轻量, 永不被封):**
```python
import requests, pandas as pd
def sina_hist(code, scale=240, datalen=900):
    full_code = f'sz{code}' if code.startswith(('0', '3')) else f'sh{code}'
    url = 'https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData'
    params = {'symbol': full_code, 'scale': scale, 'ma': 'no', 'datalen': datalen}
    r = requests.get(url, params=params, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
    df = pd.DataFrame(r.json())
    df = df.rename(columns={'day': 'date', 'open': 'open', 'high': 'high',
                            'low': 'low', 'close': 'close', 'volume': 'volume'})
    df['date'] = pd.to_datetime(df['date'])
    return df

for code, name in [('002821', '凯莱英'), ('603259', '药明康德'),
                    ('300759', '康龙化成'), ('300363', '博腾股份')]:
    df = sina_hist(code)
    df.to_csv(f'.opencode/memory/personal-system/sell-ladder/data/cross-data/{code}_{name}.csv', index=False)
```

**注:**
- akShare 对这 4 个代码经常 ConnectionError, Sina API 是稳定替代
- 900 bars ≈ 3.5 年, 满足 pair-trading / multi-factor 的 lookback=60 需求
- 如需更长历史, 改 `datalen=2000` (≈ 8 年)

---

## 三、添加新标的

### A. 已有数据的标的 (akshare 可拉)

```python
import akshare as ak
df = ak.stock_zh_a_hist(symbol='代码', period='daily', adjust='qfq',
                       start_date='20170101', end_date='今天')
df.to_csv('.opencode/memory/personal-system/sell-ladder/data/raw_daily_代码.csv', index=False)
```

### B. akShare 失败的标的 (用 Sina API)

```python
# 同上 "CDMO 同业" 更新方法
```

### C. 加新行业同业 (扩展 peer_dfs)

在 `sell_ladder.py` 的 `run_sell_ladder()` 中:
```python
for code in ['新代码1', '新代码2', ...]:
    try:
        peer_dfs[code] = load_data(code)
    except:
        pass
```

---

## 四、数据质量

### 已知问题
- akShare 不稳定 (频繁 ConnectionError), Sina API 备用
- Sina 数据无复权选项, 但 CDMO 标的近年无大比例送转, 影响小
- 300725 raw 数据用 qfq (前复权), 与 Sina 不复权数据可能差几个百分点

### 解决方案
- 300725 用 akshare qfq (优先)
- 同业用 Sina 不复权 (Sina 900 bars 限制, 但够用)
- 如需精确, 可改用 Baostock / Tushare (需 token)

---

*End of README-data — 2026-08-10*
