# Explore Agent Example Questions

**Data Files:**
- `data/architecture.json` - System architecture
- `data/code_analysis.csv` - Code file analysis

---

## Question 1: Repository Architecture
```
Explore the financial services monorepo structure.

Reference: data/architecture.json

From data/architecture.json:
- Pattern: Modular monorepo
- Layers: Presentation (React), Business Logic (Python/FastAPI), Data (PostgreSQL)
- Component Count: 145 React components, 23 services, 67 models

Key Files:
- pricing_service.py: 892 lines, high complexity
- portfolio_model.py: 445 lines, medium complexity
- order_api.py: 623 lines, high complexity

Please:
1) Map the architecture layers
2) Identify key entry points
3) Trace dependencies
4) Document integration points
```

---

## Question 2: Code Complexity Analysis
```
Analyze code complexity across the codebase.

Reference: data/code_analysis.csv

From data/code_analysis.csv:
- pricing_service.py: 892 lines, high complexity
- portfolio_model.py: 445 lines, medium complexity
- order_api.py: 623 lines, high complexity
- risk_calculator.py: 312 lines, medium complexity
- trade_executor.py: 567 lines, high complexity

Please:
1) Identify high-complexity files
2) Flag files needing refactoring
3) Map code ownership
4) Recommend test coverage priorities
```

## Question 3: 我的投资组合数据架构分析
```
请分析我的投资组合的数据架构，找出优化点。

Reference: data/architecture.json

我用以下工具来管理投资数据：
- 券商 A：富途（获取交易和持仓数据）
- 券商 B：盈透（获取美股交易数据）
- 银行：招商银行（查看现金和理财）
- 个人记账：Excel 表格（手工记录收支和投资）
- 数据导出：从各平台 CSV 导出后手动合并

From data/architecture.json:
- 参考代码仓库的架构分析思路

Please:
1) 画出当前的数据流图（数据从哪里来→怎么处理→存在哪里→怎么使用）
2) 识别每个环节的痛点和效率瓶颈
3) 评估数据一致性风险（手工合并可能出错的地方）
4) 推荐一个适合 Premier 投资者的数据整合方案
5) 建议需要自动化的环节（API 对接/自动下载/自动合并）
6) 估算自动化改造的时间和成本
7) 推荐数据安全措施（密码管理/双因素认证/备份策略）
```

## Question 4: Premier 组合的代码复杂度分析
```
请分析我个人使用的投资分析工具/脚本的代码质量。

Reference: data/code_analysis.csv

假设我使用以下工具和脚本（非从文件读取）：
- Python 脚本：定投计算器（300 行，高复杂度）
- Excel：持仓追踪表（含 VLOOKUP 和 IF 嵌套，多处硬编码）
- Python 脚本：基金评分模型（500 行，有依赖问题）
- 数据文件：多版本 CSV 不便管理

From data/code_analysis.csv:
- 参考代码分析框架和复杂度评估标准

Please:
1) 分析每个工具/脚本的代码质量和维护难度
2) 识别硬编码值、重复逻辑、缺少错误处理的模块
3) 评估数据文件版本管理的现状和风险
4) 推荐适合个人投资者的技术栈简化方案
5) 建议迁移到更易维护的平台/工具
6) 推荐测试和验证方法（确保计算正确性）
7) 如果时间有限，给出最优先重写的模块排序
```