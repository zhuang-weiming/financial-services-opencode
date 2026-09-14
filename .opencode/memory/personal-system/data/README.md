# memory/personal-system/data/ — 数据层（**只存指针，不复制数值**）

> **建立：** 2026-09-15（用户裁定方案 B）
> **产物：** `artifacts_manifest.json` — 21 项数据的**路径 + sha256 + 用途 + 产出脚本**

---

## 一、为什么是"指针"而不是"数值"

本目录**第一版曾把数值复制进来**（`timing_snapshot_*.json` + `timing_log.csv`），已删除。原因：

| 复制数值的做法 | 只存指针的做法 |
|---|---|
| 复制件会与原件**静默漂移** | 漂移变成**可检测事件**（sha256 不匹配） |
| 转录错一位 → memory 里留下**看似权威的错误** | memory 不产生新数字，**无法引入转录错误** |
| 一份数据两个来源，无一致性校验 | 单一事实来源（原件），memory 只索引 |
| 数据更新后 memory 不会自动跟随 | `--check` 会立刻报 DRIFT |

**原则：memory 记录"数据在哪里、由什么产生、是否还是那一个"，不记录"数据是什么"。**

---

## 二、怎么用

```bash
# 1) 数据在哪里 / 由什么产生
python3 -c "import json;m=json.load(open('.opencode/memory/personal-system/data/artifacts_manifest.json'));
[print(f\"{a['id']:34s} {a['role']:14s} {a['path']}\") for a in m['artifacts']]"

# 2) 漂移检查（任一文件被改/删除 → 非零退出码，可接 CI）
python3 .opencode/scripts/build_artifacts_manifest.py --check

# 3) 新增产物后刷新清单
python3 .opencode/scripts/build_artifacts_manifest.py
```

---

## 三、artifacts_manifest.json 的字段

| 字段 | 含义 |
|---|---|
| `id` | 稳定标识（跨快照不改名，便于时间序列对齐） |
| `path` | **绝对可解析的仓库相对路径** |
| `sha256` | 内容哈希 —— 漂移检测的依据 |
| `bytes` | 文件大小 |
| `as_of` | 数据自身的**观测截止日**（≠ 生成日） |
| `role` | `upstream_input` / `fetch` / `derived` / `report` / `tool` |
| `producer` | 产出该文件的脚本（`derived` 类必有） |
| `note` | 已知缺陷 / 口径 / 陷阱 |
| `exists` | 路径当前是否存在 |

---

## 四、当前 21 项产物

| role | 数量 | 说明 |
|---|---:|---|
| `upstream_input` | 4 | 官方只读输入（含**自带 2026-06-09 口径断裂**的矩阵） |
| `fetch` | 3 | 本轮 Tier-1 MCP 抓取的原始增量 |
| `derived` | 8 | 加工产物（矩阵/相位评估/核验/其他 skill/A股读数/F29 锚点） |
| `report` | 3 | 人读报告 |
| `tool` | 5 | 可复跑入口脚本 |

> `wif-matrix-base-20260716` 的 `note` 里记着 **官方矩阵在 2026-06-09 换口径**
> （SPY 739→1342，+81.5%/日）—— 这是本轮最重要的数据缺陷，注册为 `upstream_input`
> 是为了让**任何人都能复现 de-glitch 前后的差异**。

---

## 五、已知的未绑定项（诚实边界）

1. **本清单不覆盖 memory 自身的 markdown 数值。**
   `2.HYPOTHESES.md` / `3.US_FRAMEWORK.md` / `3.1.CHINA_FRAMEWORK.md` / `4.2.*` 里的监控表
   **仍是复制过来的数值**，未纳入哈希校验 —— 它们会随时间手工更新，不适合逐次哈希。
   现状：**这些表是"人读摘要"，原件仍是清单里的 artifact。**
2. **不覆盖 `example/wif-*/data/tickers_*/` 下的 48 个上游单 ticker 文件**
   （仅注册了 `CreditSpread_BAA`，因为它是 F29 缺失的直接原因）。
3. **`--check` 只验证"内容未变"，不验证"内容正确"** ——
   若原件本身就错（如官方矩阵的 06-09 断裂），哈希会一致地通过。
   **哈希防漂移，不防原始错误。**
