# Fund DB — 全球公募基金数据库

> Morningstar MCP 采集 · 窗口 2026-08-20~23 · 🇺🇸🇪🇺🇨🇳🇭🇰
> 结构权威: `pipeline/ddl_current.sql`（活库导出）· 统计权威: DB `db_stats` 表 · 语义与口径: `SCHEMA.md`

## 目录

```
fund_db.sqlite          ★ 唯一成果DB（21,891行 / 21,100独立载体，QA全过）
README.md               本文件
SCHEMA.md               字段语义/口径/护栏/datapoint注册表
pipeline/               规范管道: s1池→s2拉取→s3持仓→s4幂等入库→s5归并+视图→validate
ingest_raw/             原始数据归档（按日期标注，见 MANIFEST.md）
source_data/            Phase-1 历史源数据（只读，内含污染源警告）
```

## 使用规范（违反会得出错误结论）

1. **规模只用 `size_usd`**；`fund_size_native` 是本币口径，必须配 `size_currency`
2. **去重走 `v_fund_screen`**；`0P*` 行是同基金的另一上市点，不是另一只基金
3. **Sharpe 用 `v_fund_sharpe_clean`**
4. **集中度先滤 `weight_quarantine=0`**；`is_notional=1` 的 >100% 权重是真实名义敞口
5. **最新持仓用 `v_holdings_latest`**
6. 遗留兼容视图 `v_fund_snapshot` 勿用于新分析

## 快速开始

```bash
cd pipeline && python3 validate.py      # QA断言 + 刷新db_stats
sqlite3 fund_db.sqlite "SELECT * FROM db_stats"   # 权威统计数字
./run_all.sh --regions us,eu,cnhk       # 全量重建（需MCP token）
```

Token（24h有效）过期：重新 OAuth 后写入 `/tmp/morningstar_token.json`。
